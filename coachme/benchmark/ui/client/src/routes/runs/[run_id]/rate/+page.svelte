<script>
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { getLabeler, getRateQueue, importRatings, reopenRating, setLabeler, submitRatings } from "$lib/api";

  const runId = $derived($page.params.run_id);
  let rater = $state("coach-a");
  let queue = $state(null);
  let loading = $state(true);
  let busy = $state(false);
  let error = $state("");
  let note = $state("");
  let importFile = $state(null);
  let forceImport = $state(false);
  let importing = $state(false);

  async function load() {
    loading = true;
    error = "";
    note = "";
    try {
      setLabeler(rater);
      queue = await getRateQueue(runId, rater);
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  async function importCsv() {
    if (!importFile) return;
    importing = true;
    error = "";
    note = "";
    try {
      const result = await importRatings(runId, rater, importFile, forceImport);
      note = `Imported ${Object.keys(result.clips || {}).length} rating(s).`;
      await load();
    } catch (err) {
      error = err.message;
    } finally {
      importing = false;
    }
  }

  async function submitAll() {
    busy = true;
    error = "";
    note = "";
    try {
      const result = await submitRatings(runId, rater);
      note = `Submitted ${result.submitted} rating(s).`;
      await load();
    } catch (err) {
      error = err.message;
    } finally {
      busy = false;
    }
  }

  async function reopen(clipId) {
    const reason = prompt(`Reopen ${clipId}? Give a reason:`);
    if (!reason) return;
    busy = true;
    error = "";
    try {
      await reopenRating(runId, rater, clipId, reason);
      await load();
    } catch (err) {
      error = err.message;
    } finally {
      busy = false;
    }
  }

  onMount(() => {
    rater = getLabeler();
    load();
  });

  const canSubmit = $derived(
    queue && queue.clips.length && queue.clips.every((clip) => clip.state !== "not_started"),
  );
</script>

<div class="row" style="justify-content: space-between; margin-top: 22px">
  <div>
    <a href={`/runs/${encodeURIComponent(runId)}`} class="muted small" style="text-decoration: none">← Run</a>
    <h1 style="margin: 6px 0 4px">Blind rating</h1>
    <p class="muted" style="margin: 0">Rate A/B without seeing which mode produced each report.</p>
  </div>
  <div class="row">
    <input bind:value={rater} placeholder="rater id" style="width: 140px" />
    <button class="btn" onclick={load} disabled={loading}>Load</button>
    <button class="btn primary" onclick={submitAll} disabled={busy || !canSubmit}>Submit all</button>
  </div>
</div>

<div class="notice" style="margin-top: 14px">
  This is a local single-user view. A person with filesystem access can read the mapping.
  True blindness requires separate rater packets or a restricted machine.
</div>

<section class="card" style="margin-top: 16px">
  <h2>Import a rater sheet</h2>
  <div class="row">
    <input type="file" accept=".csv,text/csv" aria-label="Rater CSV file" onchange={(event) => (importFile = event.currentTarget.files?.[0] || null)} />
    <label class="pill" style="cursor: pointer">
      <input type="checkbox" bind:checked={forceImport} style="width: auto; margin-right: 5px" />
      replace submitted
    </label>
    <button class="btn" onclick={importCsv} disabled={!importFile || importing}>
      {importing ? "Importing?" : "Import CSV"}
    </button>
  </div>
  <p class="muted small" style="margin-bottom: 0">
    Use the per-rater template from ?Download rater packets?. Imported sheets are marked submitted.
  </p>
</section>

{#if error}<div class="error" style="margin-top: 12px">{error}</div>{/if}
{#if note}<div class="notice" style="margin-top: 12px">{note}</div>{/if}

{#if loading}
  <p class="muted" style="margin-top: 18px">Loading queue…</p>
{:else if queue}
  <section class="card" style="margin-top: 16px">
    <div class="row" style="justify-content: space-between">
      <h2 style="margin: 0">Queue</h2>
      <span class="pill">{queue.submitted}/{queue.total} submitted</span>
    </div>

    {#if !queue.clips.length}
      <p class="muted">No blind packets in this run. Run both Standard and Investigator first.</p>
    {:else}
      <table class="table" style="margin-top: 12px">
        <thead>
          <tr><th>Clip</th><th>Packet</th><th>State</th><th></th></tr>
        </thead>
        <tbody>
          {#each queue.clips as clip (clip.clip_id)}
            <tr>
              <td class="mono">{clip.clip_id}</td>
              <td><span class="pill" class:good={clip.has_packet} class:bad={!clip.has_packet}>{clip.has_packet ? "ready" : "missing"}</span></td>
              <td>
                <span class="pill" class:good={clip.state === "submitted"} class:warn={clip.state !== "submitted"}>
                  {clip.state.replaceAll("_", " ")}
                </span>
              </td>
              <td>
                <div class="row" style="gap: 6px">
                  {#if clip.has_packet && clip.state !== "submitted"}
                    <a class="btn" style="padding: 4px 8px" href={`/runs/${encodeURIComponent(runId)}/rate/${encodeURIComponent(clip.clip_id)}`}>
                      {clip.state === "draft" ? "Continue" : "Rate"}
                    </a>
                  {:else if clip.state === "submitted"}
                    <button class="btn" style="padding: 4px 8px" onclick={() => reopen(clip.clip_id)} disabled={busy}>Reopen</button>
                  {/if}
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </section>
{/if}
