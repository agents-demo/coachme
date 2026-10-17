<script>
  import { onMount } from "svelte";
  import { readiness, getProfile, saveProfile, getConfig } from "$lib/api";
  import { theme, palette, setTheme, setPalette } from "$lib/appearance";

  const tabs = [
    { value: "api", label: "API" },
    { value: "profile", label: "Profile" },
    { value: "analysis", label: "Analysis" },
    { value: "style", label: "Style" },
  ];

  const themes = [
    { value: "system", label: "System", hint: "Follow the device" },
    { value: "light", label: "Light", hint: "Always light" },
    { value: "dark", label: "Dark", hint: "Always dark" },
  ];

  const palettes = [
    {
      value: "sport",
      label: "Sport",
      hint: "Orange accent with an image-forward grid",
      from: "#f97316",
      to: "#fb923c",
    },
    {
      value: "indigo",
      label: "Indigo",
      hint: "Classic indigo accent with a landscape grid",
      from: "#4f46e5",
      to: "#818cf8",
    },
  ];

  const levelOptions = ["beginner", "intermediate", "advanced"];
  const handOptions = ["right", "left"];
  const goalOptions = ["improve", "consistency", "power", "footwork", "match play"];
  const sportSuggestions = ["table tennis", "tennis", "badminton", "squash", "padel"];

  let tab = $state("api");
  let showChecks = $state(false);
  let checks = $state([]);
  let config = $state(null);
  let configError = $state("");
  let statusError = $state("");
  let saveState = $state("");
  let profile = $state({
    sport: "table tennis",
    level: "intermediate",
    hand: "right",
    goal: "improve",
  });

  let saveTimer;
  const missing = $derived(checks.filter((c) => !c.ok).length);

  async function loadStatus() {
    statusError = "";
    try {
      checks = (await readiness()).checks || [];
    } catch (e) {
      statusError = String(e?.message || e);
    }
  }

  onMount(async () => {
    loadStatus();
    try {
      config = await getConfig();
    } catch (e) {
      configError = String(e?.message || e);
    }
    try {
      const saved = await getProfile();
      profile = {
        sport: saved.sport || "table tennis",
        level: saved.level || "intermediate",
        hand: saved.dominant_hand || saved.hand || "right",
        goal: saved.goal || "improve",
      };
    } catch {}
  });

  function updateProfile(patch) {
    profile = { ...profile, ...patch };
    saveState = "Saving…";
    clearTimeout(saveTimer);
    saveTimer = setTimeout(async () => {
      try {
        await saveProfile({
          sport: profile.sport,
          level: profile.level,
          dominant_hand: profile.hand,
          goal: profile.goal,
        });
        saveState = "Saved";
      } catch {
        saveState = "Save failed";
      }
    }, 500);
  }

  function withCurrent(options, value) {
    return options.includes(value) ? options : [...options, value];
  }

  function onOff(value) {
    return value == null ? "—" : value ? "On" : "Off";
  }
</script>

<section class="flex flex-wrap items-start justify-between gap-3">
  <div>
    <h1 class="font-display text-3xl font-extrabold">Settings</h1>
    <p class="mt-1 max-w-2xl text-sm text-muted">
      Profile changes apply to new analyses. Endpoint and analysis settings live in the server
      environment; appearance is saved on this device.
    </p>
  </div>
  <button
    onclick={() => (showChecks = true)}
    title="Open environment checks"
    class="mt-1 inline-flex shrink-0 items-center gap-1.5 rounded-full border border-line bg-surface/50 px-3 py-1.5 text-xs font-semibold text-muted transition hover:border-accent hover:text-app"
  >
    <span class="h-2 w-2 rounded-full {checks.length && missing ? 'bg-warn' : 'bg-good'}"></span>
    {checks.length
      ? missing
        ? `${missing} issue${missing === 1 ? "" : "s"}`
        : "Environment ready"
      : "Environment"}
    <span aria-hidden="true" class="text-sm leading-none">›</span>
  </button>
</section>

{#if showChecks}
  <div class="fixed inset-0 z-50 grid place-items-center p-4" role="dialog" aria-modal="true" aria-label="Environment readiness">
    <button class="absolute inset-0 bg-black/50 backdrop-blur-md" aria-label="Close" onclick={() => (showChecks = false)}></button>
    <div class="relative w-full max-w-md rounded-2xl border-2 border-line bg-surface/85 p-5 shadow-2xl backdrop-blur-xl">
      <div class="flex items-start justify-between gap-3">
        <div>
          <h2 class="font-display text-lg font-bold">Environment</h2>
          <p class="mt-0.5 text-xs text-muted">API, models, pose, PDF and sample assets.</p>
        </div>
        <button
          onclick={() => (showChecks = false)}
          class="grid h-8 w-8 shrink-0 place-items-center rounded-full border-2 border-line text-muted transition hover:border-accent hover:text-app"
          aria-label="Close"
        >✕</button>
      </div>

      <div class="mt-3 flex items-center justify-between gap-3">
        <span class="text-xs font-semibold {missing ? 'text-warn' : 'text-good'}">
          {checks.length
            ? missing
              ? `${missing} of ${checks.length} need attention`
              : `All ${checks.length} checks passed`
            : "Checking…"}
        </span>
        <button onclick={loadStatus} class="text-xs font-semibold text-muted transition hover:text-app">Refresh</button>
      </div>

      {#if statusError}
        <p class="mt-3 text-sm text-bad">{statusError}</p>
      {:else if !checks.length}
        <p class="mt-3 text-sm text-muted">No readiness checks reported.</p>
      {:else}
        <ul class="mt-3 max-h-[55vh] space-y-2 overflow-y-auto pr-1">
          {#each checks as c}
            <li class="flex items-start gap-3 rounded-xl border border-line bg-surface px-3.5 py-3">
              <span class="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full text-[11px] font-bold {c.ok ? 'bg-good/15 text-good' : 'bg-warn/15 text-warn'}">
                {c.ok ? "✓" : "!"}
              </span>
              <span class="min-w-0">
                <span class="text-sm font-medium">{c.name}</span>
                {#if c.detail}<span class="mt-0.5 block text-xs text-muted">{c.detail}</span>{/if}
              </span>
            </li>
          {/each}
        </ul>
      {/if}
    </div>
  </div>
{/if}

<div class="mt-5 flex gap-1.5 overflow-x-auto pb-1" role="tablist" aria-label="Settings sections">
  {#each tabs as t}
    <button
      role="tab"
      aria-selected={tab === t.value}
      onclick={() => (tab = t.value)}
      class="shrink-0 rounded-full px-4 py-2 text-sm font-semibold transition {tab === t.value
        ? 'bg-accent text-white'
        : 'bg-surface text-muted hover:text-app'}"
    >{t.label}</button>
  {/each}
</div>

{#if tab === "api"}
  <section class="card mt-4 p-5">
    <h2 class="font-display text-lg font-bold">Model API</h2>
    <p class="mt-1 text-xs text-muted">
      Read-only. Set in the server environment (<code>.env</code>); the key is never sent to the browser.
    </p>
    {#if configError}
      <p class="mt-3 text-sm text-bad">{configError}</p>
    {:else if config}
      <dl class="mt-4 divide-y divide-line">
        {#each [
          ["API base", config.api_base || "—"],
          ["Text model", config.text_model || "—"],
          ["Vision model", config.vision_model || "—"],
        ] as [label, value]}
          <div class="flex items-start justify-between gap-4 py-2.5">
            <dt class="text-sm text-muted">{label}</dt>
            <dd class="text-right text-sm font-medium">{value}</dd>
          </div>
        {/each}
      </dl>
    {:else}
      <p class="mt-3 text-sm text-muted">Loading…</p>
    {/if}
  </section>

{/if}

{#if tab === "profile"}
  <section class="card mt-4 p-5">
    <div class="flex items-baseline justify-between gap-3">
      <h2 class="font-display text-lg font-bold">Player profile</h2>
      {#if saveState}
        <span class="text-xs {saveState === 'Save failed' ? 'text-bad' : 'text-muted'}">{saveState}</span>
      {/if}
    </div>
    <p class="mt-1 text-xs text-muted">Feeds the prompts and the scoring rubric.</p>

    <label class="mt-4 block text-xs font-semibold uppercase tracking-wide text-muted" for="sport">Sport</label>
    <input
      id="sport"
      list="sport-suggestions"
      value={profile.sport}
      oninput={(e) => updateProfile({ sport: e.currentTarget.value })}
      class="mt-1.5 w-full rounded-xl border-2 border-line bg-surface px-3 py-2 text-sm transition focus:border-accent focus:outline-none"
    />
    <datalist id="sport-suggestions">
      {#each sportSuggestions as s}<option value={s}></option>{/each}
    </datalist>

    {#each [
      { key: "level", label: "Level", options: levelOptions },
      { key: "hand", label: "Dominant hand", options: handOptions },
      { key: "goal", label: "Goal", options: goalOptions },
    ] as field}
      <p class="mt-4 text-xs font-semibold uppercase tracking-wide text-muted">{field.label}</p>
      <div class="mt-2 flex flex-wrap gap-2">
        {#each withCurrent(field.options, profile[field.key]) as option}
          <button
            onclick={() => updateProfile({ [field.key]: option })}
            aria-pressed={profile[field.key] === option}
            class="rounded-full border-2 px-3.5 py-1.5 text-sm font-semibold capitalize transition {profile[field.key] === option
              ? 'border-accent bg-accent/10 text-accent'
              : 'border-line text-muted hover:text-app'}"
          >{option}</button>
        {/each}
      </div>
    {/each}
  </section>
{/if}

{#if tab === "analysis"}
  <section class="card mt-4 p-5">
    <h2 class="font-display text-lg font-bold">Analysis</h2>
    <p class="mt-1 text-xs text-muted">
      Read-only. These are set in the server environment (<code>.env</code>) and apply to new analyses.
    </p>
    {#if configError}
      <p class="mt-3 text-sm text-bad">{configError}</p>
    {:else if config}
      <dl class="mt-4 divide-y divide-line">
        {#each [
          ["Frame sampling", config.max_frames == null ? "—" : `${config.max_frames} frames`],
          ["Frame width", config.max_width == null ? "—" : `${config.max_width} px`],
          ["Zoom frames", config.zoom_frames == null ? "—" : `${config.zoom_frames} per window`],
          ["Zoom windows", config.max_windows == null ? "—" : `${config.max_windows} windows`],
          ["Agentic pass", onOff(config.agentic)],
          ["Verify reports", onOff(config.verify_reports)],
          ["Demo fallback", onOff(config.demo_fallback)],
        ] as [label, value]}
          <div class="flex items-start justify-between gap-4 py-2.5">
            <dt class="text-sm text-muted">{label}</dt>
            <dd class="text-right text-sm font-medium">{value}</dd>
          </div>
        {/each}
      </dl>
    {:else}
      <p class="mt-3 text-sm text-muted">Loading…</p>
    {/if}
  </section>
{/if}

{#if tab === "style"}
  <section class="card mt-4 p-5">
    <div class="flex items-baseline justify-between gap-3">
      <h2 class="font-display text-lg font-bold">Theme</h2>
      <span class="text-[11px] uppercase tracking-wide text-muted">System / Light / Dark</span>
    </div>
    <div class="mt-3 grid grid-cols-3 gap-2">
      {#each themes as t}
        <button
          onclick={() => setTheme(t.value)}
          aria-pressed={$theme === t.value}
          class="rounded-xl border-2 px-3 py-3 text-left transition {$theme === t.value
            ? 'border-accent bg-accent/10 text-accent'
            : 'border-line text-muted hover:border-accent/60 hover:text-app'}"
        >
          <span class="block text-sm font-semibold">{t.label}</span>
          <span class="mt-0.5 block text-[11px] text-muted">{t.hint}</span>
        </button>
      {/each}
    </div>
  </section>

  <section class="card mt-4 p-5">
    <div class="flex items-baseline justify-between gap-3">
      <h2 class="font-display text-lg font-bold">Palette</h2>
      <span class="text-[11px] uppercase tracking-wide text-muted">Accent + session layout</span>
    </div>
    <div class="mt-3 grid grid-cols-2 gap-3">
      {#each palettes as p}
        <button
          onclick={() => setPalette(p.value)}
          aria-pressed={$palette === p.value}
          class="rounded-2xl border-2 p-2.5 text-left transition {$palette === p.value
            ? 'border-accent bg-accent/10'
            : 'border-line hover:border-accent/60'}"
        >
          <span class="block h-16 rounded-xl" style={`background: linear-gradient(135deg, ${p.from}, ${p.to})`}></span>
          <span class="mt-2 block text-sm font-semibold {$palette === p.value ? 'text-accent' : ''}">{p.label}</span>
          <span class="mt-0.5 block text-[11px] leading-snug text-muted">{p.hint}</span>
        </button>
      {/each}
    </div>
    <p class="mt-3 text-xs text-muted">Dynamic color (Material You) is available in the Android app only.</p>
  </section>
{/if}
