<script>
  import { source, saveAnnotations } from "$lib/api";
  import { issueGroups, movementSeries, fmtTime } from "$lib/format";
  import MotionChart from "./MotionChart.svelte";
  import Timeline from "./Timeline.svelte";
  import Segments from "./Segments.svelte";
  import Moments from "./Moments.svelte";

  let { report } = $props();

  let video = $state();
  let stage = $state();
  let currentTime = $state(0);

  const groups = $derived(issueGroups(report));
  const series = $derived(movementSeries(report));
  const isPhoto = $derived(/\.(png|jpg|jpeg|bmp|webp|gif)$/i.test(report.source || ""));
  const duration = $derived(Math.max(0.001, ...(report.frame_times || [1])));
  const markers = $derived(groups.flatMap((g) => g.times.map((t) => ({ t, confidence: g.confidence, text: g.text }))));

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

  // A6 frame-step + slow-mo.
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

  // B2 telestration: draw arrow / circle / pen on the frozen frame (normalized 0..1).
  const COLOR = "#f97316";
  let drawMode = $state(false);
  let tool = $state("arrow");
  let shapes = $state([]);
  let drawing = $state(null);
  let anglePts = $state([]);
  let dirty = $state(false);
  let status = $state("");

  $effect(() => {
    shapes = (report?.annotations || []).map((s) => ({ ...s }));
    dirty = false;
  });

  const clamp = (v) => Math.max(0, Math.min(1, v));
  function norm(evt) {
    const rect = stage.getBoundingClientRect();
    return [clamp((evt.clientX - rect.left) / rect.width), clamp((evt.clientY - rect.top) / rect.height)];
  }
  function start(evt) {
    if (!drawMode) return;
    if (video) video.pause();
    const [x, y] = norm(evt);
    if (tool === "angle") {
      const pts = [...anglePts, [x, y]];
      if (pts.length === 3) {
        shapes = [...shapes, { type: "angle", color: COLOR, points: pts }];
        anglePts = [];
        dirty = true;
      } else {
        anglePts = pts;
      }
      return;
    }
    drawing = tool === "pen" ? { type: "pen", color: COLOR, points: [[x, y]] } : { type: tool, color: COLOR, x1: x, y1: y, x2: x, y2: y };
  }
  function move(evt) {
    if (!drawing) return;
    const [x, y] = norm(evt);
    if (drawing.type === "pen") drawing = { ...drawing, points: [...drawing.points, [x, y]] };
    else drawing = { ...drawing, x2: x, y2: y };
  }
  function end() {
    if (!drawing) return;
    const done = drawing;
    drawing = null;
    // Ignore accidental taps (no drag) for the two-point tools.
    if (done.type !== "pen") {
      const d = Math.hypot(done.x2 - done.x1, done.y2 - done.y1);
      if (d < 0.01) return;
    }
    shapes = [...shapes, done];
    dirty = true;
  }
  function undo() {
    shapes = shapes.slice(0, -1);
    dirty = true;
  }
  function clear() {
    shapes = [];
    anglePts = [];
    dirty = true;
  }
  // Angle at the middle of 3 normalized points, corrected for the video's aspect ratio.
  function angleAt(pts) {
    const rect = stage?.getBoundingClientRect();
    const ar = rect && rect.height ? rect.width / rect.height : 1;
    const [a, b, c] = pts;
    const v1 = [(a[0] - b[0]) * ar, a[1] - b[1]];
    const v2 = [(c[0] - b[0]) * ar, c[1] - b[1]];
    const dot = v1[0] * v2[0] + v1[1] * v2[1];
    const n = Math.hypot(...v1) * Math.hypot(...v2);
    return n ? Math.round((Math.acos(Math.max(-1, Math.min(1, dot / n))) * 180) / Math.PI) : 0;
  }
  async function save() {
    status = "saving…";
    try {
      const saved = await saveAnnotations(report.stem, shapes);
      // Keep the parent report in sync so annotations survive a tab switch/remount.
      report.annotations = (saved?.annotations || shapes).map((s) => ({ ...s }));
      status = "saved";
      dirty = false;
    } catch (e) {
      status = String(e?.message || e);
    }
  }
</script>

{#snippet shape(s)}
  {#if s.type === "pen"}
    <polyline
      points={s.points.map((p) => `${p[0]},${p[1]}`).join(" ")}
      fill="none" stroke={s.color || COLOR} stroke-width="2" vector-effect="non-scaling-stroke"
    />
  {:else if s.type === "circle"}
    <ellipse
      cx={(s.x1 + s.x2) / 2} cy={(s.y1 + s.y2) / 2}
      rx={Math.abs(s.x2 - s.x1) / 2} ry={Math.abs(s.y2 - s.y1) / 2}
      fill="none" stroke={s.color || COLOR} stroke-width="2" vector-effect="non-scaling-stroke"
    />
  {:else if s.type === "angle"}
    <polyline
      points={s.points.map((p) => `${p[0]},${p[1]}`).join(" ")}
      fill="none" stroke={s.color || COLOR} stroke-width="2" vector-effect="non-scaling-stroke"
    />
    {#each s.points as p}
      <circle cx={p[0]} cy={p[1]} r="0.008" fill={s.color || COLOR} vector-effect="non-scaling-stroke" />
    {/each}
    <text
      x={s.points[1][0]} y={s.points[1][1] - 0.035}
      text-anchor="middle" font-size="0.045" font-weight="700" fill={s.color || COLOR}
      stroke="#0b0f14" stroke-width="0.006" paint-order="stroke"
    >{angleAt(s.points)}°</text>
  {:else}
    <line x1={s.x1} y1={s.y1} x2={s.x2} y2={s.y2} stroke={s.color || COLOR} stroke-width="2" vector-effect="non-scaling-stroke" />
    {#if s.type === "arrow"}
      <circle cx={s.x2} cy={s.y2} r="0.012" fill={s.color || COLOR} />
    {/if}
  {/if}
{/snippet}

<div>
  <div>
    {#if report.has_source}
      {#if isPhoto}
        <div class="relative" bind:this={stage}>
          <img src={source(report.stem)} alt="session photo" class="w-full rounded-[14px] border-2 border-line" />
          <svg
            class="absolute inset-0 h-full w-full {drawMode ? "cursor-crosshair" : "pointer-events-none"}"
            viewBox="0 0 1 1" preserveAspectRatio="none"
            onpointerdown={start} onpointermove={move} onpointerup={end} onpointerleave={end}
          >
            {#each shapes as s (s)}{@render shape(s)}{/each}
            {#if drawing}{@render shape(drawing)}{/if}
            {#if anglePts.length}
              {#each anglePts as p}<circle cx={p[0]} cy={p[1]} r="0.008" fill={COLOR} vector-effect="non-scaling-stroke" />{/each}
              {#if anglePts.length === 2}
                <line x1={anglePts[0][0]} y1={anglePts[0][1]} x2={anglePts[1][0]} y2={anglePts[1][1]} stroke={COLOR} stroke-width="2" vector-effect="non-scaling-stroke" />
              {/if}
            {/if}
          </svg>
        </div>
      {:else}
        <div class="relative" bind:this={stage}>
          <!-- svelte-ignore a11y_media_has_caption -->
          <video bind:this={video} class="w-full rounded-[14px] border-2 border-line" src={source(report.stem)} controls preload="metadata" ontimeupdate={onTime} onloadedmetadata={onLoaded}></video>
          <svg
            class="absolute inset-0 h-full w-full {drawMode ? "cursor-crosshair" : "pointer-events-none"}"
            viewBox="0 0 1 1" preserveAspectRatio="none"
            onpointerdown={start} onpointermove={move} onpointerup={end} onpointerleave={end}
          >
            {#each shapes as s (s)}{@render shape(s)}{/each}
            {#if drawing}{@render shape(drawing)}{/if}
            {#if anglePts.length}
              {#each anglePts as p}<circle cx={p[0]} cy={p[1]} r="0.008" fill={COLOR} vector-effect="non-scaling-stroke" />{/each}
              {#if anglePts.length === 2}
                <line x1={anglePts[0][0]} y1={anglePts[0][1]} x2={anglePts[1][0]} y2={anglePts[1][1]} stroke={COLOR} stroke-width="2" vector-effect="non-scaling-stroke" />
              {/if}
            {/if}
          </svg>
        </div>
      {/if}
    {:else}
      <p class="rounded-[14px] border-2 border-line p-6 text-sm text-muted">Media not found on disk.</p>
    {/if}

    <div class="mt-2 flex flex-wrap items-center gap-2 text-sm">
      <button
        onclick={() => (drawMode = !drawMode)}
        class="rounded-lg border-2 px-3 py-1 font-semibold transition"
        class:border-accent={drawMode}
        class:bg-surface={drawMode}
        class:border-line={!drawMode}
      >✏ {drawMode ? "Drawing" : "Draw"}</button>
      {#if drawMode}
        {#each [["arrow", "Arrow"], ["circle", "Circle"], ["pen", "Pen"], ["angle", "Angle"]] as [id, label]}
          <button
            onclick={() => (tool = id)}
            class="rounded-lg border-2 px-2.5 py-1 text-xs font-semibold transition"
            class:border-accent2={tool === id}
            class:border-line={tool !== id}
          >{label}</button>
        {/each}
        {#if tool === "angle"}<span class="text-xs text-muted">click 3 points — angle is at the 2nd</span>{/if}
        <button onclick={undo} class="rounded-lg border-2 border-line px-2.5 py-1 text-xs font-semibold">Undo</button>
        <button onclick={clear} class="rounded-lg border-2 border-line px-2.5 py-1 text-xs font-semibold">Clear</button>
        <button onclick={save} disabled={!dirty} class="rounded-lg bg-accent px-3 py-1 text-xs font-semibold text-white disabled:opacity-50">Save</button>
        {#if status}<span class="text-xs text-muted">{status}</span>{/if}
      {/if}
      {#if report.has_source && !isPhoto}
        <div class="ml-auto flex items-center gap-2">
          <button onclick={() => step(-1)} class="rounded-lg border-2 border-line px-2.5 py-1 font-semibold" title="Previous frame">⏮</button>
          <button onclick={() => step(1)} class="rounded-lg border-2 border-line px-2.5 py-1 font-semibold" title="Next frame">⏭</button>
          <div class="inline-flex overflow-hidden rounded-lg border-2 border-line">
            {#each [0.25, 0.5, 1] as r}
              <button onclick={() => setRate(r)} class="px-2 py-1 text-xs font-semibold transition" class:bg-surface={rate === r} class:text-app={rate === r} class:text-muted={rate !== r}>{r}×</button>
            {/each}
          </div>
          <span class="font-mono text-xs text-muted">{fmtTime(currentTime)}</span>
        </div>
      {/if}
    </div>

    {#if !isPhoto && report.has_source}
      <div class="mt-4">
        <h3 class="font-display text-sm font-bold uppercase tracking-wide text-muted">Timeline</h3>
        <p class="mt-1 text-xs text-muted">All tied to the playhead — watch them move together; click any to jump.</p>
        <div class="mt-2 space-y-3 rounded-xl border-2 border-line p-3">
          {#if series.length}
            <div>
              <div class="text-xs font-semibold text-muted">Movement</div>
              <div class="mt-1"><MotionChart {series} playhead={currentTime} onseek={seek} /></div>
            </div>
          {/if}
          {#if (report.metrics?.ball?.segments || []).length}
            <div>
              <div class="text-xs font-semibold text-muted">Rally phases</div>
              <div class="mt-1"><Segments segments={report.metrics?.ball?.segments || []} {duration} onseek={seek} /></div>
            </div>
          {/if}
          <div>
            <div class="text-xs font-semibold text-muted">Issues</div>
            <div class="mt-1"><Timeline {markers} {duration} playhead={currentTime} onseek={seek} /></div>
          </div>
        </div>
      </div>

      <div class="mt-4">
        <h3 class="font-display text-sm font-bold uppercase tracking-wide text-muted">Key moments</h3>
        <div class="mt-2">
          <Moments {report} />
        </div>
      </div>
    {/if}
  </div>
</div>
