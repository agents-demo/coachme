<script>
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { base } from "$app/paths";

  onMount(() => goto(`${base}/progress?tab=compare`, { replaceState: true }));
</script>
