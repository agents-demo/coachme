<script>
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { getLabelContext, getLabeler, saveLabel, setLabeler, sourceUrl } from "$lib/api";

  const runId = $derived($page.params.run_id);
  const clipId = $derived($page.params.clip_id);
  const themes = ["footwork", "stroke", "preparation", "recovery", "serve", "other"];
  const evidenceTypes = ["motion", "pose", "vision"];

  let context = $state(null);
  let loading = $state(true);
  let error = $state("");
  let problems = $state([]);
  let saving = $state(false);
  let saved = $state("");
  let etag = $state("");
  let labeler = $state("coach-a");
  let video = $state(null);
  let form = $state({ findings: [], acceptable_limitations: "", zero_finding_reason: "" });
  let draftTimer;

  const draftKey = $derived(`coachme.benchmark.draft.${runId}.${clipId}`);

  function fromLabel(label) {
    return {
      findings: (label?.findings || []).map((finding, index) => ({
        id: finding.id || `f${index + 1}`,
        text: finding.text || "",
        themes: finding.themes || [],
        timesText: (finding.evidence_times || []).join(", "),
        severity: finding.severity || "medium",
        required_evidence: finding.required_evidence || [],
      })),
      acceptable_limitations: (label?.acceptable_limitations || []).join("\n"),
      zero_finding_reason: label?.zero_finding_reason || "",
    };
  }

  function cleanFinding(finding) {
    const times = String(finding.timesText || "")
      .split(",")
      .map((item) => Number(item.trim()))
      .filter((item) => Number.isFinite(item));
    return {
      id: finding.id,
      text: finding.text.trim(),
      themes: finding.themes,
      evidence_times: times,
      severity: finding.severity,
      required_evidence: finding.required_evidence,
    };
  }

  function cleanForm() {
    return {
      findings: form.findings.map(cleanFinding),
      acceptable_limitations: form.acceptable_limitations
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean),
      zero_finding_reason: form.zero_finding_reason.trim(),
    };
  }

  async function load() {
    loading = true;
    error = "";
    problems = [];
    try {
      labeler = getLabeler();
      context = await getLabelContext(runId, clipId);
      etag = context.etag;
      form = fromLabel(context.label);
      if (!context.label) {
        try {
          const draft = localStorage.getItem(draftKey);
          if (draft) form = JSON.parse(draft);
        } catch {
          /* ignore a bad draft */
        }
      }
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    load();
    draftTimer = setInterval(() => {
      try {
        localStorage.setItem(draftKey, JSON.stringify(form));
      } catch {
        /* ignore quota errors */
      }
    }, 5000);
    return () => clearInterval(draftTimer);
  });

  function addFinding() {
    if (form.findings.length >= 5) return;
    form.findings.push({
      id: `f${form.findings.length + 1}-${Date.now().toString(36).slice(-4)}`,
      text: "",
      themes: ["footwork"],
      timesText: "",
      severity: "medium",
      required_evidence: ["vision"],
    });
  }

  function removeFinding(index) {
    form.findings.splice(index, 1);
  }

  function addCurrentTime(index) {
    if (!video) return;
    const value = Number(video.currentTime || 0).toFixed(2);
    const finding = form.findings[index];
    const current = finding.timesText.trim();
    finding.timesText = current ? `${current}, ${value}` : value;
  }

  async function save() {
    saving = true;
    error = "";
    problems = [];
    saved = "";
    try {
      if (!labeler.trim()) throw new Error("labeler is required");
      if (!form.findings.length && !form.zero_finding_reason.trim()) {
        throw new Error("zero findings require a zero_finding_reason");
      }
      setLabeler(labeler);
      const result = await saveLabel(clipId, cleanForm(), etag, labeler);
      etag = result.etag;
      saved = "Label saved.";
      try {
        localStorage.removeItem(draftKey);
      } catch {
        /* ignore */
      }
    } catch (err) {
      error = err.message;
      problems = err.detail?.error?.details?.problems || [];
    } finally {
      saving = false;
    }
  }

  function onKeydown(event) {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
      event.preventDefault();
      save();
    }
  }
</script>

<svelte:window onkeydown={onKeydown} />

{#if loading}
  <p class="muted" style="margin-top: 24px">Loading label…</p>
{:else if error && !context}
  <div class="error" style="margin-top: 24px">{error}</div>
{:else if context}
  <div class="row" style="justify-content: space-between; margin-top: 22px">
    <div>
      <a href={`/runs/${encodeURIComponent(runId)}`} class="muted small" style="text-decoration: none">← Run</a>
      <h1 style="margin: 6px 0 4px" class="mono">{clipId}</h1>
      <div class="row muted small">
        <span class="pill">{context.clip.sport}</span>
        <span class="pill">{context.clip.media_type}</span>
        <span class="pill">{context.clip.duration_s}s</span>
        <span class="pill" class:good={context.label_status === "complete"} class:warn={context.label_status !== "complete"}>
          {context.label_status}
        </span>
      </div>
    </div>
    <button class="btn primary" onclick={save} disabled={saving}>{saving ? "Saving…" : "Save label"}</button>
  </div>

  <div class="notice" style="margin-top: 14px">
    Label workspace: AI reports are hidden. This local UI does not enforce blindness against filesystem access.
  </div>

  {#if error}<div class="error" style="margin-top: 12px">{error}</div>{/if}
  {#if problems.length}
    <div class="error" style="margin-top: 12px">
      {#each problems as problem}<div>• {problem}</div>{/each}
    </div>
  {/if}
  {#if saved}<div class="notice" style="margin-top: 12px">{saved}</div>{/if}

  <div class="grid two" style="margin-top: 16px; align-items: start">
    <section class="card">
      {#if context.has_source && context.clip.media_type === "video"}
        <video bind:this={video} src={sourceUrl(runId, clipId)} controls preload="metadata"><track kind="captions" /></video>
      {:else if context.has_source}
        <img src={sourceUrl(runId, clipId)} alt="Benchmark clip" style="width: 100%; border-radius: 12px" />
      {/if}
      <div class="field" style="margin-top: 12px">
        <label for="labeler">Labeler</label>
        <input id="labeler" bind:value={labeler} placeholder="coach-a" />
      </div>
      <p class="muted small" style="margin-bottom: 0">
        Use “Add current time” while the video is paused at the evidence moment.
      </p>
    </section>

    <section class="card">
      <div class="row" style="justify-content: space-between">
        <h2 style="margin: 0">Findings</h2>
        <button class="btn" onclick={addFinding} disabled={form.findings.length >= 5}>Add finding</button>
      </div>

      {#each form.findings as finding, index (finding.id)}
        <div class="finding" style="margin-top: 12px">
          <div class="row" style="justify-content: space-between">
            <strong>Finding {index + 1}</strong>
            <button class="btn" style="padding: 4px 8px" onclick={() => removeFinding(index)}>Remove</button>
          </div>

          <div class="field" style="margin-top: 10px">
            <label for={`text-${index}`}>Text</label>
            <textarea id={`text-${index}`} bind:value={finding.text} maxlength="500" placeholder="What a coach would report"></textarea>
          </div>

          <div class="field">
            <span class="label">Themes</span>
            <div class="row">
              {#each themes as theme}
                <label class="pill" style="cursor: pointer">
                  <input type="checkbox" bind:group={finding.themes} value={theme} style="width: auto; margin-right: 5px" />
                  {theme}
                </label>
              {/each}
            </div>
          </div>

          <div class="grid two" style="gap: 10px">
            <div class="field">
              <label for={`times-${index}`}>Evidence times</label>
              <div class="row">
                <input id={`times-${index}`} bind:value={finding.timesText} placeholder="2.8, 4.1" style="flex: 1" />
                <button class="btn" onclick={() => addCurrentTime(index)} type="button">Add current time</button>
              </div>
            </div>
            <div class="field">
              <label for={`severity-${index}`}>Severity</label>
              <select id={`severity-${index}`} bind:value={finding.severity}>
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
            </div>
          </div>

          <div class="field" style="margin-bottom: 0">
            <span class="label">Required evidence</span>
            <div class="row">
              {#each evidenceTypes as kind}
                <label class="pill" style="cursor: pointer">
                  <input type="checkbox" bind:group={finding.required_evidence} value={kind} style="width: auto; margin-right: 5px" />
                  {kind}
                </label>
              {/each}
            </div>
          </div>
        </div>
      {/each}

      {#if !form.findings.length}
        <div class="field" style="margin-top: 12px">
          <label for="zero">Zero-finding reason</label>
          <textarea id="zero" bind:value={form.zero_finding_reason} placeholder="Why there is no reportable coaching finding"></textarea>
        </div>
      {/if}

      <div class="field">
        <label for="limitations">Acceptable limitations (one per line)</label>
        <textarea id="limitations" bind:value={form.acceptable_limitations} placeholder="ball placement not assessed"></textarea>
      </div>
    </section>
  </div>
{/if}
