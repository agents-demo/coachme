<script>
  import { pretty } from "$lib/format";

  let { report } = $props();

  const usage = $derived(report.usage || {});
  const models = $derived(usage.models || {});
  const calls = $derived(report.calls || []);
  const tools = $derived(report.tools || []);
  const nCalls = $derived(usage.calls ?? (usage.vision?.calls || 0) + (usage.text?.calls || 0));
  const tokens = $derived(usage.total_tokens ?? (usage.vision?.total_tokens || 0) + (usage.text?.total_tokens || 0));

  const timeline = $derived(report.timeline || []);
  const totalSeconds = $derived(timeline.reduce((a, t) => a + (Number(t.seconds) || 0), 0));
  const cachedTotal = $derived(
    usage.cached_tokens ?? (usage.vision?.cached_tokens || 0) + (usage.text?.cached_tokens || 0),
  );
  function stageLabel(stage) {
    return stage === "startup" ? "startup (imports & setup)" : stage;
  }

  // The architectural stages (core.stages) are measure → observe → coach; each progress tick
  // below is a sub-step inside one of them (plus a setup prologue and a finalize epilogue).
  const STAGE_GROUP = {
    startup: "setup",
    preparing: "setup",
    "sampling frames": "measure",
    "measuring motion": "measure",
    "writing artifacts": "measure",
    "vision: overview": "observe",
    "vision: zoom": "observe",
    "vision: detail": "observe",
    "vision: reviewing image": "observe",
    "agent writing report": "coach",
    "saving report": "coach",
    verifying: "coach",
    exporting: "finalize",
    done: "finalize",
  };
  const GROUP_ORDER = ["setup", "measure", "observe", "coach", "finalize", "other"];
  const grouped = $derived.by(() => {
    const buckets = new Map(GROUP_ORDER.map((g) => [g, []]));
    for (const t of timeline) buckets.get(STAGE_GROUP[t.stage] || "other").push(t);
    return GROUP_ORDER.map((g) => ({ name: g, items: buckets.get(g) })).filter((x) => x.items.length);
  });

  // What each step (and stage) actually does — authored here, matching the pipeline's tick() calls.
  const STEP_HELP = {
    startup: "Python importing the pipeline + agent machinery before the run starts (pre-run overhead).",
    preparing: "Validate the clip, load your profile, and set up the run.",
    "sampling frames": "Pick the frames to analyze — motion-weighted, so the busy moments get more.",
    "measuring motion": "Compute the objective metrics from the frames (energy, shift, region motion, ball/rally).",
    "writing artifacts": "Render the contact sheet, motion map and metrics so the vision model can read them.",
    "vision: overview": "Vision pass 1 — the model reads the contact sheet and proposes the moments worth a closer look.",
    "vision: zoom": "Sample extra frames inside the moments the model flagged.",
    "vision: detail": "Vision pass 2 — zoom in and return findings with timestamps + confidence.",
    "vision: reviewing image": "Single still — one vision pass on the image (posture only).",
    "agent writing report": "The text model turns the observations into the coaching report (its tool calls happen here).",
    "agent: analyzing": "Agentic mode — the model drives the analysis and writes the report.",
    "saving report": "Persist the report to disk (<stem>_report.json).",
    verifying: "A second model pass that prunes any finding the evidence doesn't support.",
    exporting: "Write the export files (Markdown / HTML / PDF).",
    done: "Run complete.",
  };
  const GROUP_HELP = {
    setup: "Before the pipeline: imports and setup.",
    measure: "Stage 1 — clip → frames + measurements.",
    observe: "Stage 2 — frames → observations (vision).",
    coach: "Stage 3 — observations → coaching report.",
    finalize: "Wrap-up: save run details and export the report.",
    other: "Uncategorized steps.",
  };

  let view = $state("Stages");
  const TABS = ["Stages", "Calls & tools"];
</script>

<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
  <div class="card p-3">
    <div class="text-xs uppercase text-muted">Model calls</div>
    <div class="font-display text-2xl font-bold">{nCalls}</div>
    <div class="mt-1 text-xs text-muted">
      <span class="font-mono text-app">{usage.vision?.calls ?? 0}</span> vision ·
      <span class="font-mono text-app">{usage.text?.calls ?? 0}</span> text
    </div>
  </div>
  <div class="card p-3">
    <div class="text-xs uppercase text-muted">Tokens billed</div>
    <div class="font-display text-2xl font-bold">{tokens.toLocaleString()}</div>
    <div class="mt-1 text-xs text-muted">
      <span class="font-mono text-app">{(usage.vision?.total_tokens || 0).toLocaleString()}</span> vision ·
      <span class="font-mono text-app">{(usage.text?.total_tokens || 0).toLocaleString()}</span> text
      {#if cachedTotal}<span> · <span class="font-mono text-app">{cachedTotal.toLocaleString()}</span> cached</span>{/if}
    </div>
  </div>
</div>

<p class="mt-2 text-xs text-muted">
  Tokens are the model's own counts. <b>in</b> = the whole prompt sent that call (system prompt +
  full history + question), so the same context is billed again on every turn; <b>out</b> = the
  reply. <b>cached</b> is the discounted subset the provider serves from its prompt cache.
</p>

<div class="mt-5 flex gap-5">
  {#each TABS as t}
    <button
      onclick={() => (view = t)}
      class="whitespace-nowrap border-b-2 pb-1 text-sm font-semibold transition"
      class:border-accent={view === t}
      class:text-app={view === t}
      class:border-transparent={view !== t}
      class:text-muted={view !== t}
    >{t}</button>
  {/each}
</div>

<div class="mt-3">
  {#if view === "Stages"}
    {#if timeline.length}
      {#each grouped as g}
        <div class="mt-3 first:mt-0">
          <div class="text-[11px] font-semibold uppercase tracking-wide text-accent" title={GROUP_HELP[g.name] || ""}>
            {g.name}
          </div>
          <ol class="mt-1 space-y-1.5">
            {#each g.items as t}
              {@const secs = Number(t.seconds) || 0}
              <li class="flex items-center gap-3 text-sm" title={STEP_HELP[t.stage] || ""}>
                <span class="w-44 shrink-0 truncate pl-2 {t.stage === 'startup' ? 'text-muted' : ''}">{stageLabel(t.stage)}</span>
                <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-surface">
                  <div
                    class="h-full rounded-full {t.stage === 'startup' ? 'bg-line' : 'bg-accent'}"
                    style={`width:${totalSeconds ? Math.max(1.5, (secs / totalSeconds) * 100) : 0}%`}
                  ></div>
                </div>
                <span class="w-14 shrink-0 text-right font-mono text-xs text-muted">{secs.toFixed(2)}s</span>
              </li>
            {/each}
          </ol>
        </div>
      {/each}
      <p class="mt-3 text-xs text-muted">
        Total run: <span class="font-semibold text-app">{totalSeconds.toFixed(2)}s</span>
        &nbsp;·&nbsp;bars and numbers are <b>durations</b>. Each row is a <b>step</b>; steps are grouped
        under the <b>stage</b> they run in — the pipeline's three stages are
        <b>measure → observe → coach</b> (plus setup before and finalize after).
      </p>
      <details class="mt-3 text-xs">
        <summary class="cursor-pointer text-muted">What the stages &amp; steps mean</summary>
        <ul class="mt-2 space-y-1">
          {#each GROUP_ORDER as g}
            {#if GROUP_HELP[g] && grouped.some((x) => x.name === g)}
              <li><span class="font-semibold text-app">{g}</span> — <span class="text-muted">{GROUP_HELP[g]}</span></li>
            {/if}
          {/each}
        </ul>
        <ul class="mt-2 space-y-1 border-t-2 border-line pt-2">
          {#each grouped as g}
            {#each g.items as t}
              {#if STEP_HELP[t.stage]}
                <li><span class="font-mono text-app">{stageLabel(t.stage)}</span> — <span class="text-muted">{STEP_HELP[t.stage]}</span></li>
              {/if}
            {/each}
          {/each}
        </ul>
      </details>
    {:else}
      <p class="text-sm text-muted">No stage timings saved.</p>
    {/if}
  {:else}
    {#if calls.length || tools.length}
      <div class="space-y-2">
        {#each calls as c}
          <details class="card p-3 text-sm">
            <summary class="cursor-pointer font-semibold">
              {#if c.probe}
                🔍 image-support probe
              {:else}
                ↳ Model call {c.model ? `· ${c.model}` : ""} {c.label ? `· ${c.label}` : ""}
              {/if}
              <span class="ml-2 text-xs text-muted">
                {c.prompt_tokens ?? 0} in / {c.completion_tokens ?? 0} out{#if c.cached_tokens} · {c.cached_tokens} cached{/if}{#if c.seconds} · {Number(c.seconds).toFixed(2)}s{/if}
              </span>
            </summary>
            {#if c.probe}
              <p class="mt-2 text-xs text-muted">
                A one-word self-check that the model can read images
                (“What color is this image?” → “{c.output}”). Not part of the analysis.
              </p>
            {/if}
            <div class="mt-2 space-y-2">
              {#each c.input || [] as m}
                <div>
                  <div class="text-xs uppercase text-muted">{m.role}</div>
                  <pre class="overflow-auto rounded bg-ink/40 p-2 text-xs">{m.content}</pre>
                </div>
              {/each}
              {#if c.output}
                <div class="text-xs uppercase text-muted">output</div>
                <pre class="overflow-auto rounded bg-ink/40 p-2 text-xs">{c.output}</pre>
              {/if}
            </div>
          </details>
        {/each}
        {#each tools as t}
          <details class="card p-3 text-sm">
            <summary class="cursor-pointer font-semibold">
              🔧 Tool · {t.name || "tool"}{#if t.seconds}<span class="ml-2 text-xs text-muted">{Number(t.seconds).toFixed(2)}s</span>{/if}
            </summary>
            <div class="mt-2 text-xs uppercase text-muted">arguments</div>
            <pre class="overflow-auto rounded bg-ink/40 p-2 text-xs">{pretty(t.arguments) || "{}"}</pre>
            {#if t.result}
              <div class="mt-2 text-xs uppercase text-muted">result</div>
              <pre class="overflow-auto rounded bg-ink/40 p-2 text-xs">{t.result}</pre>
            {/if}
            {#if t.error}<p class="mt-2 text-xs text-bad">{t.error}</p>{/if}
          </details>
        {/each}
      </div>
    {:else}
      <p class="text-sm text-muted">No call detail saved (SAVE_CALL_IO may be off).</p>
    {/if}
  {/if}
</div>
