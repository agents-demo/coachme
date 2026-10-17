<script>
  import { tr } from "$lib/appearance";
  import { onMount } from "svelte";
  import { base } from "$app/paths";
  import { page } from "$app/stores";
  import { replaceState } from "$app/navigation";
  import { getReports, compare } from "$lib/api";
  import CompareVideos from "$lib/components/CompareVideos.svelte";

  let reports = $state([]);
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

  function sessionLabel(r) {
    const parts = [r.stem];
    if (r.sport) parts.push(r.sport);
    if (r.date) parts.push(r.date);
    return parts.join(" · ");
  }

  function syncUrl() {
    const url = new URL($page.url);
    if (a) url.searchParams.set("a", a); else url.searchParams.delete("a");
    if (b) url.searchParams.set("b", b); else url.searchParams.delete("b");
    replaceState(url, {});
  }

  function setA(v) { a = v; diff = null; cmpError = ""; syncUrl(); }
  function setB(v) { b = v; diff = null; cmpError = ""; syncUrl(); }

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
      reports = (await getReports()).reports;
      // Prefer URL params, then default to two most-recent sessions.
      const paramA = $page.url.searchParams.get("a");
      const paramB = $page.url.searchParams.get("b");
      if (reports.length >= 2) {
        a = (paramA && reports.find((r) => r.stem === paramA)) ? paramA : reports[1].stem;
        b = (paramB && reports.find((r) => r.stem === paramB)) ? paramB : reports[0].stem;
      }
    } finally {
      loading = false;
    }
  });
</script>

<section>
  <h1 class="font-display text-3xl font-extrabold">{tr("Compare sessions")}</h1>
  <p class="mt-1 max-w-2xl text-sm text-muted">
    {tr("Pick an earlier and a later session to see what improved, what regressed, and what's still open.")}
  </p>
</section>

{#if loading}
  <p class="mt-6 text-sm text-muted">{tr("Loading…")}</p>
{:else if reports.length < 2}
  <div class="card mt-5 p-6 text-center">
    <p class="text-sm text-muted">{tr("You need at least two sessions to compare.")}</p>
    <a
      href={`${base}/?new=1`}
      class="mt-4 inline-flex rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90"
    >{tr("New analysis")}</a>
  </div>
{:else}
  <div class="mt-5 flex flex-wrap items-end gap-3 text-sm">
    <label class="text-xs text-muted">{tr("Earlier")}
      <select value={a} onchange={(e) => setA(e.currentTarget.value)} class="mt-1 block rounded-lg border-2 border-line bg-surface px-3 py-2 transition focus:border-accent focus:outline-none">
        {#each reports as r (r.stem)}<option value={r.stem}>{sessionLabel(r)}</option>{/each}
      </select>
    </label>
    <label class="text-xs text-muted">{tr("Later")}
      <select value={b} onchange={(e) => setB(e.currentTarget.value)} class="mt-1 block rounded-lg border-2 border-line bg-surface px-3 py-2 transition focus:border-accent focus:outline-none">
        {#each reports as r (r.stem)}<option value={r.stem}>{sessionLabel(r)}</option>{/each}
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

  {#if cmpError}
    <p class="mt-2 text-sm text-bad">{cmpError}</p>
  {/if}

  {#if diff}
    <div class="card mt-4 space-y-4 p-5">
      {#if diff.text}
        <p class="text-sm text-muted">{diff.text}</p>
      {/if}

      {#each [
        { label: "Improved", items: diff.improved, chipClass: "border-good/50 bg-good/10 text-good" },
        { label: "Still an issue", items: diff.unchanged, chipClass: "border-line bg-surface/80 text-muted" },
        { label: "New / regressed", items: diff.regressed, chipClass: "border-bad/50 bg-bad/10 text-bad" },
      ] as { label, items, chipClass }}
        {#if items?.length}
          <div>
            <p class="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted">{tr(label)}</p>
            <div class="flex flex-wrap gap-1.5">
              {#each items as item}
                <span class="rounded-full border px-2.5 py-0.5 text-xs {chipClass}">{item}</span>
              {/each}
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
