<script>
  let { ontext, label = "Ask by voice" } = $props();

  const SR =
    typeof window !== "undefined" ? window.SpeechRecognition || window.webkitSpeechRecognition : null;
  const supported = !!SR;

  let listening = $state(false);
  let rec = null;

  function stop() {
    try {
      rec?.stop();
    } catch {}
    listening = false;
  }

  function start() {
    if (!supported) return;
    if (listening) {
      stop();
      return;
    }
    rec = new SR();
    rec.lang = "en-US";
    rec.interimResults = true;
    rec.continuous = false;
    rec.onresult = (e) => {
      let text = "";
      let final = false;
      for (const r of e.results) {
        text += r[0].transcript;
        if (r.isFinal) final = true;
      }
      ontext?.(text, final);
    };
    rec.onend = () => (listening = false);
    rec.onerror = () => (listening = false);
    listening = true;
    try {
      rec.start();
    } catch {
      listening = false;
    }
  }

  $effect(() => () => stop());
</script>

{#if supported}
  <button
    type="button"
    onclick={start}
    title={listening ? "Stop listening" : label}
    aria-label={listening ? "Stop listening" : label}
    class="grid h-[38px] w-[38px] shrink-0 place-items-center rounded-lg border-2 transition {listening
      ? 'border-accent bg-accent text-white'
      : 'border-line text-muted hover:border-accent2'}"
  >
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="9" y="2" width="6" height="12" rx="3" />
      <path d="M5 10v1a7 7 0 0 0 14 0v-1" />
      <line x1="12" y1="19" x2="12" y2="22" />
    </svg>
  </button>
{/if}
