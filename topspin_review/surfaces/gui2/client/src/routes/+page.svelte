<script>
  import { onMount } from "svelte";
  import { base } from "$app/paths";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { getReports, compare } from "$lib/api";
  import Readiness from "$lib/components/Readiness.svelte";
  import NewAnalysis from "$lib/components/NewAnalysis.svelte";
  import LiveJob from "$lib/components/LiveJob.svelte";
  import ReportCard from "$lib/components/ReportCard.svelte";
  import CompareVideos from "$lib/components/CompareVideos.svelte";

  let reports = $state([]);
  let jobId = $state(null);
  let loading = $state(true);
  const showNew = $derived($page.url.searchParams.get("new") === "1");

  let a = $state("");
  let b = $state("");
  let diff = $state(null);
  let cmpError = $state("");
  const aReport = $derived(reports.find((r) => r.stem === a));
  const bReport = $derived(reports.find((r) => r.stem === b));
  const canCompareVideos = $derived(
    Boolean(a && b && a !== b && aReport?.has_source && bReport?.has_source && !aReport?.is_photo && !bReport?.is_photo),
  );
  async function runCompare() {
    cmpError = "";
    diff = null;
    try {
      diff = await compare(a, b);
    } catch (e) {
      cmpError = String(e?.message || e);
    }
  }

  async function load() {
    loading = true;
    try {
      reports = (await getReports()).reports;
    } finally {
      loading = false;
    }
  }
  onMount(async () => {
    await load();
    if (reports.length >= 2) {
      b = reports[0].stem; // newest (list is newest-first)
      a = reports[reports.length - 1].stem; // oldest
    }
    if (!reports.length && !showNew) goto(`${base}/?new=1`, { replaceState: true });
  });

  function ondone(stem) {
    if (stem) goto(`${base}/result?stem=${encodeURIComponent(stem)}`);
    else load();
  }

  const avgQuality = $derived(
    reports.length ? Math.round(reports.reduce((a, r) => a + (r.score || 0), 0) / reports.length) : 0,
  );
  const totalIssues = $derived(reports.reduce((a, r) => a + (r.issue_count || 0), 0));
</script>

<section class="relative overflow-hidden rounded-3xl border-2 border-line bg-gradient-to-br from-accent/15 via-transparent to-accent2/15 p-6 sm:p-9">
  <div class="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-accent/25 blur-3xl"></div>
  <div class="pointer-events-none absolute -bottom-20 -left-10 h-48 w-48 rounded-full bg-accent2/20 blur-3xl"></div>
  <div class="relative">
    <span class="inline-flex items-center gap-1 rounded-full border border-line bg-ink/50 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-muted">Vision-powered coaching</span>
    <h1 class="mt-3 font-display text-3xl font-extrabold leading-tight sm:text-4xl">
      Turn a session video into a
      <span class="bg-gradient-to-r from-accent to-accent2 bg-clip-text text-transparent">coaching report</span>
    </h1>
    <p class="mt-2 max-w-2xl text-sm text-muted">
      Record a rally from the side. Get measured form &amp; footwork insights, the things to fix, and drills —
      from a vision model that actually watches your frames.
    </p>
  </div>
</section>

{#if reports.length && !showNew}
  <div class="mt-4 grid grid-cols-3 gap-3">
    <div class="card p-4 text-center">
      <div class="font-display text-2xl font-bold">{reports.length}</div>
      <div class="text-[11px] uppercase tracking-wide text-muted">Sessions</div>
    </div>
    <div class="card p-4 text-center">
      <div class="font-display text-2xl font-bold">{avgQuality}</div>
      <div class="text-[11px] uppercase tracking-wide text-muted">Avg quality</div>
    </div>
    <div class="card p-4 text-center">
      <div class="font-display text-2xl font-bold">{totalIssues}</div>
      <div class="text-[11px] uppercase tracking-wide text-muted">Open issues</div>
    </div>
  </div>
{/if}

<h2 class="mt-5 font-display text-lg font-bold">{showNew ? "New analysis" : "Sessions"}</h2>

{#if showNew}
  <NewAnalysis onqueued={(id) => (jobId = id)} />
  <Readiness />
{/if}

{#if jobId}
  <LiveJob {jobId} onfinished={load} ondone={ondone} />
{/if}

{#if !showNew}
  {#if loading}
    <p class="mt-6 text-sm text-muted">Loading…</p>
  {:else if !reports.length}
    <p class="mt-6 text-sm text-muted">No sessions yet. Use “＋ New analysis” in the menu above.</p>
  {:else}
    <div class="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {#each reports as r (r.stem)}
        <ReportCard report={r} ondeleted={load} />
      {/each}
    </div>

    {#if reports.length >= 2}
      <h3 class="mt-8 font-display text-lg font-bold">Compare two sessions</h3>
      <div class="mt-3 flex flex-wrap items-end gap-3 text-sm">
        <label class="text-xs text-muted">Earlier
          <select bind:value={a} class="mt-1 block rounded-lg border-2 border-line bg-surface px-3 py-2">
            {#each reports as r (r.stem)}<option value={r.stem}>{r.stem}</option>{/each}
          </select>
        </label>
        <label class="text-xs text-muted">Later
          <select bind:value={b} class="mt-1 block rounded-lg border-2 border-line bg-surface px-3 py-2">
            {#each reports as r (r.stem)}<option value={r.stem}>{r.stem}</option>{/each}
          </select>
        </label>
        <button onclick={runCompare} disabled={a === b} class="rounded-lg bg-accent px-4 py-2 font-semibold text-white disabled:opacity-50">Compare</button>
      </div>
      {#if canCompareVideos}
        <div class="mt-4">
          <CompareVideos a={{ stem: a, label: aReport.stem }} b={{ stem: b, label: bReport.stem }} />
        </div>
      {/if}
      {#if cmpError}<p class="mt-2 text-sm text-bad">{cmpError}</p>{/if}
      {#if diff}
        <p class="mt-3 text-sm">{diff.text}</p>
        {#each [["Improved", diff.improved], ["Still an issue", diff.unchanged], ["New / regressed", diff.regressed]] as [label, items]}
          {#if items?.length}
            <p class="mt-1 text-sm"><b>{label}:</b> {items.join(", ")}</p>
          {/if}
        {/each}
        {#if diff.metric_deltas && Object.keys(diff.metric_deltas).length}
          <div class="mt-2 text-xs text-muted">
            {#each Object.entries(diff.metric_deltas) as [k, v]}<span class="mr-3">{k}: {v > 0 ? "+" : ""}{v}</span>{/each}
          </div>
        {/if}
      {/if}
    {/if}
  {/if}
{/if}
