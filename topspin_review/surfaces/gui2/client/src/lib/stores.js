import { writable } from "svelte/store";

/** Whether the UI is in sport mode (orange palette + image-forward grid). */
export const sportMode = writable(false);
