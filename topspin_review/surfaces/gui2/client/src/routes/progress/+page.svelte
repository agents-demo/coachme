<script>
  import { tr } from "$lib/appearance";
  import { onMount } from "svelte";
  import { base } from "$app/paths";
  import { getReports, compare, getTrends } from "$lib/api";
  import CompareVideos from "$lib/components/CompareVideos.svelte";

  let tab = $state("trends");
  let reports = $state([]);
  let trends = $state(null);
  let loading = $state(true);
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

  onMount(async () => {
    try {
      const params = new URLSearchParams(window.location.search);
      if (params.get("tab") === "compare") tab = "compare";
      reports = (await getReports()).reports;
      try { trends = await getTrends(); } catch {}
      if (reports.length >= 2) {
        a = reports[1].stem;
        b = reports[0].stem;
      }
    } finally {
      loading = false;
    }
  });
</script>

<section class="flex flex-wrap items-start justify-between gap-3">
  <div>
    <h1 class="font-display text-3xl font-extrabold">{tr("Progress")}</h1>
    <p class="mt-1 max-w-2xl text-sm text-muted">
      {tr("See what is improving over time, or compare two sessions side by side.")}
    </p>
  </div>
  <div class="flex gap-1.5 rounded-full border border-line bg-surface p-1">
    <button
      onclick={() => (tab = "trends")}
      class="rounded-full px-4 py-1.5 text-sm font-semibold transition {tab === 'trends' ? 'bg-accent text-white' : 'text-muted hover:text-app'}"
    >{tr("Trends")}</button>
    <button
      onclick={() => (tab = "compare")}
      class="rounded-full px-4 py-1.5 text-sm font-semibold transition {tab === 'compare' ? 'bg-accent text-white' : 'text-muted hover:text-app'}"
    >{tr("Compare")}</button>
  </div>
</section>

{#if loading}
  <p class="mt-6 text-sm text-muted">{tr("Loading…")}</p>
{:else if reports.length < 2}
  <div class="card mt-5 p-6 text-center">
    <p class="text-sm text-muted">{tr("You need at least two sessions to see progress.")}</p>
    <a href={`${base}/?new=1`} class="mt-4 inline-flex rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90">
      {tr("New analysis")}
    </a>
  </div>
{:else if tab === "trends"}
  {#if trends && trends.sessions >= 2}
    <section class="card mt-4 p-4">
      {#if trends.top_issues?.length}
        {@const max = trends.top_issues[0]?.count || 1}
        <div>
          <div class="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-muted">{tr("Recurring issues")}</div>
          <div class="space-y-1.5">
            {#each trends.top_issues.slice(0, 8) as iss}
              <div class="flex items-center gap-2 text-xs">
                <div class="relative h-4 min-w-0 flex-1 overflow-hidden rounded-full bg-warn/10">
                  <div class="h-full rounded-full bg-warn/40 transition-all" style={`width: ${Math.round((iss.count / max) * 100)}%`}></div>
                  <span class="absolute inset-0 flex items-center truncate pl-2 text-[10px] text-app">{iss.text}</span>
                </div>
                <span class="shrink-0 font-mono text-[10px] text-muted">{iss.count}×</span>
              </div>
            {/each}
          </div>
        </div>
      {:else}
        <p class="text-sm text-muted">{tr("No recurring issues yet — analyze a few more sessions.")}</p>
      {/if}

      {#if trends.metrics?.length}
        <div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {#each trends.metrics as m}
            {@const vals = m.points.map((s) => s.value)}
            {@const mn = Math.min(...vals)}
            {@const mx = Math.max(...vals) || 1}
            {@const w = 120}
            {@const h = 32}
            {@const pts = vals.map((v, i) => `${Math.round((i / Math.max(vals.length - 1, 1)) * w)},${Math.round(h - ((v - mn) / (mx - mn || 1)) * (h - 4) - 2)}`).join(" ")}
            <div>
              <div class="text-[10px] text-muted">{m.label}</div>
              <svg viewBox={`0 0 ${w} ${h}`} class="h-8 w-full overflow-visible">
                <polyline points={pts} fill="none" stroke="rgb(var(--c-accent))" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round" />
                {#each vals as v, i}
                  <circle cx={Math.round((i / Math.max(vals.length - 1, 1)) * w)} cy={Math.round(h - ((v - mn) / (mx - mn || 1)) * (h - 4) - 2)} r="2" fill="rgb(var(--c-accent))" />
                {/each}
              </svg>
            </div>
          {/each}
        </div>
      {/if}

      {#if trends.drill_rate?.total > 0}
        <div class="mt-4 text-xs text-muted">{trends.drill_rate.total} {tr("total drills across all sessions")}</div>
      {/if}
    </section>
  {:else}
    <p class="mt-6 text-sm text-muted">{tr("Not enough sessions for trends yet.")}</p>
  {/if}
{:else}
  <div class="mt-5 flex flex-wrap items-end gap-3 text-sm">
    <label class="text-xs text-muted">{tr("Earlier")}
      <select bind:value={a} class="mt-1 block rounded-lg border-2 border-line bg-surface px-3 py-2 transition focus:border-accent focus:outline-none">
        {#each reports as r (r.stem)}<option value={r.stem}>{r.name || r.stem}</option>{/each}
      </select>
    </label>
    <label class="text-xs text-muted">{tr("Later")}
      <select bind:value={b} class="mt-1 block rounded-lg border-2 border-line bg-surface px-3 py-2 transition focus:border-accent focus:outline-none">
        {#each reports as r (r.stem)}<option value={r.stem}>{r.name || r.stem}</option>{/each}
      </select>
    </label>
    <button
      onclick={runCompare}
      disabled={!a || !b || a === b}
      class="rounded-lg bg-accent px-4 py-2 font-semibold text-white transition hover:opacity-90 disabled:opacity-40"
    >{tr("Compare")}</button>
  </div>

  {#if canCompareVideos}
    <div class="mt-4">
      <CompareVideos a={{ stem: a, label: aReport.stem }} b={{ stem: b, label: bReport.stem }} />
    </div>
  {/if}

  {#if cmpError}<p class="mt-2 text-sm text-bad">{cmpError}</p>{/if}

  {#if diff}
    <div class="card mt-4 space-y-4 p-5">
      {#if diff.text}<p class="text-sm text-muted">{diff.text}</p>{/if}

      {#each [
        { label: "Improved", items: diff.improved, chipClass: "border-good/50 bg-good/10 text-good" },
        { label: "Still an issue", items: diff.unchanged, chipClass: "border-line bg-surface/80 text-muted" },
        { label: "New / regressed", items: diff.regressed, chipClass: "border-bad/50 bg-bad/10 text-bad" },
      ] as { label, items, chipClass }}
        {#if items?.length}
          <div>
            <p class="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted">{tr(label)}</p>
            <div class="flex flex-wrap gap-1.5">
              {#each items as item}<span class="rounded-full border px-2.5 py-0.5 text-xs {chipClass}">{item}</span>{/each}
            </div>
          </div>
        {/if}
      {/each}

      {#if diff.metric_deltas && Object.keys(diff.metric_deltas).length}
        <div>
          <p class="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted">{tr("Metric changes")}</p>
          <div class="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {#each Object.entries(diff.metric_deltas) as [k, v]}
              <div class="rounded-xl border border-line bg-surface/60 px-3 py-2.5 text-center">
                <div class="font-display text-xl font-bold {v > 0 ? 'text-good' : v < 0 ? 'text-bad' : 'text-muted'}">{v > 0 ? '+' : ''}{v}</div>
                <div class="mt-0.5 text-[10px] uppercase tracking-wide text-muted">{k}</div>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {/if}
{/if}
