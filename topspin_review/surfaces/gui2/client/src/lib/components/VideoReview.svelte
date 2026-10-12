<script>
  import { source, clip } from "$lib/api";
  import { moments, movementSeries, fmtTime } from "$lib/format";
  import MotionChart from "./MotionChart.svelte";

  let { report } = $props();

  let video = $state();
  let currentTime = $state(0);

  const ms = $derived(moments(report));
  const series = $derived(movementSeries(report));
  const isPhoto = $derived(/\.(png|jpg|jpeg|bmp|webp|gif)$/i.test(report.source || ""));
  const clipEntries = $derived(Object.entries(report.clips || {}));
  const activeIdx = $derived.by(() => {
    let best = -1;
    ms.forEach((m, i) => {
      if (m.t != null && m.t <= currentTime + 0.8) best = i;
    });
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

<div class="grid gap-5 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
  <div>
    {#if report.has_source}
      {#if isPhoto}
        <img src={source(report.stem)} alt="session photo" class="w-full rounded-[14px] border-2 border-line" />
      {:else}
        <!-- svelte-ignore a11y_media_has_caption -->
        <video
          bind:this={video}
          src={source(report.stem)}
          controls
          preload="metadata"
          ontimeupdate={onTime}
        ></video>
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
    <h3 class="font-display text-sm font-bold uppercase tracking-wide text-muted">Moments to review</h3>
    {#if !ms.length}
      <p class="mt-2 text-sm text-muted">No timestamped issues.</p>
    {:else}
      <ol class="mt-2 space-y-1.5">
        {#each ms as m, i}
          <li>
            <button
              onclick={() => m.t != null && seek(m.t)}
              class="w-full rounded-lg border-2 px-3 py-2 text-left text-sm transition"
              class:border-accent2={i === activeIdx}
              class:bg-surface={i === activeIdx}
              class:border-line={i !== activeIdx}
            >
              {#if m.t != null}<span class="mr-2 font-mono text-xs text-accent2">▶ {fmtTime(m.t)}</span>{/if}
              <span>{m.text}</span>
              {#if m.confidence}<span class="ml-2 text-xs text-muted">({m.confidence})</span>{/if}
            </button>
          </li>
        {/each}
      </ol>
    {/if}

    {#if clipEntries.length}
      <h3 class="mt-4 font-display text-sm font-bold uppercase tracking-wide text-muted">Key-moment clips</h3>
      <div class="mt-2 flex flex-col gap-2">
        {#each clipEntries as [key] (key)}
          <div>
            <div class="mb-1 text-xs text-muted">around {key}s</div>
            <!-- svelte-ignore a11y_media_has_caption -->
            <video src={clip(report.stem, key)} controls preload="none" class="w-full"></video>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>
