<script>
  import "../app.css";
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { base } from "$app/paths";
  import { onNavigate } from "$app/navigation";
  import { sportMode } from "$lib/stores";

  let { children } = $props();
  const tabs = [
    { href: `${base}/`, label: "Sessions" },
  ];
  const here = (href) =>
    href === `${base}/` ? $page.url.pathname === `${base}/` : $page.url.pathname.startsWith(href);

  let theme = $state("dark");

  function applyTheme() {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("topspin.theme", theme); } catch {}
  }
  function toggleTheme() {
    theme = theme === "dark" ? "light" : "dark";
    applyTheme();
  }

  function toggleSport() {
    $sportMode = !$sportMode;
    if ($sportMode) {
      document.documentElement.dataset.sport = "";
    } else {
      delete document.documentElement.dataset.sport;
    }
    try { localStorage.setItem("topspin.sport", String($sportMode)); } catch {}
  }

  onMount(() => {
    const savedTheme = localStorage.getItem("topspin.theme");
    theme = savedTheme || (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    applyTheme();

    const savedSport = localStorage.getItem("topspin.sport") === "true";
    $sportMode = savedSport;
    if (savedSport) document.documentElement.dataset.sport = "";
  });

  // View Transitions API — seamless fade+slide between sessions list and result.
  onNavigate((navigation) => {
    if (!document.startViewTransition) return;
    return new Promise((resolve) => {
      document.startViewTransition(async () => {
        resolve();
        await navigation.complete;
      });
    });
  });
</script>

<div class="min-h-screen bg-ink text-app">
  <header class="sticky top-0 z-30 h-14 border-b-2 border-line bg-ink/85 backdrop-blur">
    <div class="mx-auto flex h-full max-w-5xl items-center gap-2 px-4">
      <a href={`${base}/`} class="flex items-center gap-2 font-display text-lg font-bold">
        <span class="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-accent to-accent2 text-sm text-white">🏓</span>
        Topspin Review
      </a>
      <nav class="ml-auto flex items-center gap-1">
        {#each tabs as t}
          <a
            href={t.href}
            class="rounded-full px-4 py-1.5 text-sm font-semibold transition"
            class:bg-surface={here(t.href)}
            class:text-app={here(t.href)}
            class:text-muted={!here(t.href)}
          >{t.label}</a>
        {/each}

        <!-- Primary CTA — bordered pill so it reads as an action, not a nav link. -->
        <a
          href={`${base}/?new=1`}
          class="rounded-full border-2 border-accent px-4 py-1.5 text-sm font-semibold text-accent transition hover:bg-accent hover:text-white"
        >＋ New</a>

        <!-- Sport mode toggle -->
        <button
          onclick={toggleSport}
          title={$sportMode ? "Sport mode on · click to switch off" : "Switch to sport mode (orange palette + grid)"}
          class="grid h-9 w-9 place-items-center rounded-full border-2 text-sm transition"
          class:border-accent={$sportMode}
          class:bg-accent={$sportMode}
          class:text-white={$sportMode}
          class:border-line={!$sportMode}
          class:text-muted={!$sportMode}
        >🏅</button>

        <!-- Theme toggle -->
        <button
          onclick={toggleTheme}
          title="Toggle light / dark"
          class="grid h-9 w-9 place-items-center rounded-full border-2 border-line text-sm text-muted transition hover:border-accent hover:text-app"
        >{theme === "dark" ? "☀️" : "🌙"}</button>
      </nav>
    </div>
  </header>
  <main class="mx-auto max-w-5xl px-4 pb-24 pt-6">
    {@render children()}
  </main>
</div>
