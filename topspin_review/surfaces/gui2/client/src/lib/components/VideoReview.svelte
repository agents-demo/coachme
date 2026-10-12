<script>
  import { source } from "$lib/api";
  import { issueGroups, movementSeries, fmtTime, CONF_TONE, CONF_HELP } from "$lib/format";
  import MotionChart from "./MotionChart.svelte";
  import Timeline from "./Timeline.svelte";

  let { report } = $props();

  let video = $state();
  let currentTime = $state(0);

  const groups = $derived(issueGroups(report));
  const series = $derived(movementSeries(report));
  const isPhoto = $derived(/\.(png|jpg|jpeg|bmp|webp|gif)$/i.test(report.source || ""));
  const duration = $derived(Math.max(0.001, ...(report.frame_times || [1])));
  const markers = $derived(groups.flatMap((g) => g.times.map((t) => ({ t, confidence: g.confidence }))));

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

  // A6: frame-step + slow-mo.
  const fps = $derived(Number(report.fps) || 30);
  let rate = $state(1);
  function setRate(r) {
    rate = r;
    if (video) video.playbackRate = r;
  }
  function step(dir) {
    if (!video) return;
    video.pause();
    video.currentTime = Math.max(0, video.currentTime + dir / fps);
    currentTime = video.currentTime;
  }
  function onLoaded() {
    if (video) video.playbackRate = rate;
  }
</script>

<div class="grid gap-6 lg:grid-cols-[minmax(0,1.9fr)_minmax(0,1fr)]">
  <div>
    {#if report.has_source}
      {#if isPhoto}
        <img src={source(report.stem)} alt="session photo" class="w-full rounded-[14px] border-2 border-line" />
      {:else}
        <!-- svelte-ignore a11y_media_has_caption -->
        <video bind:this={video} src={source(report.stem)} controls preload="metadata" ontimeupdate={onTime} onloadedmetadata={onLoaded}></video>
      {/if}
    {:else}
      <p class="rounded-[14px] border-2 border-line p-6 text-sm text-muted">Media not found on disk.</p>
    {/if}

    {#if report.has_source && !isPhoto}
      <div class="mt-2 flex flex-wrap items-center gap-2 text-sm">
        <button onclick={() => step(-1)} class="rounded-lg border-2 border-line px-2.5 py-1 font-semibold" title="Previous frame (step 1/fps)">⏮</button>
        <button onclick={() => step(1)} class="rounded-lg border-2 border-line px-2.5 py-1 font-semibold" title="Next frame (step 1/fps)">⏭</button>
        <span class="text-xs text-muted">frame step · {Math.round(fps)} fps</span>
        <div class="ml-auto inline-flex overflow-hidden rounded-lg border-2 border-line">
          {#each [0.25, 0.5, 1] as r}
            <button
              onclick={() => setRate(r)}
              class="px-2.5 py-1 text-xs font-semibold transition"
              class:bg-surface={rate === r}
              class:text-app={rate === r}
              class:text-muted={rate !== r}
            >{r}×</button>
          {/each}
        </div>
        <span class="font-mono text-xs text-muted">{fmtTime(currentTime)}</span>
      </div>
    {/if}

    {#if !isPhoto && report.has_source}
      <div class="mt-3">
        <Timeline {markers} {duration} playhead={currentTime} onseek={seek} />
        <p class="mt-1 text-xs text-muted">
          Issue timeline — each mark is a flagged moment (red = high, amber = medium, grey = low confidence). Click to jump.
        </p>
      </div>
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
                <span class="ml-auto shrink-0 text-xs {CONF_TONE[g.confidence] || "text-muted"}" title={CONF_HELP}>
                  {g.confidence} confidence
                </span>
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
