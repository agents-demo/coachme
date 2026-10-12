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
  // Each progress tick belongs to a pipeline stage. The header names are plain-English, with the
  // architecture name in parentheses (measure / observe / coach) so the two levels still line up.
  const STEP_GROUP = {
    startup: "Setup",
    preparing: "Setup",
    "sampling frames": "Measure",
    "measuring motion": "Measure",
    "writing artifacts": "Measure",
    "vision: overview": "Vision (observe)",
    "vision: zoom": "Vision (observe)",
    "vision: detail": "Vision (observe)",
    "vision: reviewing image": "Vision (observe)",
    "agent writing report": "Report (coach)",
    "agent: analyzing": "Report (coach)",
    "saving report": "Report (coach)",
    verifying: "Report (coach)",
    exporting: "Finalize",
    done: "Finalize",
  };
  const GROUP_ORDER = ["Setup", "Measure", "Vision (observe)", "Report (coach)", "Finalize", "Other"];
  const grouped = $derived.by(() => {
    const buckets = new Map(GROUP_ORDER.map((g) => [g, []]));
    for (const t of timeline) buckets.get(STEP_GROUP[t.stage] || "Other").push(t);
    return GROUP_ORDER.map((g) => ({ name: g, items: buckets.get(g) })).filter((x) => x.items.length);
  });

  // Plain-English name for each step (no "vision:"/"agent" jargon).
  const STEP_NAME = {
    startup: "Load pipeline",
    preparing: "Prepare clip",
    "sampling frames": "Pick frames",
    "measuring motion": "Measure movement",
    "writing artifacts": "Render images",
    "vision: overview": "First look",
    "vision: zoom": "Zoom in",
    "vision: detail": "Detailed findings",
    "vision: reviewing image": "Review image",
    "agent writing report": "Write report",
    "agent: analyzing": "Analyze",
    "saving report": "Save report",
    verifying: "Double-check",
    exporting: "Export files",
    done: "Done",
  };
  function shortLabel(stage) {
    return STEP_NAME[stage] || stage;
  }
  // Steps that make a model/agent call — tagged in the list so it's clear where tokens/time go.
  const MODEL_STEP = {
    "vision: overview": "vision",
    "vision: detail": "vision",
    "vision: reviewing image": "vision",
    "agent writing report": "text",
    "agent: analyzing": "text",
    verifying: "text",
  };
  function modelName(stage) {
    const kind = MODEL_STEP[stage];
    const name = kind === "vision" ? models.vision : models.text;
    return `Uses the ${kind} model${name ? ` (${name})` : ""}.`;
  }
  // Bookends are shown as a single stage row (their sub-steps are trivial bookkeeping).
  const COLLAPSED = new Set(["Setup", "Finalize"]);
  const GROUP_TIP = {
    Setup: "Load the pipeline and prepare the clip (before the stages).",
    Finalize: "Collect usage, save the run's details, and write the export files.",
  };
  // Hover tooltip text for each step.
  const STEP_SHORT = {
    startup: "Load the pipeline code (imports) — pre-run overhead.",
    preparing: "Validate the clip and load your profile.",
    "sampling frames": "Choose the frames to analyze (motion-weighted).",
    "measuring motion": "Compute the objective metrics from the frames.",
    "writing artifacts": "Render the frames + motion map the vision model reads.",
    "vision: overview": "Vision pass 1 — read the frames and pick the moments to zoom.",
    "vision: zoom": "Sample more frames inside those moments.",
    "vision: detail": "Vision pass 2 — findings with timestamps + confidence.",
    "vision: reviewing image": "One vision pass on the still image (posture only).",
    "agent writing report": "The text model writes the coaching report.",
    "agent: analyzing": "Agentic mode — the model drives the analysis.",
    "saving report": "Save the report file.",
    verifying: "A second model pass that prunes unsupported findings.",
    exporting: "Wrap-up: collect token usage, save the run's details, then write the export files (Markdown / HTML / PDF).",
    done: "Run complete.",
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
        {@const gsecs = g.items.reduce((a, t) => a + (Number(t.seconds) || 0), 0)}
        {#if COLLAPSED.has(g.name)}
          <div class="mt-3 first:mt-0 flex items-center gap-3 text-sm">
            <span class="w-52 shrink-0 pl-2 font-semibold" title={GROUP_TIP[g.name] || ""}>{g.name}</span>
            <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-surface">
              <div
                class="h-full rounded-full bg-line"
                style={`width:${totalSeconds ? Math.max(1.5, (gsecs / totalSeconds) * 100) : 0}%`}
              ></div>
            </div>
            <span class="w-14 shrink-0 text-right font-mono text-xs text-muted">{gsecs.toFixed(2)}s</span>
          </div>
        {:else}
          <div class="mt-3 first:mt-0">
            <div class="text-[11px] font-semibold uppercase tracking-wide text-accent">{g.name}</div>
            <ol class="mt-1 space-y-1.5">
              {#each g.items as t}
                {@const secs = Number(t.seconds) || 0}
                <li class="flex items-center gap-3 text-sm">
                  <div class="flex w-52 shrink-0 items-center gap-1.5 pl-2">
                    <span
                      class="truncate {t.stage === 'startup' ? 'text-muted' : ''}{STEP_SHORT[t.stage] ? ' cursor-help' : ''}"
                      title={STEP_SHORT[t.stage] || ""}
                    >{shortLabel(t.stage)}</span>
                    {#if MODEL_STEP[t.stage]}
                      <span
                        class="shrink-0 rounded border border-line px-1 text-[9px] font-semibold uppercase {MODEL_STEP[t.stage] === 'vision' ? 'text-accent2' : 'text-accent'}"
                        title={modelName(t.stage)}
                      >{MODEL_STEP[t.stage]}</span>
                    {/if}
                  </div>
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
        {/if}
      {/each}
      <p class="mt-3 text-xs text-muted">
        Total run: <span class="font-semibold text-app">{totalSeconds.toFixed(2)}s</span>
        &nbsp;·&nbsp;bars and numbers are <b>durations</b>. Each row is a <b>step</b>, grouped under the
        <b>stage</b> it runs in (Measure → Vision → Report). Steps tagged
        <span class="rounded border border-line px-1 text-[9px] font-semibold uppercase text-accent2">vision</span> /
        <span class="rounded border border-line px-1 text-[9px] font-semibold uppercase text-accent">text</span>
        call a model; hover a step for what it does.
      </p>
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
