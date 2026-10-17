<script>
  import { tr } from "$lib/appearance";
  // A clean, human-readable provenance block: a plain sentence about how the
  // thing was made, with an inline "details" toggle for the technical method,
  // source and engine. Expects an item from lib/outputs.js.
  let { item, hideBadge = false } = $props();
  let open = $state(false);
</script>

<p class="mt-1 text-xs text-muted">
  {#if !item.local && !hideBadge}
    <span class="mr-1 inline-flex items-center gap-1 rounded-full border-2 border-accent2/40 bg-accent2/5 px-1.5 py-0.5 align-middle text-[10px] font-semibold text-accent2">{tr("AI agent")}</span>
  {/if}
  {tr(item.how)}
  {#if item.method}
    <button
      onclick={() => (open = !open)}
      class="ml-1 font-semibold text-muted underline decoration-dotted underline-offset-2 hover:text-app"
      title="Technical detail (for developers)"
    >{open ? tr("hide details") : tr("details")}</button>
  {/if}
</p>
{#if open && item.method}
  <div class="mt-1.5 space-y-1 rounded-lg border-2 border-line bg-surface/40 px-2.5 py-1.5 text-[11px] text-muted">
    <div><span class="font-semibold text-app">{tr("Method:")}</span> {tr(item.method)}</div>
    <div><span class="font-semibold text-app">{tr("Source:")}</span> <span class="font-mono">{item.detail}</span></div>
    {#if item.engine}
      <div><span class="font-semibold text-app">{tr("Engine:")}</span> <span class="font-mono">{item.engine}</span> {tr("(third-party, bundled locally)")}</div>
    {/if}
  </div>
{/if}
