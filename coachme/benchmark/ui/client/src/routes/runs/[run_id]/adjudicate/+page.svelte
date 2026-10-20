<script>
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { getAdjudicationQueue } from "$lib/api";

  const runId = $derived($page.params.run_id);
  let queue = $state(null);
  let loading = $state(true);
  let error = $state("");

  async function load() {
    loading = true;
    error = "";
    try {
      queue = await getAdjudicationQueue(runId);
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  onMount(load);
</script>

<div class="row" style="justify-content: space-between; margin-top: 22px">
  <div>
    <a href={`/runs/${encodeURIComponent(runId)}`} class="muted small" style="text-decoration: none">← Run</a>
    <h1 style="margin: 6px 0 4px">Adjudication</h1>
    <p class="muted" style="margin: 0">Resolve disagreements after both raters submit each clip.</p>
  </div>
  <button class="btn" onclick={load} disabled={loading}>Refresh</button>
</div>

{#if error}<div class="error" style="margin-top: 14px">{error}</div>{/if}

{#if loading}
  <p class="muted" style="margin-top: 18px">Loading adjudication queue…</p>
{:else if queue}
  <section class="card" style="margin-top: 16px">
    <div class="row" style="justify-content: space-between">
      <h2 style="margin: 0">Clips</h2>
      <span class="pill">{queue.required_raters} raters required</span>
    </div>

    {#if !queue.clips.length}
      <p class="muted">No blind packets in this run.</p>
    {:else}
      <table class="table" style="margin-top: 12px">
        <thead>
          <tr><th>Clip</th><th>Ready</th><th>Votes</th><th>Decision</th><th></th></tr>
        </thead>
        <tbody>
          {#each queue.clips as clip (clip.clip_id)}
            <tr>
              <td class="mono">{clip.clip_id}</td>
              <td><span class="pill" class:good={clip.ready} class:warn={!clip.ready}>{clip.ready ? "ready" : "waiting"}</span></td>
              <td>
                {#each clip.votes as vote}
                  <span class="pill">{vote.rater}: {vote.preferred}</span>
                {/each}
                {#if !clip.votes.length}<span class="muted">—</span>{/if}
              </td>
              <td>
                {#if clip.decision}
                  <span class="pill good">{clip.decision.preferred}</span>
                {:else}
                  <span class="muted">—</span>
                {/if}
              </td>
              <td>
                {#if clip.ready}
                  <a class="btn" style="padding: 4px 8px" href={`/runs/${encodeURIComponent(runId)}/adjudicate/${encodeURIComponent(clip.clip_id)}`}>
                    {clip.decision ? "Review" : "Adjudicate"}
                  </a>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </section>
{/if}
