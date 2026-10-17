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

<div class="group card relative overflow-hidden p-0 transition hover:-translate-y-0.5 hover:border-accent2" style="view-transition-name: {vtName}">
  <button
    onclick={del}
    disabled={busy}
    title="Delete this session"
    aria-label="Delete this session"
    class="absolute right-2 top-2 z-10 grid h-7 w-7 place-items-center rounded-full bg-ink/70 text-xs text-muted backdrop-blur opacity-0 group-hover:opacity-100 transition-opacity hover:bg-bad/20 hover:text-bad disabled:opacity-30"
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
        <span class="absolute bottom-2 right-2 rounded-full bg-ink/75 px-2 py-0.5 text-[10px] uppercase tracking-wide text-muted backdrop-blur">{tr("photo")}</span>
      {/if}
    </div>

    <div class="p-3">
      <div class="flex items-center gap-2">
        <span class="truncate font-display font-bold">{report.name || report.stem}</span>
        <span class="ml-auto shrink-0 text-xs text-muted">{report.sport} · {report.date}</span>
      </div>
      {#if report.name}<p class="text-[10px] text-muted">{report.stem}</p>{/if}
      <p class="mt-1 line-clamp-2 text-xs text-muted">{report.summary || report.focus || "—"}</p>
      <div class="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-muted">
        <span class="rounded-full border border-line px-2 py-0.5">{report.issue_count} {tr("issue")}{report.issue_count === 1 ? "" : "s"}</span>
        {#if report.has_pose}<span class="rounded-full border border-line px-2 py-0.5" title="A body-pose skeleton overlay is available">{tr("pose")}</span>{/if}
        {#each (report.tags || []) as tag}
          <span class="rounded-full border border-accent/40 bg-accent/8 px-2 py-0.5 text-accent">{tag}</span>
        {/each}
      </div>
    </div>
  </a>
</div>
