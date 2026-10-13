<script>
  import { fmtTime } from "$lib/format";

  let { report, hideStats = false, hideControls = false } = $props();

  /** Reset the orbit view (exposed so callers can place the button elsewhere). */
  export function reset() {
    yaw = -0.5;
    pitch = 0.2;
  }

  const traj = $derived(report?.metrics?.ball?.trajectory3d || []);
  const stats = $derived(report?.metrics?.ball?.stats || {});

  let yaw = $state(-0.5);
  let pitch = $state(0.2);
  let dragging = $state(false);
  let last = $state([0, 0]);

  const projected = $derived.by(() => {
    if (traj.length < 2) return [];
    const cy = Math.cos(yaw), sy = Math.sin(yaw);
    const cx = Math.cos(pitch), sx = Math.sin(pitch);
    const raw = traj.map((p) => {
      const x1 = p.x * cy + p.z * sy;
      const z1 = -p.x * sy + p.z * cy;
      const y2 = p.y * cx - z1 * sx;
      return [x1, y2, p.t];
    });
    const xs = raw.map((p) => p[0]);
    const ys = raw.map((p) => p[1]);
    const minx = Math.min(...xs), maxx = Math.max(...xs);
    const miny = Math.min(...ys), maxy = Math.max(...ys);
    const s = 80 / (Math.max(maxx - minx, maxy - miny) || 1);
    const ox = 50 - ((minx + maxx) / 2) * s;
    const oy = 50 - ((miny + maxy) / 2) * s;
    return raw.map((p) => [p[0] * s + ox, p[1] * s + oy, p[2]]);
  });

  function down(e) { dragging = true; last = [e.clientX, e.clientY]; }
  function move(e) {
    if (!dragging) return;
    yaw += (e.clientX - last[0]) * 0.01;
    pitch = Math.max(-1.2, Math.min(1.2, pitch + (e.clientY - last[1]) * 0.01));
    last = [e.clientX, e.clientY];
  }
  function up() { dragging = false; }
</script>

<div>
  {#if projected.length < 2}
    <p class="rounded-xl border-2 border-line p-4 text-sm text-muted">
      Not enough tracked ball points in this report to plot a trajectory.
    </p>
  {:else}
    <div class="grid gap-3 {hideStats ? '' : 'sm:grid-cols-[minmax(0,1fr)_11rem]'}">
      <div
        class="relative h-72 overflow-hidden rounded-[14px] border-2 border-line bg-surface"
        class:cursor-grabbing={dragging} class:cursor-grab={!dragging}
        onpointerdown={down} onpointermove={move} onpointerup={up} onpointerleave={up}
      >
        <svg viewBox="0 0 100 100" class="h-full w-full touch-none">
          <polyline
            points={projected.map((p) => `${p[0]},${p[1]}`).join(" ")}
            fill="none" stroke="#38bdf8" stroke-width="1.2" stroke-linecap="round"
          />
          {#each projected as p, i}
            <circle cx={p[0]} cy={p[1]} r={i === projected.length - 1 ? 1.6 : 0.9}
              fill={i === projected.length - 1 ? "#f97316" : "#38bdf8"} />
          {/each}
        </svg>
      </div>

      {#if !hideStats}
        <div class="text-xs text-muted">
          <div class="font-semibold text-app">{projected.length} tracked points</div>
          {#if stats.x_range != null}<div>x-range {stats.x_range}</div>{/if}
          {#if stats.y_range != null}<div>y-range {stats.y_range}</div>{/if}
          {#if stats.max_speed != null}<div>max speed {stats.max_speed}/s</div>{/if}
          <div class="mt-2">{traj.length ? fmtTime(traj[0].t) + " – " + fmtTime(traj[traj.length - 1].t) : ""}</div>
        </div>
      {/if}
    </div>
    {#if !hideControls}
      <button onclick={reset} class="mt-3 rounded-lg border-2 border-line px-2.5 py-1 text-xs font-semibold text-app">Reset view</button>
    {/if}
  {/if}
</div>
