<script>
  import { tr } from "$lib/appearance";
  import { jobStatus, cancel, retry } from "$lib/api";
  import { JOB_TONE, shortLabel, STEP_GROUP, GROUP_ORDER } from "$lib/format";

  let { jobId, onfinished, ondone } = $props();

  let currentId = $state(jobId);
  let job = $state(null);
  let feed = $state([]);
  let timer;
  let es = null; // EventSource for SSE, null when polling

  function apply(s) {
    job = s;
    const p = s.progress || {};
    const done = ["done", "failed", "cancelled"].includes(s.status);
    const steps = (p.timings || []).map((t) => ({ stage: t.stage, seconds: t.seconds, state: "done" }));
    if (p.stage && p.stage !== "done") {
      steps.push({ stage: p.stage, seconds: null, state: done ? "done" : "running" });
    }
    feed = steps;
  }

  // Group the running steps by pipeline stage, like Diagnostics.
  const grouped = $derived.by(() => {
    const buckets = new Map(GROUP_ORDER.map((g) => [g, []]));
    for (const s of feed) buckets.get(STEP_GROUP[s.stage] || "Other").push(s);
    return GROUP_ORDER.map((g) => ({ name: g, items: buckets.get(g) })).filter((x) => x.items.length);
  });

  function stopAll() {
    clearInterval(timer);
    if (es) { es.close(); es = null; }
  }

  function startPolling(id) {
    clearInterval(timer);
    timer = setInterval(async () => {
      try {
        const s = await jobStatus(id);
        apply(s);
        if (["done", "failed", "cancelled"].includes(s.status)) {
          clearInterval(timer);
          onfinished?.();
          if (s.status === "done") ondone?.(s.stem);
        }
      } catch {
        /* keep polling */
      }
    }, 1200);
  }

  function start(id) {
    stopAll();
    if (typeof EventSource !== "undefined") {
      es = new EventSource(`/jobs/${encodeURIComponent(id)}/stream`);
      es.onmessage = (e) => {
        try {
          const s = JSON.parse(e.data);
          apply(s);
          if (["done", "failed", "cancelled"].includes(s.status)) {
            es?.close();
            es = null;
            onfinished?.();
            if (s.status === "done") ondone?.(s.stem);
          }
        } catch { /* ignore malformed frame */ }
      };
      es.addEventListener("error", () => {
        // SSE connection dropped — fall back to polling
        if (es) { es.close(); es = null; }
        startPolling(id);
      });
    } else {
      startPolling(id);
    }
  }

  $effect(() => {
    if (jobId && jobId !== currentId) {
      currentId = jobId;
      job = null;
      feed = [];
    }
  });

  $effect(() => {
    if (currentId) start(currentId);
    return stopAll;
  });

  async function stop() {
    if (currentId) await cancel(currentId);
  }
  async function again() {
    if (!job?.id) return;
    const { job_id } = await retry(job.id);
    currentId = job_id;
    job = null;
    feed = [];
  }
</script>

{#if job}
  <section class="card mt-4 p-4">
    <div class="flex items-center gap-2">
      <span class="text-sm font-semibold {JOB_TONE[job.status] || "text-muted"}">{job.status}</span>
      <span class="text-xs text-muted">{shortLabel(job.progress?.stage || "")}{job.progress?.detail ? ` · ${job.progress.detail}` : ""}</span>
      <span class="ml-auto text-xs text-muted">
        {#if job.progress?.elapsed != null}{Number(job.progress.elapsed).toFixed(1)}{tr("s total ·")} {/if}
        {job.progress?.pct != null ? `${Math.round(job.progress.pct)}%` : ""}
      </span>
    </div>
    {#if job.progress?.pct != null}
      <div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-surface">
        <div class="h-full rounded-full bg-gradient-to-r from-accent to-accent2" style={`width: ${Math.max(2, Math.round(job.progress.pct))}%`}></div>
      </div>
    {/if}
    {#if grouped.length}
      <div class="mt-3 space-y-2">
        {#each grouped as g}
          <div>
            <div class="text-[10px] font-semibold uppercase tracking-wide text-accent">{g.name}</div>
            <ol class="mt-0.5 space-y-1">
              {#each g.items as s}
                <li class="flex items-center gap-2 text-sm">
                  <span class={s.state === "running" ? "text-accent2" : "text-good"}>{s.state === "running" ? "●" : "✓"}</span>
                  <span class="text-app">{shortLabel(s.stage)}</span>
                  {#if s.seconds != null}<span class="ml-auto text-xs text-muted">{Number(s.seconds).toFixed(2)}{tr("s")}</span>{/if}
                </li>
              {/each}
            </ol>
          </div>
        {/each}
      </div>
    {/if}
    {#if job.error}<pre class="mt-2 overflow-auto text-xs text-bad">{job.error}</pre>{/if}
    <div class="mt-3 flex gap-3">
      {#if ["queued", "running"].includes(job.status)}
        <button onclick={stop} class="rounded-lg border-2 border-line px-4 py-2 text-sm font-semibold">{tr("Cancel")}</button>
      {/if}
      {#if ["failed", "cancelled", "done"].includes(job.status)}
        <button onclick={again} class="rounded-lg border-2 border-line px-4 py-2 text-sm font-semibold">{tr("Retry")}</button>
      {/if}
    </div>
  </section>
{/if}
