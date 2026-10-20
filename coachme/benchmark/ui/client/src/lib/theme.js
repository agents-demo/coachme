import { get, writable } from "svelte/store";

export const THEME_KEY = "coachme.benchmark.theme";
export const themeMode = writable("system");
export const isDark = writable(true);

function prefersDark() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function resolved(mode) {
  if (mode === "light") return false;
  if (mode === "dark") return true;
  return prefersDark();
}

export function applyTheme(mode) {
  const next = ["system", "light", "dark"].includes(mode) ? mode : "system";
  const dark = resolved(next);
  themeMode.set(next);
  isDark.set(dark);
  if (typeof document !== "undefined") {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
  }
  try {
    localStorage.setItem(THEME_KEY, next);
  } catch {
    /* storage may be disabled */
  }
}

export function toggleTheme() {
  applyTheme(get(isDark) ? "light" : "dark");
}

export function initTheme() {
  let saved = "system";
  try {
    saved = localStorage.getItem(THEME_KEY) || "system";
  } catch {
    saved = "system";
  }
  applyTheme(saved);
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  const onChange = () => {
    if (get(themeMode) === "system") applyTheme("system");
  };
  media.addEventListener?.("change", onChange);
  return () => media.removeEventListener?.("change", onChange);
}
