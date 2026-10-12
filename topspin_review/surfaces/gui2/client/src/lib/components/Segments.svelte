<script>
  let { segments = [], duration = 1, onseek } = $props();
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
    </div>
    <p class="mt-1 text-xs text-muted">
      Auto-segmented phases — click a block to jump (heuristic).
      <span class="font-mono">ball.phase_segments()</span> · step <span>tracking ball</span> · <span class="font-mono">report → metrics.ball.segments</span>
    </p>
  </div>
{/if}
