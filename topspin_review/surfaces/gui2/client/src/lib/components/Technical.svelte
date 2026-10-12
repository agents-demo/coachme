<script>
  import { callImage } from "$lib/api";
  import { pretty, shortLabel, STEP_SHORT, STEP_GROUP, GROUP_ORDER, MODEL_STEP } from "$lib/format";

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
  // Steps grouped under their pipeline stage; names/maps live in $lib/format (shared with the live feed).
  const grouped = $derived.by(() => {
    const buckets = new Map(GROUP_ORDER.map((g) => [g, []]));
    for (const t of timeline) buckets.get(STEP_GROUP[t.stage] || "Other").push(t);
    return GROUP_ORDER.map((g) => ({ name: g, items: buckets.get(g) })).filter((x) => x.items.length);
  });
  function modelName(stage) {
    const kind = MODEL_STEP[stage];
    const name = kind === "vision" ? models.vision : models.text;
    return `Uses the ${kind} model${name ? ` (${name})` : ""}.`;
  }

  let view = $state("Stages");
  const TABS = ["Stages", "Calls & tools"];

  // Merge model calls + tool calls into one sequence, then group by the step (stage) each ran in.
  const events = $derived.by(() => {
    const evs = [];
    for (const c of calls) evs.push({ kind: "model", seq: c.seq ?? 0, data: c });
    for (const t of tools) evs.push({ kind: "tool", seq: t.seq ?? 0, data: t });
    return evs.sort((a, b) => (a.seq || 0) - (b.seq || 0));
  });
  const byStage = $derived.by(() => {
    const map = new Map();
    for (const e of events) {
      const key = e.data.stage || "—";
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(e);
    }
    return [...map.entries()]
      .map(([stage, items]) => ({ stage, items, first: Math.min(...items.map((i) => i.seq || 0)) }))
      .sort((a, b) => a.first - b.first);
  });
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
  reply.   <b>cached</b> is the discounted subset the provider serves from its prompt cache.
</p>

{#if report.artifacts?.pose}
  <p class="mt-1 text-xs text-muted">
    The <b>pose overlay</b> is computed <b>locally</b> by mediapipe (PoseLandmarker) — a small on-device model,
    not an API call — so it uses no tokens and is not counted above.
  </p>
{/if}

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
    {#if events.length}
      {#each byStage as g}
        <h4 class="mt-4 flex items-baseline gap-2 text-sm font-semibold first:mt-0">
          <span class="text-accent">{g.stage && g.stage !== "—" ? shortLabel(g.stage) : "Other"}</span>
          {#if g.stage && g.stage !== "—" && STEP_GROUP[g.stage]}
            <span class="text-[11px] font-normal uppercase tracking-wide text-muted">{STEP_GROUP[g.stage]}</span>
          {/if}
          <span class="ml-auto text-[11px] font-normal text-muted">
            {g.items.length} event{g.items.length === 1 ? "" : "s"}
          </span>
        </h4>
        <div class="mt-1 space-y-2">
          {#each g.items as e}
            {#if e.kind === "model"}
              {@const c = e.data}
              <details class="card p-3 text-sm">
                <summary class="cursor-pointer font-semibold">
                  {#if c.probe}
                    🔍 image-support probe
                  {:else}
                    ↳ Model call {c.model ? `· ${c.model}` : ""}
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
                  <div>
                    <div class="mb-1 inline-block rounded-md bg-accent2/15 px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide text-accent2">
                      Input — everything sent to the model
                    </div>
                    {#if c.input?.length}
                      {#each c.input as m}
                        <div class="mt-1">
                          <span class="rounded border border-line px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted">{m.role}</span>
                          <pre class="mt-1 overflow-auto rounded bg-ink/40 p-2 text-xs">{m.content}</pre>
                        </div>
                      {/each}
                    {:else}
                      <p class="text-xs text-muted">Input not saved (SAVE_CALL_IO is off) or unavailable.</p>
                    {/if}
                    {#if c.images?.length}
                      <div class="mt-2">
                        <div class="text-[11px] text-muted">Images sent to the model ({c.images.length})</div>
                        <div class="mt-1 flex flex-wrap gap-2">
                          {#each c.images as p}
                            <img
                              src={callImage(report.stem, p.split(/[\\/]/).pop())}
                              alt=""
                              loading="lazy"
                              class="max-h-72 rounded border-2 border-line"
                            />
                          {/each}
                        </div>
                      </div>
                    {/if}
                  </div>
                  <div class="border-t-2 border-line pt-3">
                    <div class="mb-1 inline-block rounded-md bg-good/15 px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide text-good">
                      Output — what the model produced
                    </div>
                    {#if c.requested?.length}
                      {#each c.requested as tc}
                        <div class="mt-1 text-xs">↳ requested tool <code class="text-accent2">{tc.name}</code> with:</div>
                        {#if tc.arguments}
                          <pre class="mt-1 overflow-auto rounded bg-ink/40 p-2 text-xs">{tc.arguments}</pre>
                        {/if}
                      {/each}
                    {/if}
                    {#if c.output}
                      <pre class="mt-1 overflow-auto rounded bg-ink/40 p-2 text-xs">{c.output}</pre>
                    {:else if !c.requested?.length}
                      <p class="mt-1 text-xs text-muted">Output not saved (SAVE_CALL_IO is off) or the model produced no text.</p>
                    {/if}
                  </div>
                </div>
              </details>
            {:else}
              {@const t = e.data}
              <details class="card p-3 text-sm">
                <summary class="cursor-pointer font-semibold">
                  🔧 Tool · {t.name || "tool"}{#if t.seconds}<span class="ml-2 text-xs text-muted">{Number(t.seconds).toFixed(2)}s</span>{/if}
                </summary>
                <div class="mt-2 space-y-2">
                  <div>
                    <div class="mb-1 inline-block rounded-md bg-accent2/15 px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide text-accent2">
                      Input — arguments passed to the tool
                    </div>
                    <pre class="overflow-auto rounded bg-ink/40 p-2 text-xs">{pretty(t.arguments) || "{}"}</pre>
                  </div>
                  <div class="border-t-2 border-line pt-3">
                    <div class="mb-1 inline-block rounded-md bg-good/15 px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide text-good">
                      Output — result the tool returned
                    </div>
                    {#if t.error}<p class="text-xs text-bad">{t.error}</p>{/if}
                    <pre class="overflow-auto rounded bg-ink/40 p-2 text-xs">{t.result || "(empty)"}</pre>
                  </div>
                </div>
              </details>
            {/if}
          {/each}
        </div>
      {/each}
      <p class="mt-4 text-xs text-muted">
        Merged model + tool events, grouped under the step they ran in and ordered by sequence.
      </p>
    {:else}
      <p class="text-sm text-muted">No call detail saved (SAVE_CALL_IO may be off).</p>
    {/if}
  {/if}
</div>
