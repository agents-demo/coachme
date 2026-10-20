<script>
  import { fmtTime } from "$lib/format";

  let { markers = [], duration = 1, playhead = 0, onseek } = $props();

  let el = $state();
  const TONE = { high: "#fb7185", medium: "#fbbf24", low: "#94a3b8" };

  function seek(event) {
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const frac = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
    onseek?.(frac * duration);
  }
</script>

<div
  bind:this={el}
  onclick={seek}
  role="slider"
  aria-label="issue timeline"
  tabindex="0"
  class="relative h-6 w-full cursor-pointer rounded-full border-2 border-line bg-surface"
>
  {#each markers as m}
    <span
      class="absolute top-1/2 h-3.5 w-1.5 -translate-y-1/2 rounded-full"
      style={`left:calc(${(m.t / duration) * 100}% - 3px); background:${TONE[m.confidence] || TONE.low}`}
      title={`${fmtTime(m.t)}${m.confidence ? ` · ${m.confidence} confidence` : ""}${m.text ? `\n${m.text}` : ""}`}
    ></span>
  {/each}
  <span class="absolute inset-y-0 w-0.5 bg-accent" style={`left:${(playhead / duration) * 100}%`}></span>
</div>
