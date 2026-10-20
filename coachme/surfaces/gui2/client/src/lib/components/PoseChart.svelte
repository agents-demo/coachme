<script>
  import { tr } from "$lib/appearance";
  import { fmtTime, POSE_SERIES } from "$lib/format";

  let { report, chrome = true } = $props();

  const times = $derived(report.frame_times || []);
  const pose = $derived(report.metrics?.pose || []);

  const SERIES = POSE_SERIES;

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
    {#if chrome}
      <div class="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-muted">
        {#each SERIES as s (s.key)}
          <span class="inline-flex items-center gap-1.5">
            <span class="inline-block h-2 w-3 rounded-full" style={`background:${s.color}`}></span>{tr(s.label)}
          </span>
        {/each}
        <span class="ml-auto">0°–180° · {fmtTime(tMax)}</span>
      </div>
      <p class="mt-1 text-xs text-muted">
        {tr("Joint angles over the clip (from the sampled frames). Useful for spotting a knee/elbow dip during the\n        stroke. Values are pose estimates, not clinical measurements.")}
      </p>
    {/if}
  </div>
{:else}
  <p class="text-sm text-muted">{tr("No pose angles for this run (pose unavailable or no person detected).")}</p>
{/if}
