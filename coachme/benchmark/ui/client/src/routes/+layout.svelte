<script>
  import { onMount } from "svelte";
  import "../app.css";
  import { page } from "$app/stores";
  import { initTheme } from "$lib/theme";

  let { children } = $props();

  onMount(() => initTheme());
</script>

<header class="top">
  <div class="inner">
    <a class="brand" href="/">
      <span class="mark">CM</span>
      <span>Benchmark</span>
    </a>
    {#if $page.url.pathname !== "/login"}
    <nav>
      <a href="/" class:active={$page.url.pathname === "/"}>Runs</a>
      <a href="/help" class:active={$page.url.pathname === "/help"}>Help</a>
      <a
        href="/settings"
        class="btn settings-link"
        class:active={$page.url.pathname === "/settings"}
        aria-label="Settings"
        title="Settings"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.3 4.3c.4-1.8 2.9-1.8 3.4 0a1.7 1.7 0 0 0 2.6 1.1c1.5-.9 3.3.9 2.4 2.4a1.7 1.7 0 0 0 1 2.6c1.8.4 1.8 2.9 0 3.4a1.7 1.7 0 0 0-1 2.6c.9 1.5-.9 3.3-2.4 2.4a1.7 1.7 0 0 0-2.6 1c-.4 1.8-2.9 1.8-3.4 0a1.7 1.7 0 0 0-2.6-1c-1.5.9-3.3-.9-2.4-2.4a1.7 1.7 0 0 0-1-2.6c-1.8-.4-1.8-2.9 0-3.4a1.7 1.7 0 0 0 1-2.6c-.9-1.5.9-3.3 2.4-2.4a1.7 1.7 0 0 0 2.6-1Z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
        </svg>
      </a>
    </nav>
    {/if}
  </div>
</header>

<main class="shell">
  {@render children()}
</main>
