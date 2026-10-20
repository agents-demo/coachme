<script>
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { cancelRun, deleteRun, getClips, getRun, resumeRun, runStability, scoreRun } from "$lib/api";

  const runId = $derived($page.params.run_id);
  let run = $state(null);
  let clips = $state([]);
  let loading = $state(true);
  let error = $state("");
  let scoring = $state(false);
  let working = $state(false);
  let packetBusy = $state(false);
  let raters = $state("coach-a,coach-b");
  let against = $state("");
  let stabilityBusy = $state(false);
  let stabilityResult = $state(null);
  let timer;
  let source;

  async function load(silent = false) {
    if (!silent) loading = true;
    error = "";
    try {
      [run, clips] = await Promise.all([getRun(runId), getClips(runId)]);
      clips = clips.clips || [];
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  async function cancel() {
    if (!confirm(`Cancel ${runId}?`)) return;
    working = true;
    error = "";
    try {
      await cancelRun(runId);
      await load();
    } catch (err) {
      error = err.message;
    } finally {
      working = false;
    }
  }

  async function checkStability() {
    if (!against.trim()) return;
    stabilityBusy = true;
    error = "";
    try {
      stabilityResult = await runStability(runId, against.trim());
      await load(true);
    } catch (err) {
      error = err.message;
    } finally {
      stabilityBusy = false;
    }
  }

  async function downloadPackets() {
    packetBusy = true;
    error = "";
    try {
      const response = await fetch(`/api/runs/${encodeURIComponent(runId)}/rater-packets`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ raters: raters.split(",").map((item) => item.trim()).filter(Boolean) }),
      });
      if (!response.ok) throw new Error(`${response.status} rater packets`);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${runId}-rater-packets.zip`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      error = err.message;
    } finally {
      packetBusy = false;
    }
  }

  async function removeRun() {
    const answer = prompt(`Delete ${runId}? Type the run id to confirm:`);
    if (answer !== runId) return;
    working = true;
    error = "";
    try {
      await deleteRun(runId);
      await goto("/");
    } catch (err) {
      error = err.message;
    } finally {
      working = false;
    }
  }

  async function resume() {
    working = true;
    error = "";
    try {
      await resumeRun(runId);
      await load();
    } catch (err) {
      error = err.message;
    } finally {
      working = false;
    }
  }

  async function rescore() {
    scoring = true;
    error = "";
    try {
      await scoreRun(runId);
      await load();
    } catch (err) {
      error = err.message;
    } finally {
      scoring = false;
    }
  }

  onMount(() => {
    load();
    if (typeof EventSource !== "undefined") {
      source = new EventSource(`/api/runs/${encodeURIComponent(runId)}/stream`);
      source.onmessage = () => load(true);
      source.onerror = () => {
        source?.close();
        source = null;
        timer = setInterval(() => {
          if (run?.active || run?.status === "running" || run?.status === "queued") load(true);
        }, 3000);
      };
    } else {
      timer = setInterval(() => {
        if (run?.active || run?.status === "running" || run?.status === "queued") load(true);
      }, 3000);
    }
    return () => {
      clearInterval(timer);
      source?.close();
    };
  });

  const gateEntries = $derived(Object.entries(run?.gates || {}));
  const metrics = $derived([
    ["Precision", run?.investigator?.precision, run?.standard?.precision],
    ["Recall", run?.investigator?.recall, run?.standard?.recall],
    ["Evidence integrity", run?.investigator?.evidence_integrity, null],
    ["Coverage honesty", run?.investigator?.coverage_honesty, null],
    ["Path diversity", run?.investigator?.path_diversity, null],
    ["Partial rate", run?.investigator?.partial_rate, null],
    ["Failure rate", run?.investigator?.failure_rate, null],
    ["FP on zero clips", run?.investigator?.fp_zero_clip_rate, run?.standard?.fp_zero_clip_rate],
  ]);

  function pill(value) {
    return value === true ? "good" : value === false ? "bad" : "warn";
  }

  function metric(value) {
    if (value === null || value === undefined) return "—";
    if (typeof value === "number") {
      if (value <= 1 && value >= 0 && !Number.isInteger(value)) return `${(value * 100).toFixed(1)}%`;
      return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
    }
    return String(value);
  }
</script>

{#if loading}
  <p class="muted" style="margin-top: 24px">Loading run…</p>
{:else if error && !run}
  <div class="error" style="margin-top: 24px">{error}</div>
{:else if run}
  <div class="row" style="justify-content: space-between; margin-top: 22px">
    <div>
      <a href="/" class="muted small" style="text-decoration: none">← All runs</a>
      <h1 style="margin: 6px 0 4px">{run.label || run.run_id}</h1>
      <div class="row muted small">
        <span class="mono">{run.run_id}</span>
        <span class="pill">{run.environment}</span>
        <span class="pill">{run.status}</span>
        <span class="pill" class:good={run.release_eligible === true} class:bad={run.release_eligible === false}>
          {run.release_eligible ? "release eligible" : "blocked"}
        </span>
      </div>
    </div>
    <div class="row">
      <button class="btn" onclick={load}>Refresh</button>
      <button class="btn primary" onclick={rescore} disabled={scoring}>
        {scoring ? "Scoring…" : "Recompute score"}
      </button>
    </div>
  </div>

  {#if error}<div class="error" style="margin-top: 14px">{error}</div>{/if}

  <div class="grid two" style="margin-top: 18px">
    <section class="card">
      <h2>Release status</h2>
      <div class="row">
        <span class="pill" class:good={run.score_status === "current"} class:warn={run.score_status !== "current"}>
          score {run.score_status}
        </span>
        <span class="pill">{run.clips_complete}/{run.clips_total} clips complete</span>
        <span class="pill" class:good={run.labels_complete} class:warn={!run.labels_complete}>
          {run.labels_complete ? "labels complete" : "labels incomplete"}
        </span>
        {#if run.evidence_review?.matched}
          <span class="pill" class:good={run.evidence_review.complete} class:warn={!run.evidence_review.complete}>
            evidence review {run.evidence_review.reviewed}/{run.evidence_review.matched}
          </span>
        {/if}
        {#if run.stability?.checked_at}
          <span class="pill" class:good={run.stability.stable} class:bad={!run.stability.stable}>
            stability {run.stability.stable ? "pass" : "fail"}
          </span>
        {/if}
      </div>
      {#if run.blocked_reasons?.length}
        <div class="notice" style="margin-top: 12px">
          {run.blocked_reasons.join("\n")}
        </div>
      {/if}
    </section>

    <section class="card">
      <h2>Coach preference</h2>
      <div class="row">
        <span class="pill">Investigator {run.coach?.investigator ?? 0}</span>
        <span class="pill">Standard {run.coach?.standard ?? 0}</span>
        <span class="pill">Ties {run.coach?.ties ?? 0}</span>
        <span class="pill">Agreement {metric(run.coach?.agreement)}</span>
      </div>
      <p class="muted small" style="margin-bottom: 0">
        Preference {metric(run.coach?.preference)} · κ {metric(run.coach?.kappa)}
      </p>
    </section>
  </div>

  <section class="card" style="margin-top: 16px">
    <h2>Gates</h2>
    {#if gateEntries.length}
      <div class="gates">
        {#each gateEntries as [name, value]}
          <div class="gate">
            <span>{name.replaceAll("_", " ")}</span>
            <span class="pill" class:good={value === true} class:bad={value === false} class:warn={value === null || value === undefined}>
              {value === true ? "pass" : value === false ? "fail" : "blocked"}
            </span>
          </div>
        {/each}
      </div>
    {:else}
      <p class="muted">Score not generated. Run analysis, labels and ratings, then recompute.</p>
    {/if}
  </section>

  <section class="card" style="margin-top: 16px">
    <h2>Metrics</h2>
    <div style="overflow-x: auto">
      <table class="table">
        <thead>
          <tr><th>Metric</th><th>Standard</th><th>Investigator</th></tr>
        </thead>
        <tbody>
          {#each metrics as [label, inv, std]}
            <tr><td>{label}</td><td>{metric(std)}</td><td>{metric(inv)}</td></tr>
          {/each}
        </tbody>
      </table>
    </div>
  </section>

  <section class="card" style="margin-top: 16px">
    <h2>Exports</h2>
    <div class="row">
      <a class="btn" download href={`/api/runs/${encodeURIComponent(runId)}/export/score.json`}>score.json</a>
      <a class="btn" download href={`/api/runs/${encodeURIComponent(runId)}/export/report.md`}>report.md</a>
      <a class="btn" download href={`/api/runs/${encodeURIComponent(runId)}/export/rating_sheet.csv`}>rating_sheet.csv</a>
      <a class="btn" download href={`/api/runs/${encodeURIComponent(runId)}/export/labels.json`}>labels.json</a>
      <a class="btn" download href={`/api/runs/${encodeURIComponent(runId)}/export/run.zip`}>run.zip</a>
    </div>
    <div class="row" style="margin-top: 12px">
      <input bind:value={raters} placeholder="coach-a,coach-b" style="max-width: 240px" />
      <button class="btn" onclick={downloadPackets} disabled={packetBusy}>
        {packetBusy ? "Building?" : "Download rater packets"}
      </button>
    </div>
    <div class="row" style="margin-top: 12px">
      <input bind:value={against} placeholder="compare against run id" style="max-width: 260px" />
      <button class="btn" onclick={checkStability} disabled={stabilityBusy || !against.trim()}>
        {stabilityBusy ? "Checking?" : "Run stability check"}
      </button>
      {#if stabilityResult}
        <span class="pill" class:good={stabilityResult.stable} class:bad={!stabilityResult.stable}>
          {stabilityResult.stable ? "stable" : "not stable"}
        </span>
      {/if}
    </div>
  </section>

  <section class="card" style="margin-top: 16px">
    <h2>Clips</h2>
    {#if !clips.length}
      <p class="muted">No clips in this run.</p>
    {:else}
      <div style="overflow-x: auto">
        <table class="table">
          <thead>
            <tr><th>Clip</th><th>Type</th><th>Standard</th><th>Investigator</th><th>Label</th><th></th></tr>
          </thead>
          <tbody>
            {#each clips as clip (clip.clip_id)}
              <tr>
                <td class="mono">{clip.clip_id}</td>
                <td class="muted">{clip.media_type} · {clip.duration_s}s</td>
                <td><span class="pill">{clip.reports?.standard?.status || "missing"}</span></td>
                <td><span class="pill">{clip.reports?.investigator?.status || "missing"}</span></td>
                <td>
                  <span class="pill" class:good={clip.label_status === "complete"} class:warn={clip.label_status !== "complete"}>
                    {clip.label_status}
                  </span>
                </td>
                <td>
                  <div class="row" style="gap: 6px">
                    <a class="btn" style="padding: 4px 8px" href={`/runs/${encodeURIComponent(runId)}/clips/${encodeURIComponent(clip.clip_id)}`}>Review</a>
                    <a class="btn" style="padding: 4px 8px" href={`/runs/${encodeURIComponent(runId)}/labels/${encodeURIComponent(clip.clip_id)}`}>Label</a>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </section>
{/if}
