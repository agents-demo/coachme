<script>
  let { segments = [], duration = 1, playhead = 0, onseek } = $props();
</script>

{#if segments.length}
  <div>
    <div class="relative h-7 w-full overflow-hidden rounded-lg border-2 border-line bg-surface">
      {#each segments as s}
        <button
          onclick={() => onseek?.(s.start)}
          title="{s.label} · {s.start}–{s.end}s"
          class="absolute top-0 h-full overflow-hidden border-r border-white/20 px-1 text-left text-[10px] font-semibold text-white"
          style="left:{(s.start / duration) * 100}%; width:{Math.max(2, ((s.end - s.start) / duration) * 100)}%; background:#3b82f6; opacity:0.6"
        ><span class="block truncate">{s.label}</span></button>
      {/each}
      <span class="pointer-events-none absolute inset-y-0 w-0.5 bg-accent" style={`left:${(Math.min(Math.max(playhead, 0), duration) / duration) * 100}%`}></span>
    </div>
  </div>
{/if}
