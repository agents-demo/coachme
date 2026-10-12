<script>
  let { series = [], playhead = 0, onseek } = $props();

  let el = $state();
  const maxE = $derived(Math.max(0.0001, ...series.map((s) => s.energy)));
  const tMax = $derived(Math.max(0.001, ...series.map((s) => s.t)));

  function seek(evt) {
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const frac = Math.max(0, Math.min(1, (evt.clientX - rect.left) / rect.width));
    onseek?.(frac * tMax);
  }
</script>

<div
  bind:this={el}
  onclick={seek}
  role="slider"
  aria-label="movement over time"
  tabindex="0"
  class="relative h-6 w-full cursor-pointer overflow-hidden rounded-full border-2 border-line bg-surface"
>
  <div class="flex h-full items-end gap-px px-px">
    {#each series as s}
      <span class="flex-1 rounded-t-sm" style={`height:${Math.max(6, (s.energy / maxE) * 100)}%; background:#3b82f6; opacity:0.55`}></span>
    {/each}
  </div>
  <span
    class="absolute inset-y-0 w-0.5 bg-accent"
    style={`left:${(Math.min(Math.max(playhead, 0), tMax) / tMax) * 100}%`}
  ></span>
</div>
