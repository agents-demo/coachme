<script>
  import { base } from "$app/paths";
  import { deleteReport } from "$lib/api";
  import { scoreTone } from "$lib/format";

  let { report, ondeleted } = $props();
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

<div class="card relative p-4 transition hover:border-accent2">
  <button
    onclick={del}
    disabled={busy}
    title="Delete this session"
    aria-label="Delete this session"
    class="absolute right-2 top-2 grid h-7 w-7 place-items-center rounded-full border-2 border-line text-xs text-muted transition hover:border-bad hover:text-bad disabled:opacity-50"
  >✕</button>

  <a href={`${base}/result?stem=${encodeURIComponent(report.stem)}`} class="block">
    <div class="flex items-center gap-2 pr-8">
      <span class="font-display text-base font-bold">{report.stem}</span>
      <span class="text-xs text-muted">{report.sport} · {report.date}</span>
      <span
        class="ml-auto text-xs text-muted"
        title="Report quality: evidence coverage, confidence, and no unsupported spin/speed claims — not a performance score."
      >quality <span class="font-semibold {scoreTone(report.score)}">{report.score}</span></span>
    </div>
    <p class="mt-1 line-clamp-2 text-sm text-muted">{report.summary || report.focus || "—"}</p>
    <div class="mt-1 flex items-center gap-3 text-xs text-muted">
      <span>{report.issue_count} issue{report.issue_count === 1 ? "" : "s"}</span>
      {#if report.is_photo}<span>· photo</span>{/if}
      {#if !report.has_source}<span>· media missing</span>{/if}
    </div>
  </a>
</div>
