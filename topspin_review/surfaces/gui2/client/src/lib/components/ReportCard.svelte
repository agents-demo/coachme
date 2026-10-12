<script>
  import { base } from "$app/paths";
  import { scoreTone } from "$lib/format";

  let { report } = $props();
</script>

<a
  href={`${base}/result?stem=${encodeURIComponent(report.stem)}`}
  class="card flex flex-col gap-1 p-4 transition hover:border-accent2"
>
  <div class="flex items-center gap-2">
    <span class="font-display text-base font-bold">{report.stem}</span>
    <span class="text-xs text-muted">{report.sport} · {report.date}</span>
    <span
      class="ml-auto text-xs text-muted"
      title="Report quality: evidence coverage, confidence, and no unsupported spin/speed claims — not a performance score."
    >quality <span class="font-semibold {scoreTone(report.score)}">{report.score}</span></span>
  </div>
  <p class="line-clamp-2 text-sm text-muted">{report.summary || report.focus || "—"}</p>
  <div class="mt-1 flex items-center gap-3 text-xs text-muted">
    <span>{report.issue_count} issue{report.issue_count === 1 ? "" : "s"}</span>
    {#if report.is_photo}<span>· photo</span>{/if}
    {#if !report.has_source}<span>· media missing</span>{/if}
  </div>
</a>
