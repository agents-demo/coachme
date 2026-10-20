<script>
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { createRun, getHealth, getRuns, importRun, validateManifest } from "$lib/api";

  let runs = $state([]);
  let loading = $state(true);
  let error = $state("");
  let search = $state("");
  let health = $state(null);
  let showNew = $state(false);
  let starting = $state(false);
  let validating = $state(false);
  let validation = $state(null);
  let importPath = $state("");
  let importing = $state(false);
  let form = $state({
    manifest_path: "",
    modes: ["standard", "investigator"],
    environment: "local",
    label: "pilot",
    required_clips: 8,
    required_raters: 2,
  });

  const filtered = $derived(
    runs.filter((run) =>
      [run.run_id, run.label, run.environment, run.status]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(search.trim().toLowerCase()),
    ),
  );

  async function load() {
    loading = true;
    error = "";
    try {
      const [runsData, healthData] = await Promise.all([getRuns(), getHealth()]);
      runs = runsData.runs || [];
      health = healthData;
      if (!form.manifest_path) form.manifest_path = `${health.data_root}/manifest.json`;
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  async function checkManifest() {
    validating = true;
    validation = null;
    error = "";
    try {
      validation = await validateManifest(form.manifest_path);
    } catch (err) {
      error = err.message;
    } finally {
      validating = false;
    }
  }

  async function importExisting() {
    if (!importPath.trim()) return;
    importing = true;
    error = "";
    try {
      const result = await importRun(importPath.trim());
      await goto(`/runs/${encodeURIComponent(result.run_id)}`);
    } catch (err) {
      error = err.message;
    } finally {
      importing = false;
    }
  }

  async function startRun() {
    if (!form.modes.length) {
      error = "Select at least one mode.";
      return;
    }
    starting = true;
    error = "";
    try {
      const result = await createRun({ ...form });
      await goto(`/runs/${encodeURIComponent(result.run_id)}`);
    } catch (err) {
      error = err.message;
    } finally {
      starting = false;
    }
  }

  onMount(load);

  function tone(value) {
    if (value === true) return "good";
    if (value === false) return "bad";
    return "warn";
  }

  function when(value) {
    if (!value) return "—";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
  }
</script>

<div class="row" style="justify-content: space-between; margin-top: 22px">
  <div>
    <h1 style="margin: 0">Benchmark runs</h1>
    <p class="muted" style="margin: 4px 0 0">
      Local review of Standard and Investigator outputs, labels and release gates.
    </p>
  </div>
  <div class="row">
    <button class="btn" onclick={load} disabled={loading}>{loading ? "Loading..." : "Refresh"}</button>
    <button class="btn primary" onclick={() => (showNew = !showNew)} disabled={health?.active_run}>
      {showNew ? "Close" : "New run"}
    </button>
  </div>
</div>

{#if error}
  <div class="error" style="margin-top: 16px">{error}</div>
{/if}

{#if health?.active_run}
  <div class="notice" style="margin-top: 14px">
    Run <span class="mono">{health.active_run.run_id}</span> is active. Wait for it to finish or cancel it from its dashboard.
  </div>
{/if}

{#if showNew}
  <section class="card" style="margin-top: 16px">
    <div class="row" style="justify-content: space-between">
      <h2 style="margin: 0">New benchmark run</h2>
      <span class="pill">local execution</span>
    </div>
    <div class="grid two" style="margin-top: 12px">
      <div class="field">
        <label for="manifest">Manifest path</label>
        <input id="manifest" bind:value={form.manifest_path} />
      </div>
      <div class="field">
        <label for="label">Run label</label>
        <input id="label" bind:value={form.label} placeholder="pilot" />
      </div>
    </div>
    <div class="field">
      <span class="label">Modes</span>
      <div class="row">
        {#each ["standard", "guided", "investigator"] as mode}
          <label class="pill" style="cursor: pointer">
            <input type="checkbox" bind:group={form.modes} value={mode} style="width: auto; margin-right: 5px" />
            {mode}
          </label>
        {/each}
      </div>
    </div>
    <div class="grid two">
      <div class="field">
        <label for="environment">Environment</label>
        <select id="environment" bind:value={form.environment}>
          <option value="local">local</option>
          <option value="staging">staging</option>
          <option value="production">production</option>
        </select>
      </div>
      <div class="grid two" style="gap: 10px">
        <div class="field">
          <label for="clips">Required clips</label>
          <input id="clips" type="number" min="1" bind:value={form.required_clips} />
        </div>
        <div class="field">
          <label for="raters">Required raters</label>
          <input id="raters" type="number" min="1" bind:value={form.required_raters} />
        </div>
      </div>
    </div>
    {#if validation}
      <div class="notice" style="margin-bottom: 12px">
        {validation.ok ? `Manifest is valid: ${validation.clips} clip(s).` : validation.problems.join(" | ")}
      </div>
    {/if}
    <div class="row">
      <button class="btn" onclick={checkManifest} disabled={validating}>{validating ? "Checking..." : "Validate manifest"}</button>
      <button class="btn primary" onclick={startRun} disabled={starting || health?.active_run}>{starting ? "Starting..." : "Start run"}</button>
    </div>
    <p class="muted small" style="margin-bottom: 0">
      Analysis runs in a local subprocess with an isolated data directory. Real clips and labels stay outside git.
    </p>
    <div class="row" style="margin-top: 14px; border-top: 1px solid var(--line); padding-top: 12px">
      <input bind:value={importPath} placeholder="Import an existing run directory" style="max-width: 420px" />
      <button class="btn" onclick={importExisting} disabled={!importPath.trim() || importing}>
        {importing ? "Importing..." : "Import run"}
      </button>
    </div>
  </section>
{/if}

<div class="card" style="margin-top: 18px">
  <div class="row" style="justify-content: space-between; margin-bottom: 12px">
    <h2 style="margin: 0">Runs</h2>
    {#if runs.length > 4}
      <input class="search" bind:value={search} placeholder="Filter runs…" />
    {/if}
  </div>

  {#if loading}
    <p class="muted">Loading runs…</p>
  {:else if !runs.length}
    <p class="muted">
      No runs yet. Create one with
      <span class="mono">coachme-benchmark run --manifest benchmark-data/manifest.json</span>.
    </p>
  {:else if !filtered.length}
    <p class="muted">No runs match “{search}”.</p>
  {:else}
    <div style="overflow-x: auto">
      <table class="table">
        <thead>
          <tr>
            <th>Run</th>
            <th>Created</th>
            <th>Environment</th>
            <th>Clips</th>
            <th>Analysis</th>
            <th>Score</th>
            <th>Release</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {#each filtered as run (run.run_id)}
            <tr>
              <td>
                <a href={`/runs/${encodeURIComponent(run.run_id)}`} style="font-weight: 700; text-decoration: none">
                  {run.label || run.run_id}
                </a>
                {#if run.label}<div class="muted mono">{run.run_id}</div>{/if}
              </td>
              <td class="muted small">{when(run.created_at)}</td>
              <td><span class="pill">{run.environment}</span></td>
              <td class="mono">{run.clips_complete}/{run.clips_total}</td>
              <td>
                <span class="pill" class:good={run.status === "complete"} class:bad={run.status === "failed"}>
                  {run.status || "unknown"}
                </span>
              </td>
              <td>
                <span class="pill" class:good={run.score_status === "current"} class:warn={run.score_status !== "current"}>
                  {run.score_status || "missing"}
                </span>
              </td>
              <td>
                <span class={`pill ${tone(run.release_eligible)}`}>
                  {run.release_eligible ? "eligible" : "blocked"}
                </span>
              </td>
              <td>
                <a class="btn" style="padding: 5px 9px" href={`/runs/${encodeURIComponent(run.run_id)}`}>Open</a>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
