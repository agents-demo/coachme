<script>
  import { tr } from "$lib/appearance";
  let { series = [], lateral = null, steps = null } = $props();

  const pts = $derived((series || []).filter((p) => p && p.x != null));
  const W = 640;
  const H = 160;
  const L = 40; // room for the left/right labels
  const R = 12;
  const T = 12;
  const B = 26; // room for the time labels
  const t0 = $derived(pts.length ? pts[0].t : 0);
  const t1 = $derived(pts.length ? pts[pts.length - 1].t : 1);
  const lo = $derived(pts.length ? Math.min(...pts.map((p) => p.x)) : 0);
  const hi = $derived(pts.length ? Math.max(...pts.map((p) => p.x)) : 1);
  const span = $derived(Math.max(0.08, hi - lo));
  const dlo = $derived(Math.max(0, lo - span * 0.4));
  const dhi = $derived(Math.min(1, hi + span * 0.4));

  function X(t) {
    return L + ((t - t0) / (t1 - t0 || 1)) * (W - L - R);
  }
  function Y(x) {
    return T + ((dhi - x) / (dhi - dlo || 1)) * (H - T - B);
  }

  const line = $derived(
    pts.map((p, i) => `${i ? "L" : "M"}${X(p.t).toFixed(1)} ${Y(p.x).toFixed(1)}`).join(" "),
  );
  const bandTop = $derived(Y(hi));
  const bandBottom = $derived(Y(lo));
  const tMax = $derived(t1);
  const pct = $derived(Math.round((lateral ?? hi - lo) * 100));

  // Direction changes = points where the line reverses (same rule as the metric).
  const turns = $derived.by(() => {
    const xs = pts.map((p) => p.x);
    const out = [];
    for (let i = 1; i < xs.length - 1; i++) {
      const d1 = xs[i] - xs[i - 1];
      const d2 = xs[i + 1] - xs[i];
      if (d1 * d2 < 0 && Math.abs(d2) > 0.005) out.push(i);
    }
    return out;
  });
</script>

{#if pts.length > 1}
  <figure class="rounded-xl border-2 border-line bg-surface p-2">
    <svg viewBox={`0 0 ${W} ${H}`} class="w-full" role="img" aria-label="Lower-body side-to-side position over time">
      <!-- axes -->
      <line x1={L} y1={T} x2={L} y2={H - B} stroke="#9ca3af" stroke-width="1" />
      <line x1={L} y1={H - B} x2={W - R} y2={H - B} stroke="#9ca3af" stroke-width="1" />

      <!-- travel range band (its height is the "travel" number) -->
      <rect x={L} y={bandTop} width={W - L - R} height={Math.max(0.5, bandBottom - bandTop)} fill="rgba(79,70,229,0.12)" />
      <line x1={L} y1={bandBottom} x2={W - R} y2={bandBottom} stroke="#4f46e5" stroke-dasharray="3 3" stroke-width="0.75" opacity="0.5" />
      <line x1={L} y1={bandTop} x2={W - R} y2={bandTop} stroke="#4f46e5" stroke-dasharray="3 3" stroke-width="0.75" opacity="0.5" />
      <text x={W - R} y={bandTop - 4} text-anchor="end" font-size="11" fill="#4f46e5" font-weight="bold">{tr("travel")} {pct}%</text>

      <!-- the trace -->
      <path d={line} fill="none" stroke="#4f46e5" stroke-width="1.5" stroke-linejoin="round" />

      <!-- a dot at every direction change (the "direction changes" number) -->
      {#each turns as i (i)}
        <circle cx={X(pts[i].t)} cy={Y(pts[i].x)} r="3" fill="#fb7185" stroke="#fff" stroke-width="1" />
      {/each}

      <!-- y-axis labels: position (left at the bottom, right at the top) -->
      <text x={L - 4} y={T + 8} text-anchor="end" font-size="10" fill="currentColor" opacity="0.7">{tr("right")}</text>
      <text x={L - 4} y={H - B + 3} text-anchor="end" font-size="10" fill="currentColor" opacity="0.7">{tr("left")}</text>

      <!-- x-axis labels: time -->
      <text x={L} y={H - B + 16} text-anchor="start" font-size="10" fill="currentColor" opacity="0.7">{tr("0s")}</text>
      <text x={W - R} y={H - B + 16} text-anchor="end" font-size="10" fill="currentColor" opacity="0.7">{tMax.toFixed(1)}{tr("s")}</text>
      <text x={(L + W - R) / 2} y={H - 3} text-anchor="middle" font-size="10" fill="currentColor" opacity="0.6">{tr("time")}</text>
    </svg>
    <figcaption class="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted">
      <span>{tr("Shaded band = your side-to-side range (")}{pct}{tr("% of the frame width).")}</span>
      <span class="inline-flex items-center gap-1"><span class="inline-block h-2 w-2 rounded-full" style="background:#fb7185"></span> {steps ?? turns.length} {tr("changes of direction.")}</span>
    </figcaption>
  </figure>
{/if}
