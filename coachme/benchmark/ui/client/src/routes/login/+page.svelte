<script>
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { getHealth, login } from "$lib/api";

  let username = $state("");
  let password = $state("");
  let busy = $state(false);
  let error = $state("");

  async function submit() {
    busy = true;
    error = "";
    try {
      await login(username, password);
      await goto("/");
    } catch (err) {
      error = err.message;
    } finally {
      busy = false;
    }
  }

  onMount(async () => {
    try {
      const health = await getHealth();
      if (!health.auth_enabled) await goto("/");
    } catch {
      /* stay on login */
    }
  });
</script>

<div style="max-width: 420px; margin: 8vh auto 0">
  <section class="card">
    <div class="row">
      <span class="mark">CM</span>
      <div>
        <h1 style="margin: 0; font-size: 24px">Benchmark login</h1>
        <p class="muted small" style="margin: 2px 0 0">Local account required for remote access.</p>
      </div>
    </div>

    {#if error}<div class="error" style="margin-top: 14px">{error}</div>{/if}

    <form onsubmit={(event) => { event.preventDefault(); submit(); }} style="margin-top: 16px">
      <div class="field">
        <label for="username">Username</label>
        <input id="username" bind:value={username} autocomplete="username" required />
      </div>
      <div class="field">
        <label for="password">Password</label>
        <input id="password" type="password" bind:value={password} autocomplete="current-password" required />
      </div>
      <button class="btn primary" type="submit" disabled={busy} style="width: 100%; justify-content: center">
        {busy ? "Signing in?" : "Sign in"}
      </button>
    </form>
  </section>
</div>
