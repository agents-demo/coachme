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
  <div class="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
    <span class="font-semibold uppercase tracking-wide text-muted">Readiness</span>
    {#each checks as c}
      <span class="inline-flex items-center gap-1 {c.ok ? "text-app" : "text-muted"}">
        <span class={c.ok ? "text-good" : "text-warn"}>{c.ok ? "✓" : "○"}</span>
        {c.name}
        <span class="text-muted">· {c.detail}</span>
      </span>
    {/each}
  </div>
{/if}
