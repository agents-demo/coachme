<script>
  import { onMount } from "svelte";
  import { getReports, compare } from "$lib/api";
  import { scoreTone } from "$lib/format";
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

  onMount(async () => {
    try {
      reports = (await getReports()).reports;
      if (reports.length >= 2) {
        b = reports[0].stem; // newest (list is newest-first)
        a = reports[reports.length - 1].stem; // oldest
      }
    } finally {
      loading = false;
    }
  });

  async function runCompare() {
    cmpError = "";
    diff = null;
    try {
      diff = await compare(a, b);
    } catch (e) {
      cmpError = String(e?.message || e);
    }
  }
</script>

<h1 class="font-display text-3xl font-bold">Progress</h1>
<p class="mt-1 text-sm text-muted">How your game is trending across sessions.</p>

{#if loading}
  <p class="mt-6 text-sm text-muted">Loading…</p>
{:else if !reports.length}
  <p class="mt-6 text-sm text-muted">Analyze a few sessions to see your progress.</p>
{:else}
  <h2 class="mt-6 font-display text-lg font-bold">Sessions</h2>
  <div class="mt-3 overflow-hidden rounded-xl border-2 border-line">
    <table class="w-full text-sm">
      <thead class="bg-surface text-left text-xs uppercase text-muted">
        <tr><th class="px-3 py-2">Session</th><th class="px-3 py-2">Sport</th><th class="px-3 py-2">Issues</th><th class="px-3 py-2">Score</th><th class="px-3 py-2">Focus</th></tr>
      </thead>
      <tbody>
        {#each reports as r (r.stem)}
          <tr class="border-t-2 border-line">
            <td class="px-3 py-2 font-semibold">{r.stem}</td>
            <td class="px-3 py-2 text-muted">{r.sport}</td>
            <td class="px-3 py-2">{r.issue_count}</td>
            <td class="px-3 py-2 {scoreTone(r.score)}">{r.score}</td>
            <td class="px-3 py-2 text-muted">{r.focus}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>

  {#if reports.length >= 2}
    <h2 class="mt-8 font-display text-lg font-bold">Compare two sessions</h2>
    <div class="mt-3 flex flex-wrap items-end gap-3 text-sm">
      <label class="text-xs text-muted">Earlier
        <select bind:value={a} class="mt-1 block rounded-lg border-2 border-line bg-surface px-3 py-2">
          {#each reports as r (r.stem)}<option value={r.stem}>{r.stem}</option>{/each}
        </select>
      </label>
      <label class="text-xs text-muted">Later
        <select bind:value={b} class="mt-1 block rounded-lg border-2 border-line bg-surface px-3 py-2">
          {#each reports as r (r.stem)}<option value={r.stem}>{r.stem}</option>{/each}
        </select>
      </label>
      <button onclick={runCompare} disabled={a === b} class="rounded-lg bg-accent px-4 py-2 font-semibold text-white disabled:opacity-50">Compare</button>
    </div>
    {#if canCompareVideos}
      <div class="mt-4">
        <CompareVideos a={{ stem: a, label: aReport.stem }} b={{ stem: b, label: bReport.stem }} />
      </div>
    {/if}
    {#if cmpError}<p class="mt-2 text-sm text-bad">{cmpError}</p>{/if}
    {#if diff}
      <p class="mt-3 text-sm">{diff.text}</p>
      {#each [["Improved", diff.improved], ["Still an issue", diff.unchanged], ["New / regressed", diff.regressed]] as [label, items]}
        {#if items?.length}
          <p class="mt-1 text-sm"><b>{label}:</b> {items.join(", ")}</p>
        {/if}
      {/each}
      {#if diff.metric_deltas && Object.keys(diff.metric_deltas).length}
        <div class="mt-2 text-xs text-muted">
          {#each Object.entries(diff.metric_deltas) as [k, v]}<span class="mr-3">{k}: {v > 0 ? "+" : ""}{v}</span>{/each}
        </div>
      {/if}
    {/if}
  {/if}
{/if}
