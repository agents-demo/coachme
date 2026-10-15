<script>
  import { base } from "$app/paths";
  import { deleteReport, thumb } from "$lib/api";

  let { report, ondeleted } = $props();

  const poster = $derived(thumb(report));
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

<div class="group card relative overflow-hidden p-0 transition hover:-translate-y-0.5 hover:border-accent2">
  <button
    onclick={del}
    disabled={busy}
    title="Delete this session"
    aria-label="Delete this session"
    class="absolute right-2 top-2 z-10 grid h-7 w-7 place-items-center rounded-full bg-ink/70 text-xs text-muted backdrop-blur transition hover:bg-bad/20 hover:text-bad disabled:opacity-50"
  >✕</button>

  <a href={`${base}/result?stem=${encodeURIComponent(report.stem)}`} class="block">
    <div class="relative aspect-video overflow-hidden bg-gradient-to-br from-accent/25 to-accent2/25">
      {#if poster}
        <img
          src={poster}
          alt=""
          loading="lazy"
          class="h-full w-full object-cover opacity-90 transition duration-300 group-hover:scale-[1.03] group-hover:opacity-100"
        />
      {:else}
        <div class="grid h-full w-full place-items-center text-5xl">🏓</div>
      {/if}
      {#if report.is_photo}
        <span class="absolute bottom-2 right-2 rounded-full bg-ink/75 px-2 py-0.5 text-[10px] uppercase tracking-wide text-muted backdrop-blur">photo</span>
      {/if}
    </div>

    <div class="p-3">
      <div class="flex items-center gap-2">
        <span class="truncate font-display font-bold">{report.stem}</span>
        <span class="ml-auto shrink-0 text-xs text-muted">{report.sport} · {report.date}</span>
      </div>
      <p class="mt-1 line-clamp-2 text-xs text-muted">{report.summary || report.focus || "—"}</p>
      <div class="mt-2 flex items-center gap-2 text-xs text-muted">
        <span class="rounded-full border border-line px-2 py-0.5">{report.issue_count} issue{report.issue_count === 1 ? "" : "s"}</span>
        {#if report.has_pose}<span class="rounded-full border border-line px-2 py-0.5" title="A body-pose skeleton overlay is available">pose</span>{/if}
        {#if report.focus}<span class="truncate">{report.focus}</span>{/if}
      </div>
    </div>
  </a>
</div>
