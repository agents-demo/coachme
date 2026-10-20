<script>
  import { page } from "$app/stores";
  import { getLabeler, importReview, reviewTemplateUrl } from "$lib/api";

  const runId = $derived($page.params.run_id);
  const kinds = [
    ["evidence", "Evidence semantic review", "Check that each cited window actually contains the described finding."],
    ["tool", "Tool appropriateness", "Check that the tools used match the evidence required by each finding."],
    ["hallucination", "Hallucination review", "Confirm every flagged factual claim against the clip and evidence."],
  ];
  let reviewer = $state(getLabeler());
  let files = $state({});
  let busy = $state({});
  let notes = $state({});
  let error = $state("");

  async function upload(kind) {
    if (!files[kind]) return;
    busy = { ...busy, [kind]: true };
    error = "";
    try {
      const result = await importReview(runId, kind, reviewer, files[kind]);
      notes = { ...notes, [kind]: `Imported ${result.imported} review(s).` };
    } catch (err) {
      error = err.message;
    } finally {
      busy = { ...busy, [kind]: false };
    }
  }
</script>

<div class="row" style="justify-content: space-between; margin-top: 22px">
  <div>
    <a href={`/runs/${encodeURIComponent(runId)}`} class="muted small" style="text-decoration: none">? Run</a>
    <h1 style="margin: 6px 0 4px">Manual reviews</h1>
    <p class="muted" style="margin: 0">Review the sample of matched findings before trusting a release decision.</p>
  </div>
  <div class="field" style="min-width: 180px; margin: 0">
    <label for="reviewer">Reviewer</label>
    <input id="reviewer" bind:value={reviewer} />
  </div>
</div>

{#if error}<div class="error" style="margin-top: 14px">{error}</div>{/if}

<div class="stack" style="margin-top: 16px">
  {#each kinds as [kind, title, description]}
    <section class="card">
      <div class="row" style="justify-content: space-between">
        <div>
          <h2 style="margin-bottom: 4px">{title}</h2>
          <p class="muted small" style="margin: 0">{description}</p>
        </div>
        <a class="btn" download href={reviewTemplateUrl(runId, kind)}>Download template</a>
      </div>
      <div class="row" style="margin-top: 12px">
        <input
          type="file"
          accept=".csv,text/csv"
          aria-label={`${title} CSV file`}
          onchange={(event) => (files = { ...files, [kind]: event.currentTarget.files?.[0] || null })}
        />
        <button class="btn" onclick={() => upload(kind)} disabled={!files[kind] || busy[kind]}>
          {busy[kind] ? "Importing?" : "Import reviewed CSV"}
        </button>
        {#if notes[kind]}<span class="pill good">{notes[kind]}</span>{/if}
      </div>
    </section>
  {/each}
</div>
