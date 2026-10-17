<script>
  import { tr } from "$lib/appearance";
  import { page } from "$app/stores";
  import { getReport, ask, artifact, clip, exportUrl, reelUrl, cardUrl } from "$lib/api";
  import VideoReview from "$lib/components/VideoReview.svelte";
  import Technical from "$lib/components/Technical.svelte";
  import ReadAloud from "$lib/components/ReadAloud.svelte";
  import VoiceInput from "$lib/components/VoiceInput.svelte";
  import PoseChart from "$lib/components/PoseChart.svelte";
  import Pose3D from "$lib/components/Pose3D.svelte";
  import Ball3D from "$lib/components/Ball3D.svelte";
  import MotionChart from "$lib/components/MotionChart.svelte";
  import FootworkChart from "$lib/components/FootworkChart.svelte";
  import Segments from "$lib/components/Segments.svelte";
  import KeyMoments from "$lib/components/KeyMoments.svelte";
  import TrimExport from "$lib/components/TrimExport.svelte";
  import Provenance from "$lib/components/Provenance.svelte";
  import { outputs } from "$lib/outputs";
  import { movementSeries, issueText, fmtTime, CONF_TONE, CONF_HELP, POSE_SERIES } from "$lib/format";

  const stem = $derived($page.url.searchParams.get("stem") || "");
  const vtName = $derived('r-' + stem.replace(/[^a-zA-Z0-9]/g, '-'));
  let report = $state(null);
  let loading = $state(true);
  let error = $state("");
  let tab = $state("Video");
  let measureGroup = $state("maps");
  let playTime = $state(0);
  let playerRef = $state();
  let ball3dRef = $state();
  let obsView = $state("Findings");
  let coachView = $state("Advice");
  let videoView = $state("Motion");
  const isPhoto = $derived(/\.(png|jpg|jpeg|bmp|webp|gif)$/i.test(report?.source || ""));
  let question = $state("");
  let answers = $state([]);
  let asking = $state(false);

  // Tabs are separated by *what a thing is*: your media, what was measured (CV), and the coach's read (AI).
  const MAIN_TABS = [
    { id: "Video", hint: "Your clip: watch it, step frame-by-frame, slow it down, draw on it — with the motion measured from it." },
    { id: "Analysis", hint: "Results of analysing the video — the body, any tracked object, and the spatial maps. Pure analysis, no sport terms." },
    { id: "Observations", hint: "Everything we saw — the findings read in table-tennis terms, plus the notable moments. Not coaching yet." },
    { id: "Coaching", hint: "What the coach says: your focus, what to fix, drills, and the flagged moments." },
  ];
  const TECH_TAB = {
    id: "Diagnostics",
    hint: "Raw run detail (model calls, tokens, tool calls, stage timeline). For debugging, not coaching.",
  };

  const clipWarnings = $derived(report?.quality?.warnings || []);
  const caveats = $derived((report?.limitations || []).filter((l) => !clipWarnings.includes(l)));

  const outputGroups = $derived(outputs(report));
  const videoGroup = $derived(outputGroups.find((g) => g.id === "clip"));
  const motionGroup = $derived(outputGroups.find((g) => g.id === "movement"));
  const detectionGroups = $derived(
    ["maps", "body", "ball"]
      .map((id) => outputGroups.find((g) => g.id === id))
      .filter(Boolean),
  );
  // Video tab sub-tabs: "Motion" (player + measured-from-video items) and "Frames" (the stills read).
  const videoMotionItems = $derived(motionGroup?.items || []);
  const frameItems = $derived((videoGroup?.items || []).filter((i) => i.id === "frames"));
  const activeDetect = $derived(detectionGroups.find((g) => g.id === measureGroup) || detectionGroups[0]);
  const duration = $derived(Math.max(0.001, ...(report?.frame_times || [1])));
  const segments = $derived(report?.metrics?.ball?.segments || []);
  const strokes = $derived(report?.metrics?.strokes || []);
  const series = $derived(movementSeries(report));

  const summaryText = $derived.by(() => {
    if (!report) return "";
    const parts = [`${report.sport || "Session"} on ${report.date || "an unknown date"}.`];
    if (report.focus) parts.push(`Focus next session: ${report.focus}.`);
    const issueList = (report.issues || []).slice(0, 3).map((i) => issueText(i)).filter(Boolean);
    if (issueList.length) parts.push(`What to fix: ${issueList.join(". ")}.`);
    if (report.summary) parts.push(report.summary);
    return parts.join(" ");
  });

  const issues = $derived(report?.issues || []);

  let doneDrills = $state({});
  function drillsKey(stem) {
    return `topspin.drills.${stem || "unknown"}`;
  }
  function loadDrills(stem) {
    try {
      const raw = localStorage.getItem(drillsKey(stem));
      const saved = raw ? JSON.parse(raw) : {};
      return saved && typeof saved === "object" ? saved : {};
    } catch {
      return {};
    }
  }
  function toggleDrill(i) {
    doneDrills = { ...doneDrills, [i]: !doneDrills[i] };
    try {
      localStorage.setItem(drillsKey(report?.stem), JSON.stringify(doneDrills));
    } catch {}
  }
  const doneCount = $derived(Object.values(doneDrills).filter(Boolean).length);

  function splitIssue(text) {
    const s = String(text || "");
    const c = s.indexOf(": ");
    if (c > 8 && c < 160) return [s.slice(0, c), s.slice(c + 2)];
    const d = s.indexOf(". ");
    if (d > 8 && d < 160) return [s.slice(0, d + 1), s.slice(d + 2)];
    return [s, ""];
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
      tab = "Video";
      doneDrills = loadDrills(report?.stem);
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

  function speak(text) {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text || "");
    u.rate = 0.95;
    window.speechSynthesis.speak(u);
  }

  async function doAsk() {
    if (!question.trim() || !stem) return;
    const q = question;
    question = "";
    asking = true;
    try {
      const { answer } = await ask(stem, q);
      answers = [...answers, { q, answer }];
      speak(answer);
    } catch {
      answers = [...answers, { q, answer: "Could not answer." }];
    } finally {
      asking = false;
    }
  }
</script>

{#snippet visual(it)}
  {#if it.id === "video"}
    <VideoReview {report} />
  {:else if it.id === "movement"}
    <MotionChart series={movementSeries(report)} playhead={playTime} onseek={(t) => playerRef?.seek(t)} />
  {:else if it.id === "segments"}
    <Segments {segments} {duration} playhead={playTime} onseek={(t) => playerRef?.seek(t)} />
  {:else if it.id === "strokes"}
    <div class="flex flex-wrap gap-1.5">
      {#each strokes as s}
        <span class="rounded-full border-2 border-line px-2.5 py-0.5 font-mono text-xs text-accent2" title={`${s.hand} · strength ${s.strength}`}>
          {s.hand === "left" ? "L" : s.hand === "right" ? "R" : "?"} {fmtTime(s.t)}
        </span>
      {/each}
    </div>
  {:else if it.id === "lateral"}
    <div class="flex flex-wrap gap-8">
      <div>
        <div class="font-display text-3xl font-bold">{Math.round((it.lateral ?? 0) * 100)}%</div>
        <div class="text-[11px] uppercase tracking-wide text-muted">{tr("Side-to-side travel (the band's height)")}</div>
      </div>
      <div>
        <div class="font-display text-3xl font-bold">{it.steps ?? 0}</div>
        <div class="text-[11px] uppercase tracking-wide text-muted">{tr("Direction changes (the dots)")}</div>
      </div>
    </div>
    <div class="mt-4">
      <FootworkChart series={report.metrics?.footwork_series || []} lateral={it.lateral} steps={it.steps} />
    </div>
  {:else if it.id === "pose_angles"}
    <PoseChart {report} />
  {:else if it.id === "pose3d"}
    <Pose3D {report} />
  {:else if it.id === "ball3d"}
    <Ball3D {report} />
  {:else if it.kind}
    <figure>
      <img src={artifact(report.stem, it.kind)} alt={tr(it.label)} class="w-full rounded-xl border-2 border-line" />
    </figure>
  {:else if it.id === "ball"}
    <p class="rounded-xl border-2 border-line p-4 text-sm text-muted">
      {tr("No small moving object detected in this clip — automatic tracking is hard here.")}
    </p>
  {/if}
{/snippet}

{#snippet frow(f)}
  <div class="text-sm">
    <span class="font-semibold text-app">{tr(f.label)}:</span>
    <span class="text-app"> {tr(f.value)}</span>
    <span class="block text-xs text-muted">{tr(f.note)}</span>
  </div>
{/snippet}

{#if loading}
  <p class="mt-6 text-sm text-muted">{tr("Loading…")}</p>
{:else if error}
  <p class="mt-6 text-sm text-bad">{error}</p>
{:else if !report}
  <p class="mt-6 text-sm text-muted">{tr("No report selected.")}</p>
{:else}
  <div class="flex flex-wrap items-baseline gap-3" style="view-transition-name: {vtName}">
    <h1 class="font-display text-2xl font-bold">{report.stem}</h1>
    <span class="text-sm text-muted">{tr(report.sport)} · {report.date}</span>
    {#if report.fallback}
      <span class="rounded-full border border-warn px-2 py-0.5 text-[11px] font-semibold text-warn" title="The live run failed; this is the last recorded result for this clip.">{tr("recorded run")}</span>
    {/if}
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
        >{tr(t.id)}</button>
      {/each}
      <button
        onclick={() => (tab = TECH_TAB.id)}
        title={tr(TECH_TAB.hint)}
        class="ml-auto whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium transition"
        class:border-accent={tab === TECH_TAB.id}
        class:text-app={tab === TECH_TAB.id}
        class:border-transparent={tab !== TECH_TAB.id}
        class:text-muted={tab !== TECH_TAB.id}
      >⚙ {tr(TECH_TAB.id)}</button>
    </div>
  </div>

  <p class="mt-2 text-xs text-muted">{tr([...MAIN_TABS, TECH_TAB].find((t) => t.id === tab)?.hint ?? "")}</p>

  <div class="mt-3">
    {#if tab === "Video"}
      <div class="mb-5 flex gap-5 border-b-2 border-line pb-2">
        {#each ["Motion", "Frames"] as v}
          <button
            onclick={() => (videoView = v)}
            class="whitespace-nowrap border-b-2 pb-0.5 text-sm font-semibold transition"
            class:border-accent={videoView === v}
            class:text-app={videoView === v}
            class:border-transparent={videoView !== v}
            class:text-muted={videoView !== v}
          >{tr(v)}</button>
        {/each}
      </div>
      {#if videoView === "Motion"}
        {#if report.has_source && !isPhoto}
          <div class="flex items-start justify-between gap-3">
            <h3 class="font-display text-sm font-bold uppercase tracking-wide text-muted">{tr("Clip")}</h3>
            <TrimExport {report} />
          </div>
          <div class="mt-3"><VideoReview {report} bind:this={playerRef} bind:time={playTime} /></div>
        {/if}
        <div class="mt-8 space-y-14">
          {#each videoMotionItems as it (it.id)}
            <section>
              <h3 class="font-display text-sm font-bold uppercase tracking-wide text-muted">{tr(it.label)}</h3>
              <Provenance item={it} />
              <div class="mt-3">{@render visual(it)}</div>
            </section>
          {/each}
        </div>
      {:else}
        <div class="space-y-14">
          {#each frameItems as it (it.id)}
            <section>
              <h3 class="font-display text-sm font-bold uppercase tracking-wide text-muted">{tr(it.label)}</h3>
              <Provenance item={it} />
              <div class="mt-3">{@render visual(it)}</div>
            </section>
          {/each}
        </div>
      {/if}
    {:else if tab === "Analysis"}
      {#if detectionGroups.length > 1}
        <div class="mb-5 flex flex-wrap gap-x-4 gap-y-1 border-b-2 border-line pb-2">
          {#each detectionGroups as g}
            <button
              onclick={() => (measureGroup = g.id)}
              class="whitespace-nowrap border-b-2 pb-0.5 text-sm font-semibold transition"
              class:border-accent={activeDetect?.id === g.id}
              class:text-app={activeDetect?.id === g.id}
              class:border-transparent={activeDetect?.id !== g.id}
              class:text-muted={activeDetect?.id !== g.id}
            >{tr(g.group)}</button>
          {/each}
        </div>
      {/if}
      {#if activeDetect}
        <div class="space-y-14">
          {#each activeDetect.items as it (it.id)}
            <section>
              <h3 class="font-display text-sm font-bold uppercase tracking-wide text-muted">{tr(it.label)}</h3>
              <Provenance item={it} />
              <div class="mt-3">{@render visual(it)}</div>
            </section>
          {/each}
        </div>
      {/if}
    {:else if tab === "Observations"}
      <div class="mb-5 flex gap-5 border-b-2 border-line pb-2">
        {#each ["Findings", "Key moments"] as v}
          <button
            onclick={() => (obsView = v)}
            class="whitespace-nowrap border-b-2 pb-0.5 text-sm font-semibold transition"
            class:border-accent={obsView === v}
            class:text-app={obsView === v}
            class:border-transparent={obsView !== v}
            class:text-muted={obsView !== v}
          >{tr(v)}</button>
        {/each}
      </div>
      {#if obsView === "Findings"}
      {#if report.tt_reading?.findings?.length}
        {#each ["Play", "Player", "Ball"] as grp}
          {@const items = report.tt_reading.findings.filter((f) => f.group === grp)}
          {#if items.length}
            <section class="mt-5 rounded-xl border-2 border-line p-4">
              <h4 class="font-display text-sm font-bold uppercase tracking-wide text-accent">{tr(grp)}</h4>

              {#if grp === "Ball"}
                <div class="mt-3 space-y-5">
                  {#if report.artifacts?.ball}
                    <div class="grid gap-5 sm:grid-cols-2">
                      <figure>
                        <img src={artifact(report.stem, "ball")} alt="Tracked path" class="w-full rounded-lg border-2 border-line" />
                      </figure>
                      <div class="grid content-start gap-y-2">
                        {#each items.filter((f) => f.label === "Tracked" || f.label === "Path extent") as f}{@render frow(f)}{/each}
                      </div>
                    </div>
                  {/if}
                  {#if (report.metrics?.ball?.trajectory3d || []).length > 2}
                    <div class="grid gap-5 sm:grid-cols-2">
                      <Ball3D {report} hideStats hideControls bind:this={ball3dRef} />
                      <div class="grid content-start gap-y-2">
                        {#each items.filter((f) => f.label !== "Tracked" && f.label !== "Path extent") as f}{@render frow(f)}{/each}
                        <button onclick={() => ball3dRef?.reset()} class="mt-2 w-fit rounded-lg border-2 border-line px-2.5 py-1 text-xs font-semibold text-app">{tr("Reset view")}</button>
                      </div>
                    </div>
                  {/if}
                  {#if !report.artifacts?.ball && (report.metrics?.ball?.trajectory3d || []).length <= 2}
                    <div class="grid content-start gap-y-2">
                      {#each items as f}{@render frow(f)}{/each}
                    </div>
                  {/if}
                </div>
              {:else}
                <div class="mt-3 grid gap-5 sm:grid-cols-2">
                  <div class="space-y-4">
                    {#if grp === "Play"}
                      {#if series.length}<MotionChart {series} playhead={0} onseek={() => {}} />{/if}
                      {#if segments.length}<Segments {segments} {duration} playhead={0} onseek={() => {}} tt />{/if}
                    {:else if grp === "Player"}
                      {#if report.artifacts?.pose_hero || report.artifacts?.pose}
                        <figure>
                          <img src={artifact(report.stem, report.artifacts.pose_hero ? "pose_hero" : "pose")} alt="Skeleton" class="w-full rounded-lg border-2 border-line" />
                        </figure>
                      {/if}
                      <PoseChart {report} chrome={false} />
                    {/if}
                  </div>

                  <div class="grid content-start gap-y-2">
                    {#each items as f}{@render frow(f)}{/each}
                    {#if grp === "Player"}
                      <div class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-muted">
                        {#each POSE_SERIES as s (s.key)}
                          <span class="inline-flex items-center gap-1.5">
                            <span class="inline-block h-2 w-3 rounded-full" style={`background:${s.color}`}></span>{tr(s.label)}
                          </span>
                        {/each}
                        <span>0°–180° · {fmtTime(duration)}</span>
                      </div>
                      <p class="text-xs text-muted">
                        {tr("Joint angles over the clip (from the sampled frames). Values are pose estimates, not clinical measurements.")}
                      </p>
                    {/if}
                  </div>
                </div>
              {/if}
            </section>
          {/if}
        {/each}
      {:else}
        <p class="mt-3 text-sm text-muted">{tr("No observations available for this run.")}</p>
      {/if}
      {:else}

      {#if issues.length || report.focus}
        <section class="mt-8">
          <h3 class="flex items-center gap-2 font-display text-sm font-bold uppercase tracking-wide text-muted">
            {tr("Key moments")}
            <span class="inline-flex items-center gap-1 rounded-full border-2 border-accent2/40 bg-accent2/5 px-1.5 py-0.5 text-[10px] font-semibold text-accent2">{tr("✨ AI agent")}</span>
          </h3>
          <p class="mt-1 text-xs text-muted">{tr("The notable seconds — click a time to play just that moment.")}</p>
          <div class="mt-3"><KeyMoments {report} /></div>
        </section>
      {/if}

      {#if report.clips && Object.keys(report.clips).length}
        <section class="mt-8">
          <h3 class="font-display text-sm font-bold uppercase tracking-wide text-muted">{tr("Moment clips")}</h3>
          <p class="mt-1 text-xs text-muted">{tr("Short clips around the noted moments.")}</p>
          <div class="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {#each Object.entries(report.clips).sort((a, b) => Number(a[0]) - Number(b[0])) as [key]}
              <figure class="rounded-xl border-2 border-line p-2">
                <!-- svelte-ignore a11y_media_has_caption -->
                <video src={clip(report.stem, key)} controls preload="metadata" class="w-full rounded-lg border-2 border-line"></video>
                <figcaption class="mt-1 flex items-center justify-between text-xs text-muted">
                  <span class="font-mono">@ {fmtTime(Number(key))}</span>
                  <a href={clip(report.stem, key)} download class="font-semibold text-accent">{tr("Download")}</a>
                </figcaption>
              </figure>
            {/each}
          </div>
        </section>
      {/if}
      {/if}
    {:else if tab === "Coaching"}
      <div class="mb-5 flex gap-5 border-b-2 border-line pb-2">
        {#each ["Advice", "Practice", "Export", "Ask"] as v}
          <button
            onclick={() => (coachView = v)}
            class="whitespace-nowrap border-b-2 pb-0.5 text-sm font-semibold transition"
            class:border-accent={coachView === v}
            class:text-app={coachView === v}
            class:border-transparent={coachView !== v}
            class:text-muted={coachView !== v}
          >{tr(v)}</button>
        {/each}
      </div>
      {#if coachView === "Advice"}
      <div class="mb-3 flex justify-end">
        <ReadAloud text={summaryText} />
      </div>
      {#if report.focus}
        <div class="rounded-2xl border-2 border-good/40 bg-good/10 p-5">
          <div class="font-display text-sm font-bold uppercase tracking-wide text-good">{tr("Focus next session")}</div>
          <p class="mt-1 text-base font-semibold text-app">{report.focus}</p>
        </div>
      {/if}
      <div class="mt-4 grid gap-4 lg:grid-cols-2">
        <section class="rounded-xl border-2 border-good/30 bg-good/5 p-4">
          <h3 class="flex items-center gap-2 font-display font-bold text-good">✅ {tr("What's working")}</h3>
          {#if report.strengths?.length}
            <ul class="mt-2 space-y-1.5 text-sm">
              {#each report.strengths as s}<li>{s}</li>{/each}
            </ul>
          {:else}
            <p class="mt-2 text-sm text-muted">—</p>
          {/if}
        </section>

        {#if issues.length}
          <section class="rounded-xl border-2 border-warn/30 bg-warn/5 p-4">
            <h3 class="flex items-center gap-2 font-display font-bold text-warn">🎯 {tr("What to improve")}</h3>
            <ul class="mt-2 space-y-1.5 text-sm">
              {#each issues as issue}
                {@const parts = splitIssue(issueText(issue))}
                <li class="flex items-start gap-2">
                  <span class="mt-0.5 text-warn">•</span>
                  <span class="font-semibold">{parts[0]}</span>
                </li>
              {/each}
            </ul>
            <p class="mt-2 text-xs text-muted">{tr("Full observations (with timestamps) are on the Observations tab.")}</p>
          </section>
        {/if}
      </div>

      {#if report.summary || report.progress}
        <div class="mt-6 border-t-2 border-line pt-4">
          <h4 class="text-[11px] font-semibold uppercase tracking-wide text-muted">{tr("Read more")}</h4>
          {#if report.summary}<p class="mt-2 text-sm text-muted">{report.summary}</p>{/if}
          {#if report.progress}<p class="mt-3 text-sm text-muted"><b class="text-app">{tr("Since last time:")}</b> {report.progress}</p>{/if}
        </div>
      {/if}

      {#if clipWarnings.length || caveats.length}
        <div class="mt-6 border-t-2 border-line pt-4">
          <h4 class="text-[11px] font-semibold uppercase tracking-wide text-muted">{tr("About this analysis")}</h4>
          {#if clipWarnings.length}
            <h4 class="mt-3 text-sm font-semibold text-app">{tr("Your clip")}</h4>
            <ul class="mt-1 list-disc pl-5 text-sm">{#each clipWarnings as w}<li>{w}</li>{/each}</ul>
          {/if}
          {#if caveats.length}
            <h4 class="mt-3 text-sm font-semibold text-app">{tr("Limits")}</h4>
            <ul class="mt-1 list-disc pl-5 text-sm">{#each caveats as l}<li>{l}</li>{/each}</ul>
          {/if}
        </div>
      {/if}
      {:else if coachView === "Export"}
      <h3 class="font-display font-bold">{tr("Export")}</h3>
      <p class="mt-1 text-sm text-muted">{tr("Save or share this report.")}</p>

      <div class="mt-4 flex flex-wrap gap-3 text-sm">
        <a class="rounded-lg border-2 border-line px-4 py-2 font-semibold" href={exportUrl(report.stem, "md")} download>{tr("Download Markdown")}</a>
        <a class="rounded-lg border-2 border-line px-4 py-2 font-semibold" href={exportUrl(report.stem, "html")} target="_blank" rel="noreferrer">{tr("Open HTML")}</a>
        {#if report.clips && Object.keys(report.clips).length}
          <a class="rounded-lg border-2 border-line px-4 py-2 font-semibold" href={reelUrl(report.stem)} download>{tr("Highlight reel (mp4)")}</a>
        {/if}
        <a class="rounded-lg border-2 border-line px-4 py-2 font-semibold" href={cardUrl(report.stem)} download>{tr("Share card (PNG)")}</a>
      </div>
      {:else if coachView === "Practice"}
      {#if report.drills?.length}
        <div class="mb-4 flex items-center gap-3">
          <span class="text-sm text-muted">{doneCount} {tr("of")} {report.drills.length} {tr("done")}</span>
          <div class="ml-auto h-2 w-40 overflow-hidden rounded-full bg-surface">
            <div class="h-full rounded-full bg-accent transition-all" style={`width: ${(doneCount / report.drills.length) * 100}%`}></div>
          </div>
        </div>
        <ul class="space-y-3">
          {#each report.drills as d, i}
            {@const det = report.drill_details?.[i]}
            {@const done = !!doneDrills[i]}
            <li>
              <label
                class="flex cursor-pointer items-start gap-3 rounded-xl border-2 p-4 transition {done
                  ? 'border-good/50 bg-good/5'
                  : 'border-line'}"
              >
                <input type="checkbox" checked={done} onchange={() => toggleDrill(i)} class="mt-1 h-4 w-4" />
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2">
                    <span class="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-accent/15 text-xs font-bold text-accent">{i + 1}</span>
                    <span class="font-semibold text-app" class:text-muted={done} class:line-through={done}>{d}</span>
                  </div>
                  {#if det}
                    <div class="mt-2 space-y-1 pl-8 text-xs text-muted">
                      {#if det.cue}<div><span class="font-semibold text-app">{tr("Cue:")}</span> {det.cue}</div>{/if}
                      {#if det.progression}<div><span class="font-semibold text-app">{tr("Next step:")}</span> {det.progression}</div>{/if}
                    </div>
                  {/if}
                </div>
              </label>
            </li>
          {/each}
        </ul>
      {:else}
        <p class="text-sm text-muted">{tr("No practice items for this session.")}</p>
      {/if}
      {:else if coachView === "Ask"}
      <section class="card p-4">
        <h3 class="font-display font-bold">{tr("Ask about this report")}</h3>
        <p class="mt-1 text-xs text-muted">{tr("Type, or press the mic and speak — the answer is read aloud.")}</p>
        {#each answers as a}
          <div class="mt-2 text-sm">
            <div><span class="text-muted">{tr("You:")}</span> {a.q}</div>
            <div class="mt-0.5"><span class="text-accent2">{tr("Coach:")}</span> {a.answer}</div>
            <div class="mt-1"><ReadAloud text={a.answer} label={tr("Replay")} /></div>
          </div>
        {/each}
        <div class="mt-3 flex gap-2">
          <input
            bind:value={question}
            onkeydown={(e) => e.key === "Enter" && doAsk()}
            placeholder={tr("e.g. How do I fix my split-step?")}
            class="flex-1 rounded-lg border-2 border-line bg-surface px-3 py-2 text-sm"
          />
          <VoiceInput ontext={(t, final) => { question = t; if (final) doAsk(); }} />
          <button onclick={doAsk} disabled={asking} class="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
            {asking ? tr("Thinking…") : tr("Ask")}
          </button>
        </div>
      </section>
      {/if}
    {:else if tab === "Diagnostics"}
      <Technical {report} />
    {/if}
  </div>
{/if}
