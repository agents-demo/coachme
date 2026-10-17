<script>
  import { tr } from "$lib/appearance";
  import { base } from "$app/paths";
  import { deleteReport, thumb } from "$lib/api";

  let { report, ondeleted } = $props();
  const poster = $derived(thumb(report));
  const vtName = $derived('r-' + (report.stem || '').replace(/[^a-zA-Z0-9]/g, '-'));
  let busy = $state(false);

  async function del(e) {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm(`Delete session "${report.stem}"? This removes its report, artifacts and exports.`)) return;
    busy = true;
    try {
      await deleteReport(report.stem);
      ondeleted?.();
    } catch {
      /* ignore */
    } finally {
      busy = false;
    }
  }
</script>

<!--
  Sport-mode card: full-bleed thumbnail, gradient scrim at bottom,
  session title + meta overlaid on the image. Issue count badge top-left.
  Delete button reveals on hover (top-right).
-->
<div class="group relative overflow-hidden rounded-2xl" style="aspect-ratio: 3/4; view-transition-name: {vtName}">
  <a href={`${base}/result?stem=${encodeURIComponent(report.stem)}`} class="block h-full">
    {#if poster}
      <img
        src={poster}
        alt=""
        loading="lazy"
        class="h-full w-full object-cover transition duration-300 group-hover:scale-[1.04]"
      />
    {:else}
      <div class="h-full w-full bg-gradient-to-br from-accent/25 to-accent2/25 grid place-items-center text-5xl">🏓</div>
    {/if}

    <!-- Gradient scrim -->
    <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent pointer-events-none"></div>

    <!-- Bottom overlay -->
    <div class="absolute bottom-0 left-0 right-0 p-3 pointer-events-none">
      <p class="truncate font-display font-bold text-white text-sm leading-tight">{report.name || report.stem}</p>
      <p class="mt-0.5 text-[11px] text-white/70">{report.sport} · {report.date}</p>
    </div>

    <!-- Issue count badge (top-left) -->
    {#if report.drill_count > 0}
      <span class="absolute top-2 left-2 rounded-full bg-good/90 px-2 py-0.5 text-[10px] font-bold text-white backdrop-blur pointer-events-none">
        ✓ {report.drill_count} {tr("drills")}
      </span>
    {/if}

    {#if report.is_photo}
      <span class="absolute bottom-12 right-2 rounded-full bg-black/60 px-2 py-0.5 text-[10px] uppercase tracking-wide text-white/70 backdrop-blur pointer-events-none">{tr("photo")}</span>
    {/if}
  </a>

  <!-- Delete button — hidden until hover -->
  <button
    onclick={del}
    disabled={busy}
    title="Delete this session"
    aria-label="Delete this session"
    class="absolute right-2 top-2 z-10 grid h-7 w-7 place-items-center rounded-full bg-black/60 text-xs text-white/70 backdrop-blur transition-opacity duration-150 opacity-0 group-hover:opacity-100 hover:bg-bad/80 hover:text-white disabled:opacity-30"
  >✕</button>
</div>
