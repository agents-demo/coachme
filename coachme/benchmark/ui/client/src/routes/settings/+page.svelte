<script>
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { getHealth, getMe, logout } from "$lib/api";
  import { applyTheme, isDark, themeMode } from "$lib/theme";

  let user = $state(null);
  let loggingOut = $state(false);

  onMount(async () => {
    const health = await getHealth();
    if (health.auth_enabled) user = (await getMe()).user;
  });

  async function signOut() {
    loggingOut = true;
    try {
      await logout();
      await goto("/login");
    } finally {
      loggingOut = false;
    }
  }

  const options = [
    ["system", "System"],
    ["light", "Light"],
    ["dark", "Dark"],
  ];
</script>

<div style="margin-top: 22px">
  <h1 style="margin: 0">Settings</h1>
  <p class="muted" style="margin: 4px 0 0">Local preferences for this benchmark UI.</p>
</div>

<section class="card" style="margin-top: 16px; max-width: 720px">
  <h2>Appearance</h2>
  <p class="muted" style="margin-top: 0">
    Choose a theme or follow your operating system. The choice is stored in this browser only.
  </p>

  <div class="theme-options" role="group" aria-label="Theme">
    {#each options as [value, label]}
      <button
        class="btn"
        class:primary={$themeMode === value}
        aria-pressed={$themeMode === value}
        onclick={() => applyTheme(value)}
      >{label}</button>
    {/each}
  </div>

  <p class="muted small" style="margin-bottom: 0; margin-top: 14px">
    {#if $themeMode === "system"}
      Following the system theme right now ({$isDark ? "dark" : "light"}).
    {:else}
      Explicit {$themeMode} theme selected.
    {/if}
  </p>
</section>

{#if user}
  <section class="card" style="margin-top: 16px; max-width: 720px">
    <h2>Account</h2>
    <p class="muted" style="margin-top: 0">
      Signed in as <strong>{user.display_name || user.username}</strong>
      ({user.role}, tenant {user.tenant}).
    </p>
    <button class="btn" onclick={signOut} disabled={loggingOut}>{loggingOut ? "Signing out?" : "Sign out"}</button>
  </section>
{/if}
