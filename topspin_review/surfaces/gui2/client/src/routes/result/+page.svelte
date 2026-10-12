<script>
  import { page } from "$app/stores";
  import { getReport, ask, artifact, exportUrl } from "$lib/api";
  import VideoReview from "$lib/components/VideoReview.svelte";
  import Technical from "$lib/components/Technical.svelte";
  import { scoreTone, issueText, fmtTime, CONF_TONE, CONF_HELP } from "$lib/format";

  const stem = $derived($page.url.searchParams.get("stem") || "");
  let report = $state(null);
  let loading = $state(true);
  let error = $state("");
  let tab = $state("Watch");
  let question = $state("");
  let answers = $state([]);
  let asking = $state(false);

  // Each tab is named by what the user does there, with a one-line hint.
  // User-facing tabs on the left; the raw execution detail is a separate "utility" tab on the right.
  const MAIN_TABS = [
    { id: "Watch", hint: "Play the video. Tap a moment to jump to it; click the chart to seek." },
    { id: "Coaching", hint: "Your focus, what's working, what to fix, and drills to practice." },
    { id: "Model view", hint: "The frames, motion map, and pose the model looked at — how it reached the findings." },
    { id: "Details", hint: "Limitations, the report-quality score, and downloads." },
  ];
  const TECH_TAB = {
    id: "Diagnostics",
    hint: "Raw run detail (model calls, tokens, tool calls, stage timeline). For debugging, not coaching.",
  };

  const evidence = $derived(
    Boolean(report?.artifacts?.motion || report?.artifacts?.frames || report?.artifacts?.pose),
  );

  async function load() {
    if (!stem) {
      loading = false;
      return;
    }
    loading = true;
    error = "";
    try {
      report = await getReport(stem);
    } catch (e) {
      error = String(e?.message || e);
      report = null;
    } finally {
      loading = false;
    }
  }
  $effect(() => {
    load();
  });

  async function doAsk() {
    if (!question.trim() || !stem) return;
    const q = question;
    question = "";
    asking = true;
    try {
      const { answer } = await ask(stem, q);
      answers = [...answers, { q, answer }];
    } catch {
      answers = [...answers, { q, answer: "Could not answer." }];
    } finally {
      asking = false;
    }
  }
</script>

{#if loading}
  <p class="mt-6 text-sm text-muted">Loading…</p>
{:else if error}
  <p class="mt-6 text-sm text-bad">{error}</p>
{:else if !report}
  <p class="mt-6 text-sm text-muted">No report selected.</p>
{:else}
  <div class="flex items-baseline gap-3">
    <h1 class="font-display text-2xl font-bold">{report.stem}</h1>
    <span class="text-sm text-muted">{report.sport} · {report.date}</span>
    <span
      class="ml-auto text-right"
      title="How trustworthy the report is (evidence coverage, confidence, no unsupported spin/speed claims) — not how well you played."
    >
      <span class="font-display text-xl font-bold {scoreTone(report.score?.score ?? 0)}">
        {report.score?.score ?? 0}<span class="text-sm text-muted">/100</span>
      </span>
      <span class="block text-[11px] uppercase tracking-wide text-muted">report quality</span>
    </span>
  </div>

  <div class="sticky top-14 z-20 -mx-4 mt-4 border-b-2 border-line bg-ink/90 px-4 backdrop-blur">
    <div class="flex gap-1 overflow-x-auto">
      {#each MAIN_TABS as t}
        <button
          onclick={() => (tab = t.id)}
          class="whitespace-nowrap border-b-2 px-3 py-2 text-sm font-semibold transition"
          class:border-accent={tab === t.id}
          class:text-app={tab === t.id}
          class:border-transparent={tab !== t.id}
          class:text-muted={tab !== t.id}
        >{t.id}</button>
      {/each}
      <button
        onclick={() => (tab = TECH_TAB.id)}
        title={TECH_TAB.hint}
        class="ml-auto whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium transition"
        class:border-accent={tab === TECH_TAB.id}
        class:text-app={tab === TECH_TAB.id}
        class:border-transparent={tab !== TECH_TAB.id}
        class:text-muted={tab !== TECH_TAB.id}
      >⚙ {TECH_TAB.id}</button>
    </div>
  </div>

  <p class="mt-2 text-xs text-muted">{[...MAIN_TABS, TECH_TAB].find((t) => t.id === tab)?.hint}</p>

  <div class="mt-3">
    {#if tab === "Watch"}
      <VideoReview {report} />
      {#if evidence}
        <button
          onclick={() => (tab = "Model view")}
          class="mt-4 rounded-lg border-2 border-line px-3 py-2 text-sm font-semibold text-muted transition hover:border-accent2 hover:text-app"
        >See what the model looked at (frames, motion map, pose) →</button>
      {/if}
    {:else if tab === "Model view"}
      {#if evidence}
        <div class="grid gap-4 sm:grid-cols-2">
          {#if report.artifacts?.frames}
            <figure><img src={artifact(report.stem, "frames")} alt="sampled frames" class="w-full rounded-lg border-2 border-line" /><figcaption class="mt-1 text-xs text-muted">Sampled frames the model read.</figcaption></figure>
          {/if}
          {#if report.artifacts?.motion}
            <figure><img src={artifact(report.stem, "motion")} alt="motion map" class="w-full rounded-lg border-2 border-line" /><figcaption class="mt-1 text-xs text-muted">Motion map — red = where you moved most.</figcaption></figure>
          {/if}
          {#if report.artifacts?.pose}
            <figure><img src={artifact(report.stem, "pose")} alt="pose overlay" class="w-full rounded-lg border-2 border-line" /><figcaption class="mt-1 text-xs text-muted">Body-pose overlay.</figcaption></figure>
          {/if}
        </div>
      {:else}
        <p class="text-sm text-muted">No frames saved for this report (single-image inputs have none).</p>
      {/if}
    {:else if tab === "Coaching"}
      {#if report.focus}
        <div class="rounded-lg border-2 border-good/40 bg-good/10 p-3 text-sm"><b>Focus next session:</b> {report.focus}</div>
      {/if}
      {#if report.summary}<p class="mt-3 text-sm">{report.summary}</p>{/if}

      {#if report.strengths?.length}
        <h3 class="mt-4 font-display font-bold">What's working</h3>
        <ul class="mt-1 list-disc pl-5 text-sm">{#each report.strengths as s}<li>{s}</li>{/each}</ul>
      {/if}

      {#if report.issues?.length}
        <h3 class="mt-4 font-display font-bold">What to fix</h3>
        <ul class="mt-1 space-y-1 text-sm">
          {#each report.issues as i}
            <li class="rounded-lg border-2 border-line p-2">
              {issueText(i)}
              {#if i.evidence_times?.length}
                <span class="ml-1 font-mono text-xs text-accent2">{i.evidence_times.map((t) => fmtTime(t)).join(", ")}</span>
              {/if}
              {#if i.confidence}
                <span
                  class="ml-2 whitespace-nowrap rounded-full border-2 border-line px-2 py-0.5 text-xs {CONF_TONE[i.confidence] || 'text-muted'}"
                  title={CONF_HELP}
                >{i.confidence} confidence</span>
              {/if}
            </li>
          {/each}
        </ul>
      {/if}

      {#if report.drills?.length}
        <h3 class="mt-4 font-display font-bold">Drills to practice</h3>
        <ul class="mt-1 list-disc pl-5 text-sm">{#each report.drills as d}<li>{d}</li>{/each}</ul>
      {/if}
      {#if report.progress}<p class="mt-3 text-sm text-muted">Since last time: {report.progress}</p>{/if}
    {:else if tab === "Details"}
      {#if report.limitations?.length}
        <h3 class="font-display font-bold">Keep in mind</h3>
        <ul class="mt-1 list-disc pl-5 text-sm">{#each report.limitations as l}<li>{l}</li>{/each}</ul>
      {/if}
      <p class="mt-3 text-sm">
        <b class={scoreTone(report.score?.score ?? 0)}>{report.score?.score ?? 0}/100</b> —
        how trustworthy the report is, not how well you played. Built from
        evidence coverage ({Math.round((report.score?.evidence_coverage || 0) * 100)}% of issues cite a timestamp),
        the confidence mix, and a check for unsupported claims (spin / ball speed / exact angles).
      </p>
      {#if report.score?.hallucination_flags?.length}
        <p class="mt-1 text-xs text-bad">Unsupported claims flagged: {report.score.hallucination_flags.join(", ")}</p>
      {/if}
      <div class="mt-3 flex gap-3 text-sm">
        <a class="rounded-lg border-2 border-line px-4 py-2 font-semibold" href={exportUrl(report.stem, "md")} download>Download Markdown</a>
        <a class="rounded-lg border-2 border-line px-4 py-2 font-semibold" href={exportUrl(report.stem, "html")} target="_blank" rel="noreferrer">Open HTML</a>
      </div>
    {:else if tab === "Diagnostics"}
      <Technical {report} />
    {/if}
  </div>

  <section class="card mt-6 p-4">
    <h3 class="font-display font-bold">Ask about this report</h3>
    {#each answers as a}
      <div class="mt-2 text-sm"><span class="text-muted">You:</span> {a.q}<br /><span class="text-accent2">Coach:</span> {a.answer}</div>
    {/each}
    <div class="mt-3 flex gap-2">
      <input
        bind:value={question}
        onkeydown={(e) => e.key === "Enter" && doAsk()}
        placeholder="e.g. How do I fix my split-step?"
        class="flex-1 rounded-lg border-2 border-line bg-surface px-3 py-2 text-sm"
      />
      <button onclick={doAsk} disabled={asking} class="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
        {asking ? "…" : "Ask"}
      </button>
    </div>
  </section>
{/if}
