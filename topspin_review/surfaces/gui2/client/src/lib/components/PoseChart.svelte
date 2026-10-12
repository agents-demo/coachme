<script>
  import { fmtTime } from "$lib/format";

  let { report } = $props();

  const times = $derived(report.frame_times || []);
  const pose = $derived(report.metrics?.pose || []);
  const p3 = $derived(report.metrics?.pose3d_summary || {});

  const SERIES = [
    { key: "l_knee", label: "Left knee", color: "#4f46e5" },
    { key: "r_knee", label: "Right knee", color: "#818cf8" },
    { key: "l_elbow", label: "Left elbow", color: "#34d399" },
    { key: "r_elbow", label: "Right elbow", color: "#fbbf24" },
  ];

  const W = 640;
  const H = 170;
  const pad = 8;
  const MAXV = 180; // joint angles in degrees

  const series = $derived.by(() =>
    SERIES.map((s) => ({
      ...s,
      pts: times
        .map((t, i) => ({ t: Number(t), v: pose[i]?.[s.key] }))
        .filter((p) => p.v != null),
    })),
  );
  const hasData = $derived(series.some((s) => s.pts.length > 1));
  const tMax = $derived(Math.max(0.001, ...times.map((t) => Number(t))));

  const X = (t) => pad + (W - 2 * pad) * (t / tMax);
  const Y = (v) => H - pad - (H - 2 * pad) * (Math.max(0, Math.min(MAXV, v)) / MAXV);
  const path = (pts) => pts.map((p, i) => `${i ? "L" : "M"}${X(p.t).toFixed(1)},${Y(p.v).toFixed(1)}`).join(" ");
</script>

{#if hasData}
  <div>
    <svg viewBox={`0 0 ${W} ${H}`} class="w-full" role="img" aria-label="joint angles over time">
      <line x1={pad} y1={Y(90)} x2={W - pad} y2={Y(90)} stroke="currentColor" stroke-width="1" opacity="0.12" />
      {#each series as s (s.key)}
        {#if s.pts.length}
          <path d={path(s.pts)} fill="none" stroke={s.color} stroke-width="2" vector-effect="non-scaling-stroke" />
        {/if}
      {/each}
    </svg>
    <div class="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-muted">
      {#each SERIES as s (s.key)}
        <span class="inline-flex items-center gap-1.5">
          <span class="inline-block h-2 w-3 rounded-full" style={`background:${s.color}`}></span>{s.label}
        </span>
      {/each}
      <span class="ml-auto">0°–180° · {fmtTime(tMax)}</span>
    </div>
    <p class="mt-1 text-xs text-muted">
      Joint angles over the clip (from the sampled frames). Useful for spotting a knee/elbow dip during the
      stroke. Values are pose estimates, not clinical measurements.
    </p>

    {#if Object.keys(p3).length}
      <div class="mt-3 rounded-xl border-2 border-line p-3">
        <div class="text-[11px] font-semibold uppercase tracking-wide text-accent">3D biomechanics (world-landmark mean)</div>
        <div class="mt-1.5 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted sm:grid-cols-4">
          {#each [["L knee", p3.l_knee_3d_mean], ["R knee", p3.r_knee_3d_mean], ["L elbow", p3.l_elbow_3d_mean], ["R elbow", p3.r_elbow_3d_mean], ["Torso lean", p3.torso_lean_mean], ["Shoulder twist", p3.shoulder_twist_mean], ["Hip twist", p3.hip_twist_mean]] as [label, val]}
            {#if val != null}<div><span class="font-semibold text-app">{val}°</span> {label}</div>{/if}
          {/each}
        </div>
        <p class="mt-1.5 text-[11px] text-muted">Approximate 3D from a single camera — treat as an indicator, not a precise measurement.</p>
      </div>
    {/if}
  </div>
{:else}
  <p class="text-sm text-muted">No pose angles for this run (pose unavailable or no person detected).</p>
{/if}
