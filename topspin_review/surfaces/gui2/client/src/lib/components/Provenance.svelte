<script>
  // A clean, human-readable provenance block: a plain sentence about how the
  // thing was made, plus badges (on-device / step) and an optional "details"
  // toggle for the raw producer/file. Expects an item from lib/outputs.js.
  let { item } = $props();
  let open = $state(false);
</script>

<div class="mt-2">
  <p class="text-xs text-muted">{item.how}</p>
  <div class="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1">
    {#if !item.local}
      <span class="inline-flex items-center gap-1 rounded-full border-2 border-accent2/40 bg-accent2/5 px-2 py-0.5 text-[11px] font-semibold text-accent2">
        ✨ Uses the AI model
      </span>
    {/if}
    <span class="rounded-full border-2 border-line px-2 py-0.5 text-[11px] font-semibold text-muted">{item.stepLabel}</span>
    <button
      onclick={() => (open = !open)}
      class="text-[11px] font-semibold text-muted underline decoration-dotted underline-offset-2 hover:text-app"
      title="Show the technical detail (for developers)"
    >{open ? "hide details" : "details"}</button>
  </div>
  {#if open}
    <div class="mt-1.5 space-y-1 rounded-lg border-2 border-line bg-surface/40 px-2.5 py-1.5 text-[11px] text-muted">
      <div><span class="font-semibold text-app">Method:</span> {item.method}</div>
      <div><span class="font-semibold text-app">Source:</span> <span class="font-mono">{item.detail}</span></div>
      {#if item.engine}
        <div><span class="font-semibold text-app">Engine:</span> <span class="font-mono">{item.engine}</span> (third-party, bundled locally)</div>
      {/if}
    </div>
  {/if}
</div>
