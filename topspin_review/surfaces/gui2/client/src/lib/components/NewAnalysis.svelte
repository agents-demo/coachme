<script>
  import { onMount } from "svelte";
  import { samples, upload, analyzeAsync } from "$lib/api";

  let { onqueued } = $props();

  let mode = $state("sample");
  let list = $state([]);
  let samplePath = $state("");
  let file = $state(null);
  let pathText = $state("");
  let agentic = $state(false);
  let useBox = $state(false);
  let box = $state([0, 0, 1, 1]);
  let busy = $state(false);
  let error = $state("");

  onMount(async () => {
    try {
      list = (await samples()).samples;
      samplePath = list[0]?.path || "";
    } catch {
      list = [];
    }
  });

  async function submit() {
    error = "";
    busy = true;
    try {
      let video_path = "";
      if (mode === "upload") {
        if (!file) throw new Error("Choose a file first.");
        video_path = (await upload(file)).path;
      } else if (mode === "sample") {
        if (!samplePath) throw new Error("No sample clip found. Make one with tests\\integration\\make_sample.py.");
        video_path = samplePath;
      } else {
        video_path = pathText.trim();
        if (!video_path) throw new Error("Enter a video path.");
      }
      const region_box = useBox ? box.map(Number) : null;
      const { job_id } = await analyzeAsync({ video_path, region_box, agentic });
      onqueued?.(job_id);
    } catch (e) {
      error = String(e?.message || e);
    } finally {
      busy = false;
    }
  }
</script>

<section class="card mt-5 p-5">
  <h2 class="font-display text-lg font-bold">Analyze a video or photo</h2>
  <p class="mt-1 text-sm text-muted">
    A few rallies from the side (full body) gives the most; a single photo gives posture feedback.
  </p>

  <div class="mt-3 flex flex-wrap gap-2 text-sm">
    {#each [["sample", "Use the sample clip"], ["upload", "Upload a clip/photo"], ["path", "Paste a path"]] as [v, label]}
      <button
        onclick={() => (mode = v)}
        class="rounded-full border-2 px-3 py-1.5 font-semibold transition"
        class:border-accent={mode === v}
        class:bg-surface={mode === v}
        class:border-line={mode !== v}
        class:text-muted={mode !== v}
      >{label}</button>
    {/each}
  </div>

  <div class="mt-4">
    {#if mode === "sample"}
      {#if list.length}
        <select bind:value={samplePath} class="w-full rounded-lg border-2 border-line bg-surface px-3 py-2 text-sm">
          {#each list as s (s.path)}<option value={s.path}>{s.title}</option>{/each}
        </select>
      {:else}
        <p class="text-sm text-muted">
          No sample yet. Run <code>python tests\integration\make_sample.py</code>, then upload it.
        </p>
      {/if}
    {:else if mode === "upload"}
      <input
        type="file"
        accept="video/*,image/*"
        onchange={(e) => (file = e.currentTarget.files?.[0] || null)}
        class="w-full rounded-lg border-2 border-line bg-surface px-3 py-2 text-sm"
      />
    {:else}
      <input
        bind:value={pathText}
        placeholder="C:\path\to\session.mp4"
        class="w-full rounded-lg border-2 border-line bg-surface px-3 py-2 text-sm"
      />
    {/if}
  </div>

  <details class="mt-3 text-sm">
    <summary class="cursor-pointer font-semibold text-muted">Advanced</summary>
    <div class="mt-2 flex flex-col gap-2">
      <label class="flex items-center gap-2">
        <input type="checkbox" bind:checked={agentic} />
        Let the model decide what to review (slower)
      </label>
      <label class="flex items-center gap-2">
        <input type="checkbox" bind:checked={useBox} />
        Only look at me (region box, 0..1)
      </label>
      {#if useBox}
        <div class="grid grid-cols-4 gap-2">
          {#each ["left", "top", "right", "bottom"] as name, i}
            <label class="text-xs text-muted">{name}
              <input type="number" min="0" max="1" step="0.05" bind:value={box[i]}
                class="mt-1 w-full rounded border-2 border-line bg-surface px-2 py-1" />
            </label>
          {/each}
        </div>
      {/if}
    </div>
  </details>

  {#if error}<p class="mt-3 text-sm text-bad">{error}</p>{/if}

  <button
    onclick={submit}
    disabled={busy}
    class="mt-4 rounded-lg bg-accent px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
  >{busy ? "Starting…" : "Analyze"}</button>
</section>
