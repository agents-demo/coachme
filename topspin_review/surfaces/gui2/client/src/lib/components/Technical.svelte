<script>
  import { pretty } from "$lib/format";

  let { report } = $props();

  const usage = $derived(report.usage || {});
  const models = $derived(usage.models || {});
  const calls = $derived(report.calls || []);
  const tools = $derived(report.tools || []);
  const nCalls = $derived(usage.calls ?? (usage.vision?.calls || 0) + (usage.text?.calls || 0));
  const tokens = $derived(usage.total_tokens ?? (usage.vision?.total_tokens || 0) + (usage.text?.total_tokens || 0));
</script>

<div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
  <div class="card p-3"><div class="text-xs uppercase text-muted">Model calls</div><div class="text-xl font-bold">{nCalls}</div></div>
  <div class="card p-3"><div class="text-xs uppercase text-muted">Tokens billed</div><div class="text-xl font-bold">{tokens.toLocaleString()}</div></div>
  <div class="card p-3"><div class="text-xs uppercase text-muted">Vision calls</div><div class="text-xl font-bold">{usage.vision?.calls ?? 0}</div></div>
  <div class="card p-3"><div class="text-xs uppercase text-muted">Text calls</div><div class="text-xl font-bold">{usage.text?.calls ?? 0}</div></div>
</div>

{#if models.text || models.vision}
  <p class="mt-2 text-xs text-muted">
    Text: {models.text || "?"} · Vision: {models.vision || "?"} · {models.provider || "?"} ({models.api_base || ""})
  </p>
{/if}

{#if report.timeline?.length}
  <h3 class="mt-5 font-display text-sm font-bold uppercase tracking-wide text-muted">Stages</h3>
  <ol class="mt-2 space-y-1">
    {#each report.timeline as t}
      <li class="flex items-center justify-between rounded-lg border-2 border-line px-3 py-1.5 text-sm">
        <span>{t.stage}</span><span class="font-mono text-xs text-muted">{t.seconds}s</span>
      </li>
    {/each}
  </ol>
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
