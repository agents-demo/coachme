<script>
  import { tr } from "$lib/appearance";
  import { onMount } from "svelte";
  import { base } from "$app/paths";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { getReports } from "$lib/api";
  import { sportMode } from "$lib/stores";
  import NewAnalysis from "$lib/components/NewAnalysis.svelte";
  import LiveJob from "$lib/components/LiveJob.svelte";
  import ReportCard from "$lib/components/ReportCard.svelte";
  import SportCard from "$lib/components/SportCard.svelte";

  let reports = $state([]);
  let jobId = $state(null);
  let loading = $state(true);
  const showNew = $derived($page.url.searchParams.get("new") === "1");

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
    if (!reports.length && !showNew) goto(`${base}/?new=1`, { replaceState: true });
  });

  function ondone(stem) {
    if (stem) goto(`${base}/result?stem=${encodeURIComponent(stem)}`);
    else load();
  }

  const totalIssues = $derived(reports.reduce((a, r) => a + (r.issue_count || 0), 0));

  let search = $state("");
  const filtered = $derived(
    search.trim()
      ? reports.filter((r) =>
          [r.stem, r.sport, r.date].join(" ").toLowerCase().includes(search.trim().toLowerCase()),
        )
      : reports,
  );
</script>

<!-- Hero banner -->
<section class="relative overflow-hidden rounded-3xl border-2 border-line bg-gradient-to-br from-accent/15 via-transparent to-accent2/15 p-6 sm:p-9">
  <div class="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-accent/25 blur-3xl"></div>
  <div class="pointer-events-none absolute -bottom-20 -left-10 h-48 w-48 rounded-full bg-accent2/20 blur-3xl"></div>
  <div class="relative">
    <span class="inline-flex items-center gap-1 rounded-full border border-line bg-ink/50 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-muted">{tr("Vision-powered coaching")}</span>
    <h1 class="mt-3 font-display text-3xl font-extrabold leading-tight sm:text-4xl">
      {tr("Turn a session video into a")}
      <span class="bg-gradient-to-r from-accent to-accent2 bg-clip-text text-transparent">{tr("coaching report")}</span>
    </h1>
    <p class="mt-2 max-w-2xl text-sm text-muted">{tr("Record a rally from the side. Get measured form & footwork insights, the things to fix, and drills — from a vision model that actually watches your frames.")}</p>
  </div>
</section>

{#if reports.length && !showNew}
  <div class="mt-4 grid grid-cols-2 gap-3">
    <div class="card p-4 text-center">
      <div class="font-display text-2xl font-bold">{reports.length}</div>
      <div class="text-[11px] uppercase tracking-wide text-muted">{tr("Sessions")}</div>
    </div>
    <div class="card p-4 text-center">
      <div class="font-display text-2xl font-bold">{totalIssues}</div>
      <div class="text-[11px] uppercase tracking-wide text-muted">{tr("Open issues")}</div>
    </div>
  </div>
{/if}

{#if reports.length > 3 && !showNew}
  <div class="relative mt-5">
    <svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="8"/><path stroke-linecap="round" stroke-linejoin="round" d="m21 21-4.35-4.35"/></svg>
    <input
      bind:value={search}
      placeholder={tr("Search sessions…")}
      class="w-full rounded-xl border-2 border-line bg-surface py-2 pl-9 pr-4 text-sm transition focus:border-accent focus:outline-none"
    />
    {#if search}
      <button onclick={() => (search = "")} aria-label="Clear search" class="absolute right-3 top-1/2 -translate-y-1/2 text-muted transition hover:text-app">✕</button>
    {/if}
  </div>
{/if}

<h2 class="mt-5 font-display text-lg font-bold">{showNew ? tr("New analysis") : tr("Sessions")}</h2>

{#if showNew}
  <NewAnalysis onqueued={(id) => (jobId = id)} />
{/if}

{#if jobId}
  <LiveJob {jobId} onfinished={load} ondone={ondone} />
{/if}

{#if !showNew}
  {#if loading}
    <p class="mt-6 text-sm text-muted">{tr("Loading…")}</p>
  {:else if !reports.length}
    <p class="mt-6 text-sm text-muted">{tr("No sessions yet. Start a new analysis above.")}</p>
  {:else if !filtered.length}
    <p class="mt-6 text-sm text-muted">{tr("No sessions match")} "<span class="text-app">{search}</span>".</p>
  {:else}
    <!-- Sport mode: 2-col portrait grid (full-bleed, image-forward).
         Default mode: 3-col landscape grid with metadata below the thumbnail. -->
    {#if $sportMode}
      <div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {#each filtered as r (r.stem)}
          <SportCard report={r} ondeleted={load} />
        {/each}
      </div>
    {:else}
      <div class="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {#each filtered as r (r.stem)}
          <ReportCard report={r} ondeleted={load} />
        {/each}
      </div>
    {/if}

  {/if}
{/if}

{#if !showNew}
  <a
    href={`${base}/?new=1`}
    aria-label="New analysis"
    class="fixed bottom-5 right-4 z-40 inline-flex items-center gap-2 rounded-full bg-accent px-5 py-3.5 text-sm font-semibold text-white shadow-xl shadow-accent/25 transition hover:scale-[1.03] hover:opacity-95 sm:bottom-7 sm:right-7"
  >
    <span class="text-lg leading-none">+</span>
    {tr("New analysis")}
  </a>
{/if}
