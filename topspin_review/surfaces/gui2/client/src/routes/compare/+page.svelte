<script>
  import { onMount } from "svelte";
  import { base } from "$app/paths";
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
      if (reports.length >= 2) {
        b = reports[0].stem;
        a = reports[reports.length - 1].stem;
      }
    } finally {
      loading = false;
    }
  });
</script>

<section>
  <h1 class="font-display text-3xl font-extrabold">Compare sessions</h1>
  <p class="mt-1 max-w-2xl text-sm text-muted">
    Pick an earlier and a later session to see what improved, what regressed, and what's still open.
  </p>
</section>

{#if loading}
  <p class="mt-6 text-sm text-muted">Loading…</p>
{:else if reports.length < 2}
  <div class="card mt-5 p-6 text-center">
    <p class="text-sm text-muted">You need at least two sessions to compare.</p>
    <a
      href={`${base}/?new=1`}
      class="mt-4 inline-flex rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90"
    >New analysis</a>
  </div>
{:else}
  <div class="mt-5 flex flex-wrap items-end gap-3 text-sm">
    <label class="text-xs text-muted">Earlier
      <select bind:value={a} class="mt-1 block rounded-lg border-2 border-line bg-surface px-3 py-2 transition focus:border-accent focus:outline-none">
        {#each reports as r (r.stem)}<option value={r.stem}>{r.stem}</option>{/each}
      </select>
    </label>
    <label class="text-xs text-muted">Later
      <select bind:value={b} class="mt-1 block rounded-lg border-2 border-line bg-surface px-3 py-2 transition focus:border-accent focus:outline-none">
        {#each reports as r (r.stem)}<option value={r.stem}>{r.stem}</option>{/each}
      </select>
    </label>
    <button
      onclick={runCompare}
      disabled={!a || !b || a === b}
      class="rounded-lg bg-accent px-4 py-2 font-semibold text-white transition hover:opacity-90 disabled:opacity-40"
    >Compare</button>
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
            <p class="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted">{label}</p>
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
          <p class="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted">Metric changes</p>
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
