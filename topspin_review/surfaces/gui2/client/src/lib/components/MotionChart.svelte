<script>
  import { fmtTime } from "$lib/format";

  let { series = [], playhead = 0, onseek } = $props();

  let svg = $state();
  const W = 640;
  const H = 90;
  const pad = 4;

  const maxE = $derived(Math.max(0.0001, ...series.map((s) => s.energy)));
  const tMax = $derived(Math.max(0.001, ...series.map((s) => s.t)));

  const X = (t) => pad + (W - 2 * pad) * (t / tMax);
  const Y = (e) => H - pad - (H - 2 * pad) * (e / maxE);

  const line = $derived(
    series.map((s, i) => `${i ? "L" : "M"}${X(s.t).toFixed(1)},${Y(s.energy).toFixed(1)}`).join(" "),
  );
  const area = $derived(`${line} L${X(tMax).toFixed(1)},${H - pad} L${X(0).toFixed(1)},${H - pad} Z`);
  const playX = $derived(X(Math.min(Math.max(playhead, 0), tMax)));

  function seek(evt) {
    const rect = svg.getBoundingClientRect();
    const x = ((evt.clientX - rect.left) / rect.width) * W;
    const t = Math.min(Math.max((x - pad) / (W - 2 * pad), 0), 1) * tMax;
    onseek?.(t);
  }
</script>

<div class="text-[10px] uppercase tracking-wide text-muted">Movement energy</div>
<svg
  bind:this={svg}
  viewBox={`0 0 ${W} ${H}`}
  class="w-full cursor-pointer select-none"
  onpointerdown={seek}
  onpointermove={(e) => e.buttons === 1 && seek(e)}
  role="img"
  aria-label="movement over time"
>
  <path d={area} fill="rgba(79,70,229,0.18)" />
  <path d={line} fill="none" stroke="#4f46e5" stroke-width="2" vector-effect="non-scaling-stroke" />
  <line x1={playX} y1={pad} x2={playX} y2={H - pad} stroke="#fb7185" stroke-width="2" vector-effect="non-scaling-stroke" />
</svg>
<div class="flex justify-between text-[10px] text-muted">
  <span>0s</span>
  <span>time (s)</span>
  <span>{fmtTime(tMax)}</span>
</div>
