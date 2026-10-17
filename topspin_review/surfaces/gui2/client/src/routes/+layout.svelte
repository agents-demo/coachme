<script>
  import { tr } from "$lib/appearance";
  import "../app.css";
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { base } from "$app/paths";
  import { onNavigate } from "$app/navigation";
  import { initAppearance } from "$lib/appearance";

  let { children } = $props();
  const tabs = [
    { href: `${base}/`, label: "Sessions" },
    { href: `${base}/progress`, label: "Progress" },
  ];
  const here = (href) =>
    href === `${base}/` ? $page.url.pathname === `${base}/` : $page.url.pathname.startsWith(href);

  onMount(() => {
    initAppearance();
  });

  $effect(() => {
    if (typeof document !== "undefined") document.title = tr("Topspin Review");
  });

  // View Transitions API: seamless fade+slide between sessions list and result.
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
      <a href={`${base}/`} class="flex shrink-0 items-center gap-2 font-display text-lg font-bold">
        <span class="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-accent to-accent2 text-[11px] font-extrabold text-white">{tr("TR")}</span>
        <span class="hidden sm:inline">{tr("Topspin Review")}</span>
      </a>
      <nav class="ml-auto flex items-center gap-1">
        {#each tabs as t}
          <a
            href={t.href}
            class="rounded-full px-3 py-1.5 text-sm font-semibold transition sm:px-4"
            class:bg-surface={here(t.href)}
            class:text-app={here(t.href)}
            class:text-muted={!here(t.href)}
          >{tr(t.label)}</a>
        {/each}

        <a
          href={`${base}/settings`}
          aria-label={tr("Settings")}
          title={tr("Settings")}
          class="grid h-9 w-9 shrink-0 place-items-center rounded-full border-2 border-line text-muted transition hover:border-accent hover:text-app"
          class:border-accent={here(`${base}/settings`)}
          class:bg-accent={here(`${base}/settings`)}
          class:text-white={here(`${base}/settings`)}
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="h-4 w-4" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 0 0-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 0 0-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 0 0-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 0 0-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 0 0 1.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065Z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
          </svg>
        </a>
      </nav>
    </div>
  </header>
  <main class="mx-auto max-w-5xl px-4 pb-24 pt-6">
    {@render children()}
  </main>
</div>
