<script>
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { getClip, sourceUrl } from "$lib/api";

  const runId = $derived($page.params.run_id);
  const clipId = $derived($page.params.clip_id);
  let clip = $state(null);
  let loading = $state(true);
  let error = $state("");
  let mode = $state("investigator");
  let video = $state(null);

  async function load() {
    loading = true;
    error = "";
    try {
      clip = await getClip(runId, clipId);
      if (!clip.reports?.investigator && clip.reports?.standard) mode = "standard";
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  onMount(load);

  const report = $derived(clip?.reports?.[mode] || null);
  const issues = $derived(report?.issues || []);

  function seek(time) {
    if (!video) return;
    const value = Number(time);
    if (Number.isFinite(value)) {
      video.currentTime = value;
      video.play().catch(() => {});
    }
  }

  function fmt(value) {
    const time = Number(value);
    return Number.isFinite(time) ? `${time.toFixed(2)}s` : String(value ?? "");
  }

  function issueText(issue) {
    return typeof issue === "string" ? issue : issue?.issue || "";
  }
</script>

{#if loading}
  <p class="muted" style="margin-top: 24px">Loading clip…</p>
{:else if error}
  <div class="error" style="margin-top: 24px">{error}</div>
{:else if clip}
  <div class="row" style="justify-content: space-between; margin-top: 22px">
    <div>
      <a href={`/runs/${encodeURIComponent(runId)}`} class="muted small" style="text-decoration: none">← Run</a>
      <h1 style="margin: 6px 0 4px" class="mono">{clip.clip_id}</h1>
      <div class="row muted small">
        <span>{clip.clip.sport}</span>
        <span class="pill">{clip.clip.media_type}</span>
        <span class="pill">{clip.clip.duration_s}s</span>
        <span class="pill" class:good={clip.label_status === "complete"} class:warn={clip.label_status !== "complete"}>
          label {clip.label_status}
        </span>
      </div>
    </div>
    <div class="row">
      <a class="btn" href={`/runs/${encodeURIComponent(runId)}/labels/${encodeURIComponent(clipId)}`}>Edit label</a>
    </div>
  </div>

  {#if !clip.has_source}
    <div class="notice" style="margin-top: 14px">Source media is missing for this clip.</div>
  {/if}

  <div class="grid two" style="margin-top: 16px; align-items: start">
    <section class="card">
      {#if clip.has_source && clip.clip.media_type === "video"}
        <video bind:this={video} src={sourceUrl(runId, clipId)} controls preload="metadata"><track kind="captions" /></video>
      {:else if clip.has_source}
        <img src={sourceUrl(runId, clipId)} alt="Benchmark clip" style="width: 100%; border-radius: 12px" />
      {/if}
      <p class="muted small" style="margin-bottom: 0; margin-top: 10px">{clip.clip.capture}</p>
    </section>

    <section class="card">
      <div class="row" style="justify-content: space-between; margin-bottom: 12px">
        <h2 style="margin: 0">Report</h2>
        <div class="tabs">
          <button class:active={mode === "investigator"} onclick={() => (mode = "investigator")}>Investigator</button>
          <button class:active={mode === "standard"} onclick={() => (mode = "standard")}>Standard</button>
          {#if clip.reports?.guided}
            <button class:active={mode === "guided"} onclick={() => (mode = "guided")}>Guided</button>
          {/if}
        </div>
      </div>

      {#if !report}
        <p class="muted">No {mode} report for this clip.</p>
      {:else}
        <p class="muted">{report.summary || "No summary."}</p>
        {#if issues.length}
          {#each issues as issue, index (index)}
            <div class="finding">
              <div class="row" style="justify-content: space-between">
                <strong>{issueText(issue)}</strong>
                {#if issue?.confidence}<span class="pill">{issue.confidence}</span>{/if}
              </div>
              {#if issue?.evidence_times?.length}
                <div class="times" style="margin-top: 6px">
                  {#each issue.evidence_times as time}
                    <button onclick={() => seek(time)}>{fmt(time)}</button>
                  {/each}
                </div>
              {/if}
            </div>
          {/each}
        {:else}
          <p class="muted">No findings.</p>
        {/if}
        {#if report.limitations?.length}
          <h3 style="margin-top: 16px">Limitations</h3>
          <ul class="muted small" style="padding-left: 18px; line-height: 1.6">
            {#each report.limitations as item}<li>{item}</li>{/each}
          </ul>
        {/if}
      {/if}
    </section>
  </div>

  {#if clip.traces?.investigator}
    <section class="card" style="margin-top: 16px">
      <h2>Investigator trace</h2>
      <div class="row">
        {#each clip.traces.investigator.tool_sequence || [] as tool}
          <span class="pill">{tool}</span>
        {/each}
      </div>
      {#if clip.traces.investigator.evidence?.length}
        <table class="table" style="margin-top: 12px">
          <thead><tr><th>Evidence</th><th>Tool</th><th>Window</th><th>Confidence</th></tr></thead>
          <tbody>
            {#each clip.traces.investigator.evidence as evidence}
              <tr>
                <td class="mono">{evidence.id || "?"}</td>
                <td>{evidence.tool || "?"}</td>
                <td class="mono">{evidence.window ? `${evidence.window[0]}?${evidence.window[1]}s` : "?"}</td>
                <td>{evidence.confidence || "?"}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
      <p class="muted small" style="margin-bottom: 0">
        {clip.traces.investigator.evidence?.length || 0} evidence records ?
        {clip.traces.investigator.budget?.seconds ?? "?"}s
      </p>
    </section>
  {/if}

  {#if clip.artifacts && Object.keys(clip.artifacts).length}
    <section class="card" style="margin-top: 16px">
      <h2>Artifacts</h2>
      <div class="grid two">
        {#each Object.entries(clip.artifacts) as [kind, url]}
          <div class="finding">
            <div class="row" style="justify-content: space-between">
              <strong>{kind}</strong>
              <a class="btn" style="padding: 3px 7px" href={url} target="_blank" rel="noreferrer">Open</a>
            </div>
            {#if !["metrics", "observability"].includes(kind)}
              <img src={url} alt={kind} style="width: 100%; margin-top: 8px; border-radius: 8px" />
            {/if}
          </div>
        {/each}
      </div>
    </section>
  {/if}
{/if}
