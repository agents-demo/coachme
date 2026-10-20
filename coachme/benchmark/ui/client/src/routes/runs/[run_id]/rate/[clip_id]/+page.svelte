<script>
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { getBlind, getLabeler, saveRating, submitRatings } from "$lib/api";

  const runId = $derived($page.params.run_id);
  const clipId = $derived($page.params.clip_id);
  const rater = getLabeler();
  const scores = [1, 2, 3, 4, 5];

  let blind = $state(null);
  let etag = $state("");
  let loading = $state(true);
  let saving = $state(false);
  let error = $state("");
  let note = $state("");
  let rating = $state(defaultRating());

  function defaultRating() {
    return {
      A_specific: 4,
      A_supported: 4,
      A_complete: 4,
      A_honest: 4,
      A_use: "yes",
      B_specific: 4,
      B_supported: 4,
      B_complete: 4,
      B_honest: 4,
      B_use: "yes",
      preferred: "tie",
      rationale: "",
      notes: "",
    };
  }

  async function load() {
    loading = true;
    error = "";
    note = "";
    try {
      blind = await getBlind(runId, clipId, rater);
      etag = blind.etag;
      rating = { ...defaultRating(), ...(blind.rating || {}) };
    } catch (err) {
      error =
        err.status === 409
          ? "This rating is already submitted. Reopen it from the rating queue to edit."
          : err.message;
    } finally {
      loading = false;
    }
  }

  async function save() {
    saving = true;
    error = "";
    note = "";
    try {
      if (rating.preferred !== "tie" && !rating.rationale.trim()) {
        throw new Error("rationale is required when a report is preferred");
      }
      const result = await saveRating(runId, rater, clipId, rating, etag);
      etag = result.etag;
      rating = { ...rating, ...result.rating };
      note = "Draft saved.";
      return true;
    } catch (err) {
      error = err.message;
      return false;
    } finally {
      saving = false;
    }
  }

  async function submitAll() {
    error = "";
    note = "";
    const saved = await save();
    if (!saved) return;
    saving = true;
    try {
      const result = await submitRatings(runId, rater);
      note = `Submitted ${result.submitted} rating(s).`;
    } catch (err) {
      error = err.message;
    } finally {
      saving = false;
    }
  }

  onMount(load);

  function onKeydown(event) {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
      event.preventDefault();
      save();
    }
  }
</script>

<svelte:window onkeydown={onKeydown} />

{#if loading}
  <p class="muted" style="margin-top: 24px">Loading blind packet…</p>
{:else if error && !blind}
  <div class="error" style="margin-top: 24px">{error}</div>
{:else if blind}
  <div class="row" style="justify-content: space-between; margin-top: 22px">
    <div>
      <a href={`/runs/${encodeURIComponent(runId)}/rate`} class="muted small" style="text-decoration: none">← Rating queue</a>
      <h1 style="margin: 6px 0 4px" class="mono">{clipId}</h1>
      <div class="row muted small">
        <span class="pill">rater {rater}</span>
        <span class="pill">blind A/B</span>
      </div>
    </div>
    <div class="row">
      <button class="btn" onclick={save} disabled={saving}>{saving ? "Saving…" : "Save draft"}</button>
      <button class="btn primary" onclick={submitAll} disabled={saving}>Save and submit all</button>
    </div>
  </div>

  <div class="notice" style="margin-top: 14px">
    Do not infer the mode from the text. Rate each report on its own merits.
  </div>
  {#if error}<div class="error" style="margin-top: 12px">{error}</div>{/if}
  {#if note}<div class="notice" style="margin-top: 12px">{note}</div>{/if}

  <div class="grid two" style="margin-top: 16px; align-items: start">
    {#each ["A", "B"] as label}
      <section class="card">
        <h2>{label}</h2>
        <p class="muted">{blind.reports[label].summary || "No summary."}</p>
        {#if blind.reports[label].issues?.length}
          {#each blind.reports[label].issues as issue, index (index)}
            <div class="finding">
              <strong>{issue.text || issue.issue}</strong>
              {#if issue.times?.length}
                <div class="muted small" style="margin-top: 4px">
                  {issue.times.join(", ")}s
                </div>
              {/if}
            </div>
          {/each}
        {:else}
          <p class="muted">No findings.</p>
        {/if}
        {#if blind.reports[label].limitations?.length}
          <h3 style="margin-top: 14px">Limitations</h3>
          <ul class="muted small" style="padding-left: 18px; line-height: 1.6">
            {#each blind.reports[label].limitations as item}<li>{item}</li>{/each}
          </ul>
        {/if}
      </section>
    {/each}
  </div>

  <section class="card" style="margin-top: 16px">
    <h2>Rating</h2>
    <div style="overflow-x: auto">
      <table class="table">
        <thead>
          <tr><th>Question</th><th>A</th><th>B</th></tr>
        </thead>
        <tbody>
          {#each [
            ["specific", "Specific and actionable"],
            ["supported", "Supported by the clip"],
            ["complete", "Nothing important missing"],
            ["honest", "Clear about what was not assessed"],
          ] as [key, question]}
            <tr>
              <td>{question}</td>
              <td>
                <select aria-label={`A ${question}`} bind:value={rating[`A_${key}`]}>
                  {#each scores as score}<option value={score}>{score}</option>{/each}
                </select>
              </td>
              <td>
                <select aria-label={`B ${question}`} bind:value={rating[`B_${key}`]}>
                  {#each scores as score}<option value={score}>{score}</option>{/each}
                </select>
              </td>
            </tr>
          {/each}
          <tr>
            <td>Would use before a lesson?</td>
            <td><select aria-label="Would use A" bind:value={rating.A_use}><option value="yes">yes</option><option value="no">no</option></select></td>
            <td><select aria-label="Would use B" bind:value={rating.B_use}><option value="yes">yes</option><option value="no">no</option></select></td>
          </tr>
          <tr>
            <td><strong>Which is better?</strong></td>
            <td colspan="2">
              <select id="preferred" aria-label="Preferred report" bind:value={rating.preferred} style="max-width: 220px">
                <option value="A">A</option>
                <option value="B">B</option>
                <option value="tie">tie</option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="field" style="margin-top: 14px">
      <label for="rationale">Rationale</label>
      <textarea id="rationale" bind:value={rating.rationale} placeholder="Required when you prefer A or B"></textarea>
    </div>
    <div class="field">
      <label for="notes">Notes</label>
      <textarea id="notes" bind:value={rating.notes}></textarea>
    </div>
  </section>

  <section class="card" style="margin-top: 16px">
    <video src={blind.media_url} controls preload="metadata"><track kind="captions" /></video>
  </section>
{/if}
