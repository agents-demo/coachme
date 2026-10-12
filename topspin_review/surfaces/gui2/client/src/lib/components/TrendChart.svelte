<script>
  let { points = [], color = "#4f46e5", caption = "", unit = "" } = $props();

  const W = 320;
  const H = 90;
  const pad = 10;

  const values = $derived(points.map((p) => Number(p.value) || 0));
  const maxV = $derived(Math.max(1, ...values));
  const minV = $derived(Math.min(0, ...values));
  const X = (i) => (points.length > 1 ? pad + (W - 2 * pad) * (i / (points.length - 1)) : W / 2);
  const Y = (v) => H - pad - (H - 2 * pad) * ((v - minV) / Math.max(1e-6, maxV - minV));
  const path = $derived(values.map((v, i) => `${i ? "L" : "M"}${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(" "));
  const last = $derived(values.length ? values[values.length - 1] : "—");
</script>

<div class="card p-4">
  <div class="flex items-baseline justify-between">
    <span class="text-[11px] uppercase tracking-wide text-muted">{caption}</span>
    <span class="font-display text-lg font-bold" style={`color:${color}`}>{last}{unit}</span>
  </div>
  {#if points.length > 1}
    <svg viewBox={`0 0 ${W} ${H}`} class="mt-2 w-full" role="img" aria-label={caption}>
      <path d={path} fill="none" stroke={color} stroke-width="2" vector-effect="non-scaling-stroke" />
      {#each values as v, i (i)}
        <circle cx={X(i)} cy={Y(v)} r="2.5" fill={color} />
      {/each}
    </svg>
  {:else}
    <p class="mt-2 text-xs text-muted">Need ≥ 2 sessions to show a trend.</p>
  {/if}
</div>
