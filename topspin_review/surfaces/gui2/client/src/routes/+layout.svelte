<script>
  import "../app.css";
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { base } from "$app/paths";
  let { children } = $props();
  const tabs = [
    { href: `${base}/`, label: "Sessions" },
  ];
  const here = (href) =>
    href === `${base}/` ? $page.url.pathname === `${base}/` : $page.url.pathname.startsWith(href);

  let theme = $state("dark");
  function apply() {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("topspin.theme", theme);
    } catch {}
  }
  function toggle() {
    theme = theme === "dark" ? "light" : "dark";
    apply();
  }
  onMount(() => {
    const saved = localStorage.getItem("topspin.theme");
    theme = saved || (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    apply();
  });
</script>

<div class="min-h-screen bg-ink text-app">
  <header class="sticky top-0 z-30 h-14 border-b-2 border-line bg-ink/85 backdrop-blur">
    <div class="mx-auto flex h-full max-w-5xl items-center gap-4 px-4">
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
        <a
          href={`${base}/?new=1`}
          class="rounded-full px-4 py-1.5 text-sm font-semibold text-muted transition"
        >＋ New analysis</a>
        <button
          onclick={toggle}
          title="Toggle theme"
          class="ml-1 grid h-9 w-9 place-items-center rounded-full border-2 border-line text-sm"
        >{theme === "dark" ? "☀️" : "🌙"}</button>
      </nav>
    </div>
  </header>
  <main class="mx-auto max-w-5xl px-4 pb-24 pt-6">
    {@render children()}
  </main>
</div>
