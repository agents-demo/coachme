<script>
  let { text, label = "Play summary" } = $props();

  let speaking = $state(false);
  const supported = typeof window !== "undefined" && "speechSynthesis" in window;

  function toggle() {
    if (!supported) return;
    if (speaking) {
      window.speechSynthesis.cancel();
      speaking = false;
      return;
    }
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text || "");
    utter.rate = 0.95;
    utter.onend = () => (speaking = false);
    utter.onerror = () => (speaking = false);
    speaking = true;
    window.speechSynthesis.speak(utter);
  }

  // Stop speaking when this component unmounts (e.g. tab change / navigation).
  $effect(() => () => {
    if (supported) window.speechSynthesis.cancel();
  });
</script>

{#if supported && text}
  <button
    onclick={toggle}
    class="inline-flex items-center gap-1.5 rounded-lg border-2 border-line px-3 py-1.5 text-sm font-semibold text-app transition hover:border-accent2"
    title="Read the summary aloud"
  >{speaking ? "⏹ Stop" : `🔊 ${label}`}</button>
{/if}
