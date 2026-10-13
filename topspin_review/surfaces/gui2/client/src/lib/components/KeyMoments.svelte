<script>
  import { source } from "$lib/api";
  import { issueGroups, fmtTime, CONF_TONE, CONF_HELP } from "$lib/format";

  let { report, moments = null } = $props();

  const groups = $derived(moments ? [] : issueGroups(report));
  let open = $state(null); // { t, text }
  let video = $state();

  function play(t, text) {
    open = { t, text };
  }
  function close() {
    open = null;
  }
  function onReady() {
    if (video && open) {
      try {
        video.currentTime = open.t;
        video.play();
      } catch {}
    }
  }
  function onKey(e) {
    if (e.key === "Escape") close();
  }
</script>

<svelte:window onkeydown={onKey} />

{#if moments?.length}
  <div class="flex flex-wrap gap-1.5">
    {#each moments as m}
      <button
        onclick={() => play(m.t, m.label)}
        class="rounded-full border-2 border-line px-2.5 py-0.5 font-mono text-xs text-accent2 transition hover:border-accent2"
        title="Play this moment in a pop-up"
      >▶ {fmtTime(m.t)} <span class="font-sans text-muted">{m.label}</span></button>
    {/each}
  </div>
{:else if !groups.length}
  <p class="text-sm text-muted">No timestamped issues in this report.</p>
{:else}
  <ol class="space-y-2">
    {#each groups as g, i}
      <li class="rounded-xl border-2 border-line p-3">
        <p class="text-sm leading-snug">{g.text}</p>
        <div class="mt-2 flex flex-wrap items-center gap-1.5">
          {#if g.confidence}
            <span class="shrink-0 rounded-full border-2 border-line px-2 py-0.5 text-xs {CONF_TONE[g.confidence] || 'text-muted'}" title={CONF_HELP}>
              confidence: {g.confidence}
            </span>
          {/if}
          {#each g.times as t}
            <button
              onclick={() => play(t, g.text)}
              class="rounded-full border-2 border-line px-2.5 py-0.5 font-mono text-xs text-accent2 transition hover:border-accent2"
              title="Play this moment in a pop-up"
            >▶ {fmtTime(t)}</button>
          {/each}
        </div>
      </li>
    {/each}
  </ol>
{/if}

{#if open}
  <div class="fixed inset-0 z-50 grid place-items-center bg-ink/80 p-4" role="presentation" onclick={close}>
    <div class="w-full max-w-3xl rounded-2xl border-2 border-line bg-ink p-3 shadow-xl" role="presentation" onclick={(e) => e.stopPropagation()}>
      <div class="mb-2 flex items-center justify-between gap-3">
        <span class="font-mono text-sm text-accent2">▶ {fmtTime(open.t)}</span>
        <button onclick={close} title="Close" class="rounded-lg border-2 border-line px-2 py-0.5 text-sm font-semibold">✕</button>
      </div>
      <!-- svelte-ignore a11y_media_has_caption -->
      <video bind:this={video} src={source(report.stem)} controls autoplay onloadedmetadata={onReady} class="w-full rounded-lg border-2 border-line"></video>
      <p class="mt-2 text-sm text-muted">{open.text}</p>
    </div>
  </div>
{/if}
