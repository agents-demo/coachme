<script>
  import { tr } from "$lib/appearance";
  import { fmtTime } from "$lib/format";

  let { report } = $props();

  const frames = $derived(
    (report?.metrics?.pose || []).map((p, i) => ({ ...p, i })).filter((p) => p.landmarks3d),
  );
  const times = $derived(report.frame_times || []);
  const p3 = $derived(report.metrics?.pose3d_summary || {});

  let idxRaw = $state(0);
  let yaw = $state(-0.5);
  let pitch = $state(0.15);
  let dragging = $state(false);
  let last = $state([0, 0]);

  const idx = $derived(Math.min(idxRaw, Math.max(0, frames.length - 1)));

  const CONN = [
    [11, 12], [11, 13], [13, 15], [12, 14], [14, 16], [11, 23], [12, 24], [23, 24],
    [23, 25], [25, 27], [24, 26], [26, 28], [27, 29], [29, 31], [28, 30], [30, 32],
    [15, 17], [15, 19], [16, 18], [16, 20], [17, 19], [18, 20], [9, 10], [5, 9],
    [6, 10], [5, 6], [5, 7], [7, 9], [6, 8], [8, 10], [0, 1], [0, 2], [1, 3], [2, 4],
  ];

  const projected = $derived.by(() => {
    const f = frames[idx];
    if (!f) return [];
    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    const cx = Math.cos(pitch), sx = Math.sin(pitch);
    const raw = f.landmarks3d.map(([x, y, z]) => {
      const x1 = x * cy + z * sy;
      const z1 = -x * sy + z * cy;
      const y2 = y * cx - z1 * sx;
      return [x1, y2];
    });
    const xs = raw.map((p) => p[0]);
    const ys = raw.map((p) => p[1]);
    const minx = Math.min(...xs), maxx = Math.max(...xs);
    const miny = Math.min(...ys), maxy = Math.max(...ys);
    const span = Math.max(maxx - minx, maxy - miny) || 1;
    const s = 80 / span;
    const ox = 50 - ((minx + maxx) / 2) * s;
    const oy = 50 - ((miny + maxy) / 2) * s;
    return raw.map((p) => [p[0] * s + ox, p[1] * s + oy]);
  });

  function down(e) {
    dragging = true;
    last = [e.clientX, e.clientY];
  }
  function move(e) {
    if (!dragging) return;
    yaw += (e.clientX - last[0]) * 0.01;
    pitch = Math.max(-1.2, Math.min(1.2, pitch + (e.clientY - last[1]) * 0.01));
    last = [e.clientX, e.clientY];
  }
  function up() {
    dragging = false;
  }
</script>

<div>
  {#if Object.keys(p3).length}
    <div class="rounded-xl border-2 border-line p-3">
      <div class="text-[11px] font-semibold uppercase tracking-wide text-accent">{tr("3D biomechanics (world-landmark mean)")}</div>
      <div class="mt-1.5 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted sm:grid-cols-4">
        {#each [[tr("L knee"), p3.l_knee_3d_mean], [tr("R knee"), p3.r_knee_3d_mean], [tr("L elbow"), p3.l_elbow_3d_mean], [tr("R elbow"), p3.r_elbow_3d_mean], [tr("Torso lean"), p3.torso_lean_mean], [tr("Shoulder twist"), p3.shoulder_twist_mean], [tr("Hip twist"), p3.hip_twist_mean]] as [label, val]}
          {#if val != null}<div><span class="font-semibold text-app">{val}°</span> {label}</div>{/if}
        {/each}
      </div>
      <p class="mt-1.5 text-[11px] text-muted">{tr("Approximate 3D from a single camera — treat as an indicator, not a precise measurement.")}</p>
    </div>
  {/if}
  {#if !frames.length}
    <p class="mt-3 rounded-xl border-2 border-line p-4 text-sm text-muted">
      {tr("No 3D pose in this report. Re-run the analysis to capture it.")}
    </p>
  {:else}
    <div class="mt-3 grid gap-3 sm:grid-cols-[minmax(0,1fr)_11rem]">
      <div
        class="relative h-72 overflow-hidden rounded-[14px] border-2 border-line bg-surface"
        class:cursor-grabbing={dragging}
        class:cursor-grab={!dragging}
        onpointerdown={down} onpointermove={move} onpointerup={up} onpointerleave={up}
      >
        <svg viewBox="0 0 100 100" class="h-full w-full touch-none">
          <line x1="50" y1="10" x2="50" y2="90" stroke="currentColor" stroke-width="0.2" class="text-line" opacity="0.4" />
          {#each CONN as [a, b]}
            {#if projected[a] && projected[b]}
              <line x1={projected[a][0]} y1={projected[a][1]} x2={projected[b][0]} y2={projected[b][1]} stroke="#38bdf8" stroke-width="1.1" stroke-linecap="round" />
            {/if}
          {/each}
          {#each projected as p}
            <circle cx={p[0]} cy={p[1]} r="1.1" fill="#f97316" />
          {/each}
        </svg>
      </div>

      <div class="text-xs text-muted">
        <label class="block">{tr("Frame")} <span class="font-mono text-app">{idx + 1}</span> / {frames.length}</label>
        <input type="range" min="0" max={frames.length - 1} step="1" bind:value={idxRaw} class="mt-1 w-full" />
        {#if times.length}<div class="mt-1 font-mono">{fmtTime(times[frames[idx]?.i] || 0)}</div>{/if}
        <div class="mt-3 font-semibold text-app">{report.metrics?.pose3d_summary?.torso_lean_mean ?? "—"}{tr("° torso lean")}</div>
        <div>{tr("shoulder twist")} {report.metrics?.pose3d_summary?.shoulder_twist_mean ?? "—"}°</div>
        <div>{tr("hip twist")} {report.metrics?.pose3d_summary?.hip_twist_mean ?? "—"}°</div>
        <button onclick={() => { yaw = -0.5; pitch = 0.15; }} class="mt-3 rounded-lg border-2 border-line px-2.5 py-1 font-semibold text-app">{tr("Reset view")}</button>
      </div>
    </div>
  {/if}
</div>

