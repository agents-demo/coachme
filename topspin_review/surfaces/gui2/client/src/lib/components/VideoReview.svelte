<script>
  import { source } from "$lib/api";
  import { issueGroups, movementSeries, fmtTime } from "$lib/format";
  import MotionChart from "./MotionChart.svelte";

  let { report } = $props();

  let video = $state();
  let currentTime = $state(0);

  const groups = $derived(issueGroups(report));
  const series = $derived(movementSeries(report));
  const isPhoto = $derived(/\.(png|jpg|jpeg|bmp|webp|gif)$/i.test(report.source || ""));

  const CONF_TONE = { high: "text-bad", medium: "text-warn", low: "text-muted" };

  // The issue whose moment is the most recent at/before the playhead.
  const activeGroup = $derived.by(() => {
    let best = -1;
    let bestT = -Infinity;
    groups.forEach((g, i) =>
      g.times.forEach((t) => {
        if (t <= currentTime + 0.8 && t > bestT) {
          bestT = t;
          best = i;
        }
      }),
    );
    return best;
  });

  function seek(t) {
    if (video) {
      try {
        video.currentTime = Number(t);
        video.play();
      } catch {}
    }
    currentTime = Number(t);
  }
  function onTime() {
    if (video) currentTime = video.currentTime;
  }
</script>

<div class="grid gap-6 lg:grid-cols-[minmax(0,1.9fr)_minmax(0,1fr)]">
  <div>
    {#if report.has_source}
      {#if isPhoto}
        <img src={source(report.stem)} alt="session photo" class="w-full rounded-[14px] border-2 border-line" />
      {:else}
        <!-- svelte-ignore a11y_media_has_caption -->
        <video bind:this={video} src={source(report.stem)} controls preload="metadata" ontimeupdate={onTime}></video>
      {/if}
    {:else}
      <p class="rounded-[14px] border-2 border-line p-6 text-sm text-muted">Media not found on disk.</p>
    {/if}

    {#if series.length}
      <div class="mt-3">
        <MotionChart {series} playhead={currentTime} onseek={seek} />
        <p class="mt-1 text-xs text-muted">
          Movement over time — a spike is a step or a swing. Click the chart to jump the video.
        </p>
      </div>
    {/if}
  </div>

  <div>
    <h3 class="font-display text-sm font-bold uppercase tracking-wide text-muted">
      Moments to review {#if groups.length}<span class="text-muted">· {groups.length}</span>{/if}
    </h3>
    {#if !groups.length}
      <p class="mt-2 text-sm text-muted">No timestamped issues.</p>
    {:else}
      <ol class="mt-2 space-y-2">
        {#each groups as g, i}
          <li
            class="rounded-xl border-2 p-3 transition"
            class:border-accent2={i === activeGroup}
            class:bg-surface={i === activeGroup}
            class:border-line={i !== activeGroup}
          >
            <div class="flex items-start gap-2">
              <span class="text-sm leading-snug">{g.text}</span>
              {#if g.confidence}
                <span class="ml-auto shrink-0 text-xs {CONF_TONE[g.confidence] || "text-muted"}">{g.confidence}</span>
              {/if}
            </div>
            {#if g.times.length}
              <div class="mt-2 flex flex-wrap gap-1.5">
                {#each g.times as t}
                  <button
                    onclick={() => seek(t)}
                    class="rounded-full border-2 border-line px-2.5 py-0.5 font-mono text-xs text-accent2 transition hover:border-accent2"
                  >▶ {fmtTime(t)}</button>
                {/each}
              </div>
            {/if}
          </li>
        {/each}
      </ol>
    {/if}
  </div>
</div>
