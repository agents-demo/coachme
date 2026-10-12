<script>
  import { onMount } from "svelte";
  import { base } from "$app/paths";
  import { goto } from "$app/navigation";
  import { getReports } from "$lib/api";
  import Readiness from "$lib/components/Readiness.svelte";
  import NewAnalysis from "$lib/components/NewAnalysis.svelte";
  import LiveJob from "$lib/components/LiveJob.svelte";
  import ReportCard from "$lib/components/ReportCard.svelte";

  let reports = $state([]);
  let jobId = $state(null);
  let loading = $state(true);

  async function load() {
    loading = true;
    try {
      reports = (await getReports()).reports;
    } finally {
      loading = false;
    }
  }
  onMount(load);

  function ondone(stem) {
    if (stem) goto(`${base}/result?stem=${encodeURIComponent(stem)}`);
    else load();
  }
</script>

<h1 class="font-display text-3xl font-bold">Turn a session video into a coaching report</h1>
<p class="mt-1 text-sm text-muted">
  A video in. Measured form &amp; footwork insights, what to fix, and drills out.
</p>

<Readiness />

<NewAnalysis onqueued={(id) => (jobId = id)} />

{#if jobId}
  <LiveJob {jobId} onfinished={load} ondone={ondone} />
{/if}

{#if loading}
  <p class="mt-6 text-sm text-muted">Loading…</p>
{:else if !reports.length}
  <p class="mt-6 text-sm text-muted">No sessions yet. Analyze a clip above.</p>
{:else}
  <h2 class="mt-8 font-display text-lg font-bold">Sessions</h2>
  <div class="mt-4 grid gap-4 sm:grid-cols-2">
    {#each reports as r (r.stem)}
      <ReportCard report={r} ondeleted={load} />
    {/each}
  </div>
{/if}
