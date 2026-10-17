<script>
  import { tr } from "$lib/appearance";
  import { source } from "$lib/api";

  // a = earlier (left), b = later (right); each { stem, label }
  let { a, b } = $props();

  let pos = $state(50);
  let playing = $state(false);
  let va = $state();
  let vb = $state();
  let syncing = false;

  function togglePlay() {
    if (!va || !vb) return;
    if (playing) {
      va.pause();
      vb.pause();
      playing = false;
    } else {
      va.play();
      vb.play();
      playing = true;
    }
  }
  function onA() {
    if (syncing || !va || !vb || !va.duration || !vb.duration) return;
    syncing = true;
    vb.currentTime = (va.currentTime / va.duration) * vb.duration;
    syncing = false;
  }
  function onB() {
    if (syncing || !va || !vb || !va.duration || !vb.duration) return;
    syncing = true;
    va.currentTime = (vb.currentTime / vb.duration) * va.duration;
    syncing = false;
  }
</script>

<div class="relative overflow-hidden rounded-xl border-2 border-line">
  <!-- svelte-ignore a11y_media_has_caption -->
  <video src={source(b.stem)} bind:this={vb} muted playsinline preload="metadata" class="block w-full" ontimeupdate={onB}></video>
  <!-- svelte-ignore a11y_media_has_caption -->
  <video
    src={source(a.stem)}
    bind:this={va}
    muted
    playsinline
    preload="metadata"
    class="absolute inset-0 h-full w-full object-cover"
    style={`clip-path: inset(0 ${100 - pos}% 0 0)`}
    ontimeupdate={onA}
  ></video>
  <div class="pointer-events-none absolute inset-y-0 z-10 w-0.5 bg-white/90 shadow" style={`left:${pos}%`}></div>
  <input
    type="range"
    min="0"
    max="100"
    bind:value={pos}
    aria-label="Compare position"
    class="absolute inset-0 z-20 h-full w-full cursor-ew-resize opacity-0"
  />
  <span class="absolute left-2 top-2 z-30 rounded-full bg-ink/70 px-2 py-0.5 text-[11px] font-semibold text-app backdrop-blur">{a.label}</span>
  <span class="absolute right-2 top-2 z-30 rounded-full bg-ink/70 px-2 py-0.5 text-[11px] font-semibold text-app backdrop-blur">{b.label}</span>
</div>
<div class="mt-2 flex flex-wrap items-center gap-3 text-sm">
  <button onclick={togglePlay} class="rounded-lg border-2 border-line px-3 py-1.5 font-semibold">{playing ? "⏸ Pause both" : "▶ Play both"}</button>
  <span class="text-xs text-muted">{tr("Drag the divider — left = earlier, right = later (playback synced by progress).")}</span>
</div>
