<script>
  import { tr } from "$lib/appearance";
  import { trimUrl } from "$lib/api";

  let { report } = $props();

  const duration = $derived(Math.max(0.001, ...(report?.frame_times || [1])));
  let open = $state(false);
  let tStart = $state(0);
  let tEnd = $state(0);
  let tFmt = $state("mp4");
  let tVert = $state(false);

  $effect(() => {
    tEnd = Math.round(duration * 10) / 10;
  });
  const href = $derived(trimUrl(report.stem, tStart, tEnd, tFmt, tVert));

  function onKey(e) {
    if (e.key === "Escape") open = false;
  }
</script>

<svelte:window onkeydown={onKey} />

<button
  onclick={() => (open = true)}
  class="shrink-0 rounded-lg border-2 border-line px-3 py-1 text-xs font-semibold transition hover:border-accent"
  title={tr("Trim the clip and export mp4 / GIF / vertical")}
>✂ {tr("Trim & export")}</button>

{#if open}
  <div class="fixed inset-0 z-50 grid place-items-center bg-ink/80 p-4" role="presentation" onclick={() => (open = false)}>
    <div class="w-full max-w-lg rounded-2xl border-2 border-line bg-ink p-4 shadow-xl" role="presentation" onclick={(e) => e.stopPropagation()}>
      <div class="flex items-center justify-between gap-3">
        <h2 class="font-display font-bold">{tr("Trim & export")}</h2>
        <button onclick={() => (open = false)} title="Close" class="rounded-lg border-2 border-line px-2 py-0.5 text-sm font-semibold">✕</button>
      </div>
      <p class="mt-1 text-xs text-muted">{tr("Pick a range and download it as a clip.")}</p>

      <div class="mt-4 space-y-3 text-sm">
        <label class="block text-muted">{tr("Start")} <span class="font-mono text-app">{tStart.toFixed(1)}{tr("s")}</span>
          <input type="range" min="0" max={duration} step="0.1" bind:value={tStart} class="mt-1 block w-full" />
        </label>
        <label class="block text-muted">{tr("End")} <span class="font-mono text-app">{tEnd.toFixed(1)}{tr("s")}</span>
          <input type="range" min="0" max={duration} step="0.1" bind:value={tEnd} class="mt-1 block w-full" />
        </label>
        <div class="flex flex-wrap items-end gap-4">
          <label class="text-muted">{tr("Format")}
            <select bind:value={tFmt} class="mt-1 block rounded border-2 border-line bg-surface px-2 py-1">
              <option value="mp4">{tr("mp4")}</option>
              <option value="gif">{tr("gif")}</option>
            </select>
          </label>
          <label class="flex items-center gap-1 text-muted"><input type="checkbox" bind:checked={tVert} /> {tr("vertical 9:16")}</label>
        </div>
      </div>

      <div class="mt-5 flex justify-end gap-2">
        <button onclick={() => (open = false)} class="rounded-lg border-2 border-line px-4 py-2 text-sm font-semibold">{tr("Cancel")}</button>
        <a href={href} download class="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white">{tr("Export clip")}</a>
      </div>
    </div>
  </div>
{/if}
