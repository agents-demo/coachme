import { derived, get, writable } from "svelte/store";

export const theme = writable("system");
export const palette = writable("indigo");
export const sportMode = derived(palette, ($palette) => $palette === "sport");

let mediaQuery = null;

function systemPrefersLight() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: light)").matches;
}

export function applyTheme(value) {
  if (typeof document === "undefined") return;
  const resolved = value === "system" ? (systemPrefersLight() ? "light" : "dark") : value;
  document.documentElement.dataset.theme = resolved;
  document.documentElement.style.colorScheme = resolved;
}

export function applyPalette(value) {
  if (typeof document === "undefined") return;
  if (value === "sport") document.documentElement.dataset.sport = "";
  else delete document.documentElement.dataset.sport;
}

export function initAppearance() {
  if (typeof window === "undefined") return;
  const savedTheme = localStorage.getItem("topspin.theme");
  const storedTheme =
    savedTheme === "light" || savedTheme === "dark" || savedTheme === "system" ? savedTheme : "system";
  const savedPalette = localStorage.getItem("topspin.palette");
  const legacySport = localStorage.getItem("topspin.sport") === "true";
  const storedPalette =
    savedPalette === "sport" || savedPalette === "indigo" ? savedPalette : legacySport ? "sport" : "indigo";

  theme.set(storedTheme);
  palette.set(storedPalette);
  applyTheme(storedTheme);
  applyPalette(storedPalette);

  mediaQuery = window.matchMedia("(prefers-color-scheme: light)");
  mediaQuery.addEventListener("change", () => {
    if (get(theme) === "system") applyTheme("system");
  });
}

export function setTheme(value) {
  theme.set(value);
  try {
    localStorage.setItem("topspin.theme", value);
  } catch {}
  applyTheme(value);
}

export function setPalette(value) {
  palette.set(value);
  try {
    localStorage.setItem("topspin.palette", value);
  } catch {}
  applyPalette(value);
}
