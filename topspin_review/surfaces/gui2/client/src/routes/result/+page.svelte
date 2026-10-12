<script>
  import { page } from "$app/stores";
  import { getReport, ask, artifact, exportUrl, reelUrl, cardUrl } from "$lib/api";
  import VideoReview from "$lib/components/VideoReview.svelte";
  import Technical from "$lib/components/Technical.svelte";
  import ReadAloud from "$lib/components/ReadAloud.svelte";
  import PoseChart from "$lib/components/PoseChart.svelte";
  import Pose3D from "$lib/components/Pose3D.svelte";
  import Ball3D from "$lib/components/Ball3D.svelte";
  import { outputs } from "$lib/outputs";
  import { scoreTone, issueText, fmtTime, CONF_TONE, CONF_HELP } from "$lib/format";

  const stem = $derived($page.url.searchParams.get("stem") || "");
  let report = $state(null);
  let loading = $state(true);
  let error = $state("");
  let tab = $state("Watch");
  let watchView = $state("video");
  let question = $state("");
  let answers = $state([]);
  let asking = $state(false);
  let tourOpen = $state(false);
  let tourSeen = false;

  // User-facing tabs on the left; the raw execution detail is a separate "utility" tab on the right.
  const MAIN_TABS = [
    { id: "Watch", hint: "See everything this session produced — the clip, how you moved, the ball, your body — plus the moments to look at." },
    { id: "Coaching", hint: "Your focus, what's working, what to fix, and drills to practice." },
    { id: "Notes", hint: "Caveats about this clip, the report-quality score, and downloads." },
  ];
  const TECH_TAB = {
    id: "Diagnostics",
    hint: "Raw run detail (model calls, tokens, tool calls, stage timeline). For debugging, not coaching.",
  };

  const clipWarnings = $derived(report?.quality?.warnings || []);
  const caveats = $derived((report?.limitations || []).filter((l) => !clipWarnings.includes(l)));

  // Everything this run produced (see lib/outputs.js).
  const outputGroups = $derived(outputs(report));
  const outputItems = $derived(outputGroups.flatMap((g) => g.items));
  // Charts shown inside the Video view (and clips) are not separate tabs.
  const INLINE = ["movement", "segments", "clips"];
  const tabItems = $derived(outputItems.filter((i) => !INLINE.includes(i.id)));
  const current = $derived(tabItems.find((i) => i.id === watchView) || tabItems[0]);
  const hasImages = $derived(tabItems.length > 1);

  // Spoken summary: focus + the top few issues + the summary paragraph.
  const summaryText = $derived.by(() => {
    if (!report) return "";
    const parts = [`${report.sport || "Session"} on ${report.date || "an unknown date"}.`];
    if (report.focus) parts.push(`Focus next session: ${report.focus}.`);
    const issues = (report.issues || []).slice(0, 3).map((i) => issueText(i)).filter(Boolean);
    if (issues.length) parts.push(`What to fix: ${issues.join(". ")}.`);
    if (report.summary) parts.push(report.summary);
    return parts.join(" ");
  });

  const issues = $derived(report?.issues || []);

  // Drills checklist (local, not persisted).
  let doneDrills = $state({});
  function toggleDrill(i) {
    doneDrills = { ...doneDrills, [i]: !doneDrills[i] };
  }
  const doneCount = $derived(Object.values(doneDrills).filter(Boolean).length);

  // Split "claim: evidence" issue text so the metrics de-emphasize under the claim.
  function splitIssue(text) {
    const s = String(text || "");
    const c = s.indexOf(": ");
    if (c > 8 && c < 160) return [s.slice(0, c), s.slice(c + 2)];
    const d = s.indexOf(". ");
    if (d > 8 && d < 160) return [s.slice(0, d + 1), s.slice(d + 2)];
    return [s, ""];
  }

  function openTour() {
    tourOpen = true;
  }
  function closeTour() {
    tourOpen = false;
    tourSeen = true;
    try {
      localStorage.setItem("topspin_tour_seen", "1");
    } catch {}
  }

  async function load() {
    if (!stem) {
      loading = false;
      return;
    }
    loading = true;
    error = "";
    try {
      report = await getReport(stem);
      watchView = "video";
      doneDrills = {};
      if (!tourSeen) {
        try {
          tourSeen = !!localStorage.getItem("topspin_tour_seen");
        } catch {}
        if (!tourSeen) tourOpen = true;
      }
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
    {#if report.fallback}
      <span class="rounded-full border border-warn px-2 py-0.5 text-[11px] font-semibold text-warn" title="The live run failed; this is the last recorded result for this clip.">recorded run</span>
    {/if}
    <button onclick={openTour} title="What am I looking at?" class="rounded-full border-2 border-line px-2.5 py-0.5 text-xs font-semibold text-muted">?</button>
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
      {#if hasImages}
        <div class="mb-3 flex flex-wrap gap-x-4 gap-y-1">
          {#each tabItems as it}
            <button
              onclick={() => (watchView = it.id)}
              title={`${it.producer} · ${it.step} · ${it.where}`}
              class="whitespace-nowrap border-b-2 pb-0.5 text-sm font-semibold transition"
              class:border-accent={watchView === it.id}
              class:text-app={watchView === it.id}
              class:border-transparent={watchView !== it.id}
              class:text-muted={watchView !== it.id}
            >{it.label}</button>
          {/each}
        </div>
      {/if}

      {#if !current || ["video", "movement", "segments", "clips"].includes(current.id)}
        <VideoReview {report} />
      {:else if current.id === "pose_angles"}
        <PoseChart {report} />
      {:else if current.id === "pose3d"}
        <Pose3D {report} />
      {:else if current.id === "ball3d"}
        <Ball3D {report} />
      {:else if current.kind}
        <figure class="max-w-3xl">
          <img src={artifact(report.stem, current.kind)} alt={current.label} class="w-full rounded-lg border-2 border-line" />
        </figure>
      {/if}

      {#if current}
        <p class="mt-2 text-xs text-muted">
          made by <span class="font-mono text-app">{current.producer}</span>
          · step <span class="text-app">{current.step}</span>
          · <span class="font-mono">{current.where}</span>
          {#if current.local}<span class="ml-1 rounded border-2 border-line px-1.5 py-0.5 text-[10px]">on-device · no tokens</span>{/if}
        </p>
      {/if}
    {:else if tab === "Coaching"}
      <div class="mb-3 flex justify-end">
        <ReadAloud text={summaryText} />
      </div>
      {#if report.focus}
        <div class="rounded-xl border-2 border-good/40 bg-good/10 p-4 text-sm">
          <span class="font-display font-bold text-good">Focus next session · </span>{report.focus}
        </div>
      {/if}
      {#if report.summary}
        <div class="mt-3 rounded-xl border-2 border-line bg-surface/40 p-4 text-sm">{report.summary}</div>
      {/if}

      <div class="mt-4 grid gap-4 lg:grid-cols-2">
        <section class="rounded-xl border-2 border-good/30 bg-good/5 p-4">
          <h3 class="flex items-center gap-2 font-display font-bold text-good">✅ What's working</h3>
          {#if report.strengths?.length}
            <ul class="mt-2 space-y-1.5 text-sm">
              {#each report.strengths as s}<li>{s}</li>{/each}
            </ul>
          {:else}
            <p class="mt-2 text-sm text-muted">—</p>
          {/if}
        </section>

        <section class="rounded-xl border-2 border-warn/30 bg-warn/5 p-4">
          <h3 class="flex items-center gap-2 font-display font-bold text-warn">🎯 What to fix</h3>
          {#if issues.length}
            <ol class="mt-2 space-y-3 text-sm">
              {#each issues as issue, idx}
                {@const parts = splitIssue(issueText(issue))}
                <li class="flex gap-2">
                  <span class="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-warn/20 text-[11px] font-bold text-warn">{idx + 1}</span>
                  <div>
                    <div class="font-semibold">{parts[0]}</div>
                    {#if parts[1]}<div class="mt-0.5 text-xs text-muted">{parts[1]}</div>{/if}
                    <div class="mt-1.5 flex flex-wrap items-center gap-1.5">
                      {#each issue.evidence_times || [] as t}
                        <span class="rounded-full border-2 border-line px-2 py-0.5 font-mono text-xs text-accent2">{fmtTime(t)}</span>
                      {/each}
                      {#if issue.confidence}
                        <span
                          class="rounded-full border-2 border-line px-2 py-0.5 text-xs {CONF_TONE[issue.confidence] || 'text-muted'}"
                          title={CONF_HELP}
                        >{issue.confidence}</span>
                      {/if}
                    </div>
                  </div>
                </li>
              {/each}
            </ol>
          {:else}
            <p class="mt-2 text-sm text-muted">No issues found.</p>
          {/if}
        </section>
      </div>

      {#if report.drills?.length}
        <section class="mt-4 rounded-xl border-2 border-line p-4">
          <h3 class="flex items-center gap-2 font-display font-bold">
            🏋 Drills to practice
            <span class="text-xs font-normal text-muted">{doneCount}/{report.drills.length} done</span>
          </h3>
          <ul class="mt-2 space-y-2 text-sm">
            {#each report.drills as d, i}
              {@const det = report.drill_details?.[i]}
              <li class="rounded-xl border-2 border-line p-3">
                <label class="flex cursor-pointer items-start gap-2">
                  <input type="checkbox" checked={!!doneDrills[i]} onchange={() => toggleDrill(i)} class="mt-0.5" />
                  <span class="font-semibold" class:text-muted={doneDrills[i]} class:line-through={doneDrills[i]}>{d}</span>
                </label>
                {#if det}
                  <div class="mt-1.5 space-y-0.5 pl-6 text-xs text-muted">
                    {#if det.cue}<div><b class="text-app">Cue:</b> {det.cue}</div>{/if}
                    {#if det.progression}<div><b class="text-app">Next:</b> {det.progression}</div>{/if}
                  </div>
                {/if}
              </li>
            {/each}
          </ul>
          <div class="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-surface">
            <div class="h-full rounded-full bg-accent transition-all" style={`width: ${(doneCount / report.drills.length) * 100}%`}></div>
          </div>
        </section>
      {/if}

      {#if report.progress}<p class="mt-3 text-sm text-muted">Since last time: {report.progress}</p>{/if}
    {:else if tab === "Notes"}
      <h3 class="font-display font-bold">Notes</h3>
      <p class="mt-1 text-sm text-muted">
        Caveats for this analysis of <b>this clip</b> (and the limits of the method) — not coaching advice.
      </p>

      {#if clipWarnings.length}
        <h4 class="mt-4 text-sm font-semibold text-app">About your clip</h4>
        <ul class="mt-1 list-disc pl-5 text-sm">{#each clipWarnings as w}<li>{w}</li>{/each}</ul>
      {/if}

      {#if caveats.length}
        <h4 class="mt-4 text-sm font-semibold text-app">What limits the analysis</h4>
        <ul class="mt-1 list-disc pl-5 text-sm">{#each caveats as l}<li>{l}</li>{/each}</ul>
      {/if}

      <h4 class="mt-4 text-sm font-semibold text-app">Report quality</h4>
      <p class="mt-1 text-sm">
        <b class={scoreTone(report.score?.score ?? 0)}>{report.score?.score ?? 0}/100</b> —
        how trustworthy the report is, not how well you played. Built from
        evidence coverage ({Math.round((report.score?.evidence_coverage || 0) * 100)}% of issues cite a timestamp),
        the confidence mix, and a check for unsupported claims (spin / ball speed / exact angles).
      </p>
      {#if report.score?.hallucination_flags?.length}
        <p class="mt-1 text-xs text-bad">Unsupported claims flagged: {report.score.hallucination_flags.join(", ")}</p>
      {/if}

      <h4 class="mt-4 text-sm font-semibold text-app">Download</h4>
      <div class="mt-1 flex flex-wrap gap-3 text-sm">
        <a class="rounded-lg border-2 border-line px-4 py-2 font-semibold" href={exportUrl(report.stem, "md")} download>Download Markdown</a>
        <a class="rounded-lg border-2 border-line px-4 py-2 font-semibold" href={exportUrl(report.stem, "html")} target="_blank" rel="noreferrer">Open HTML</a>
        {#if report.clips && Object.keys(report.clips).length}
          <a class="rounded-lg border-2 border-line px-4 py-2 font-semibold" href={reelUrl(report.stem)} download>Highlight reel (mp4)</a>
        {/if}
        <a class="rounded-lg border-2 border-line px-4 py-2 font-semibold" href={cardUrl(report.stem)} download>Share card (PNG)</a>
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

  {#if tourOpen}
    <div class="fixed inset-0 z-50 grid place-items-center bg-ink/70 p-4" role="presentation">
      <div class="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-2xl border-2 border-line bg-ink p-5 shadow-xl">
        <div class="flex items-start justify-between gap-3">
          <h2 class="font-display text-lg font-bold">What you're looking at</h2>
          <button onclick={closeTour} title="Close" class="rounded-lg border-2 border-line px-2 py-0.5 text-sm font-semibold">✕</button>
        </div>
        <p class="mt-1 text-sm text-muted">
          For each item: the <b class="text-app">code</b> that produced it, the pipeline <b class="text-app">step</b>
          it ran in, and <b class="text-app">where</b> it lands. Everything here is computed on-device (no tokens);
          only the written report uses the model.
        </p>
        <div class="mt-4 space-y-3">
          {#each outputGroups as g}
            <div>
              <div class="text-[11px] font-semibold uppercase tracking-wide text-accent">{g.group}</div>
              <ul class="mt-1 space-y-1 text-sm">
                {#each g.items as it}
                  <li>
                    <b class="text-app">{it.label}</b> — <span class="font-mono text-muted">{it.producer}</span>,
                    step <span class="text-muted">{it.step}</span> → <span class="font-mono text-muted">{it.where}</span>
                  </li>
                {/each}
              </ul>
            </div>
          {/each}
        </div>
        <button onclick={closeTour} class="mt-5 w-full rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white">Got it</button>
      </div>
    </div>
  {/if}
{/if}
