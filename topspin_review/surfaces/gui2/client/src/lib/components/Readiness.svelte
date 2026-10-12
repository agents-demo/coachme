<script>
  import { onMount } from "svelte";
  import { readiness } from "$lib/api";

  let checks = $state([]);

  onMount(async () => {
    try {
      checks = (await readiness()).checks || [];
    } catch {
      checks = [];
    }
  });
</script>

{#if checks.length}
  <div class="mt-4 flex flex-wrap items-center gap-2 text-[11px]">
    <span class="uppercase tracking-wide text-muted">Environment</span>
    {#each checks as c}
      <span
        class="inline-flex items-center gap-1 rounded-full border border-line px-2 py-0.5 {c.ok ? "text-muted" : "text-warn"}"
        title={c.detail}
      >
        <span class={c.ok ? "text-good" : "text-warn"}>{c.ok ? "✓" : "○"}</span>{c.name}
      </span>
    {/each}
  </div>
{/if}
