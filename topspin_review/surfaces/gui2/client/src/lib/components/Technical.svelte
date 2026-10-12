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
  function stageLabel(stage) {
    return stage === "startup" ? "startup (imports & setup)" : stage;
  }
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
    </div>
  </div>
</div>

{#if models.text || models.vision}
  <p class="mt-2 text-xs text-muted">
    Text: {models.text || "?"} · Vision: {models.vision || "?"} · {models.provider || "?"} ({models.api_base || ""})
  </p>
{/if}

{#if timeline.length}
  <h3 class="mt-5 font-display text-sm font-bold uppercase tracking-wide text-muted">
    Stages <span class="font-normal normal-case tracking-normal">· time taken</span>
  </h3>
  <ol class="mt-2 space-y-1.5">
    {#each timeline as t}
      {@const secs = Number(t.seconds) || 0}
      <li class="flex items-center gap-3 text-sm">
        <span class="w-44 shrink-0 truncate {t.stage === 'startup' ? 'text-muted' : ''}">{stageLabel(t.stage)}</span>
        <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-surface">
          <div
            class="h-full rounded-full {t.stage === 'startup' ? 'bg-line' : 'bg-accent'}"
            style={`width:${totalSeconds ? Math.max(1.5, (secs / totalSeconds) * 100) : 0}%`}
          ></div>
        </div>
        <span class="w-14 shrink-0 text-right font-mono text-xs text-muted">{secs.toFixed(1)}s</span>
      </li>
    {/each}
  </ol>
  <p class="mt-3 text-xs text-muted">
    Total run: <span class="font-semibold text-app">{totalSeconds.toFixed(1)}s</span>
    &nbsp;·&nbsp;bar length and numbers are <b>durations</b> (how long each step took), not timestamps.
  </p>
{/if}

{#if calls.length || tools.length}
  <h3 class="mt-5 font-display text-sm font-bold uppercase tracking-wide text-muted">Model &amp; tool calls</h3>
  <div class="mt-2 space-y-2">
    {#each calls as c}
      <details class="card p-3 text-sm">
        <summary class="cursor-pointer font-semibold">
          ↳ Model call {c.model ? `· ${c.model}` : ""} {c.label ? `· ${c.label}` : ""}
          <span class="ml-2 text-xs text-muted">
            {c.prompt_tokens ?? 0} in / {c.completion_tokens ?? 0} out{#if c.seconds} · {c.seconds}s{/if}
          </span>
        </summary>
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
          🔧 Tool · {t.name || "tool"}{#if t.seconds}<span class="ml-2 text-xs text-muted">{t.seconds}s</span>{/if}
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
  <p class="mt-4 text-sm text-muted">No call detail saved (SAVE_CALL_IO may be off).</p>
{/if}
