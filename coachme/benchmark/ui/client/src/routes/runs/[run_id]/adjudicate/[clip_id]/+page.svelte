<script>
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { getAdjudication, saveAdjudication } from "$lib/api";

  const runId = $derived($page.params.run_id);
  const clipId = $derived($page.params.clip_id);
  let detail = $state(null);
  let etag = $state("");
  let loading = $state(true);
  let saving = $state(false);
  let error = $state("");
  let note = $state("");
  let decision = $state({ preferred: "tie", rationale: "" });

  async function load() {
    loading = true;
    error = "";
    note = "";
    try {
      detail = await getAdjudication(runId, clipId);
      etag = detail.etag;
      if (detail.decision) {
        decision = { preferred: detail.decision.preferred, rationale: detail.decision.rationale || "" };
      }
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  async function save() {
    saving = true;
    error = "";
    note = "";
    try {
      if (!decision.rationale.trim()) throw new Error("rationale is required");
      const result = await saveAdjudication(runId, clipId, decision, etag);
      etag = result.etag;
      detail = { ...detail, decision: result.decision };
      note = "Decision saved.";
    } catch (err) {
      error = err.message;
    } finally {
      saving = false;
    }
  }

  onMount(load);

  const modeA = $derived(detail?.mapping?.A || "");
  const modeB = $derived(detail?.mapping?.B || "");
</script>

{#if loading}
  <p class="muted" style="margin-top: 24px">Loading adjudication…</p>
{:else if error && !detail}
  <div class="error" style="margin-top: 24px">{error}</div>
{:else if detail}
  <div class="row" style="justify-content: space-between; margin-top: 22px">
    <div>
      <a href={`/runs/${encodeURIComponent(runId)}/adjudicate`} class="muted small" style="text-decoration: none">← Adjudication queue</a>
      <h1 style="margin: 6px 0 4px" class="mono">{clipId}</h1>
      <div class="row muted small">
        <span class="pill">A = {modeA}</span>
        <span class="pill">B = {modeB}</span>
      </div>
    </div>
    <button class="btn primary" onclick={save} disabled={saving}>{saving ? "Saving…" : "Save decision"}</button>
  </div>

  {#if error}<div class="error" style="margin-top: 12px">{error}</div>{/if}
  {#if note}<div class="notice" style="margin-top: 12px">{note}</div>{/if}

  <section class="card" style="margin-top: 16px">
    <video src={detail.media_url} controls preload="metadata"><track kind="captions" /></video>
  </section>

  <div class="grid two" style="margin-top: 16px; align-items: start">
    {#each [["A", modeA], ["B", modeB]] as [label, mode]}
      <section class="card">
        <h2>{label} · {mode}</h2>
        {#if detail.reports[mode]}
          <p class="muted">{detail.reports[mode].summary || "No summary."}</p>
          {#each detail.reports[mode].issues || [] as issue, index (index)}
            <div class="finding">
              <strong>{issue.issue || issue.text}</strong>
              {#if issue.evidence_times?.length}
                <div class="muted small" style="margin-top: 4px">{issue.evidence_times.join(", ")}s</div>
              {/if}
            </div>
          {/each}
        {:else}
          <p class="muted">No report.</p>
        {/if}
      </section>
    {/each}
  </div>

  <section class="card" style="margin-top: 16px">
    <h2>Rater votes</h2>
    {#each Object.entries(detail.ratings || {}) as [rater, rating]}
      <div class="finding">
        <div class="row" style="justify-content: space-between">
          <strong>{rater}</strong>
          <span class="pill">{rating.preferred || "tie"}</span>
        </div>
        <p class="muted small" style="margin: 6px 0 0">{rating.rationale || "No rationale."}</p>
      </div>
    {/each}

    <div class="field" style="margin-top: 14px">
      <label for="preferred">Final preference</label>
      <select id="preferred" bind:value={decision.preferred} style="max-width: 220px">
        <option value="A">A</option>
        <option value="B">B</option>
        <option value="tie">tie</option>
      </select>
    </div>
    <div class="field">
      <label for="rationale">Rationale</label>
      <textarea id="rationale" bind:value={decision.rationale} placeholder="Why this decision?"></textarea>
    </div>
  </section>
{/if}
