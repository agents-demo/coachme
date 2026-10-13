<script>
  let { series = [] } = $props();

  const pts = $derived((series || []).filter((p) => p && p.x != null));
  const W = 640;
  const H = 130;
  const P = 16;
  const t0 = $derived(pts.length ? pts[0].t : 0);
  const t1 = $derived(pts.length ? pts[pts.length - 1].t : 1);
  const lo = $derived(pts.length ? Math.min(...pts.map((p) => p.x)) : 0);
  const hi = $derived(pts.length ? Math.max(...pts.map((p) => p.x)) : 1);
  const span = $derived(Math.max(0.08, hi - lo));
  const dlo = $derived(Math.max(0, lo - span * 0.4));
  const dhi = $derived(Math.min(1, hi + span * 0.4));

  function X(t) {
    return P + ((t - t0) / (t1 - t0 || 1)) * (W - 2 * P);
  }
  function Y(x) {
    return H - P - ((x - dlo) / (dhi - dlo || 1)) * (H - 2 * P);
  }

  const line = $derived(
    pts.map((p, i) => `${i ? "L" : "M"}${X(p.t).toFixed(1)} ${Y(p.x).toFixed(1)}`).join(" "),
  );
  const bandTop = $derived(Y(hi));
  const bandBottom = $derived(Y(lo));
</script>

{#if pts.length > 1}
  <figure class="rounded-xl border-2 border-line bg-surface p-2">
    <svg viewBox={`0 0 ${W} ${H}`} class="w-full" role="img" aria-label="Lower-body side-to-side position over the clip">
      <rect
        x={P}
        y={bandTop}
        width={W - 2 * P}
        height={Math.max(0.5, bandBottom - bandTop)}
        fill="rgba(79,70,229,0.12)"
      />
      <line x1={P} y1={bandBottom} x2={W - P} y2={bandBottom} stroke="#4f46e5" stroke-dasharray="3 3" stroke-width="0.75" opacity="0.5" />
      <line x1={P} y1={bandTop} x2={W - P} y2={bandTop} stroke="#4f46e5" stroke-dasharray="3 3" stroke-width="0.75" opacity="0.5" />
      <path d={line} fill="none" stroke="#4f46e5" stroke-width="1.5" stroke-linejoin="round" />
      <text x={P} y={H - 3} font-size="9" fill="currentColor" opacity="0.6">left ←  → right (over time)</text>
    </svg>
    <figcaption class="mt-1 text-xs text-muted">
      Your lower body's left–right position through the clip; the shaded band is the travel range.
    </figcaption>
  </figure>
{/if}
