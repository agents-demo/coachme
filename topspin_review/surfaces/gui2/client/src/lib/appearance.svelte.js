import { derived, get, writable } from "svelte/store";
import { zh, zhExtra, zhExtraMore, zhWeb, zhUi, zhWeb2, zhProfile, zhHome, zhNew, zhMisc, zhResult, zhBrand, zhMore2, zhFrames, zhTech, zhTech2, zhObs, zhCoach, zhDiag, zhDiag2, zhProgress, zhIssues, zhPositive } from "$lib/i18n/zh";

export const theme = writable("system");
export const palette = writable("indigo");
export const language = writable("system");
export const languageState = $state({ value: "system" });
export const sportMode = derived(palette, ($palette) => $palette === "sport");

function resolveLanguage(value) {
  if (value === "en" || value === "zh") return value;
  const browser = typeof navigator !== "undefined" ? navigator.language || "" : "";
  return browser.toLowerCase().startsWith("zh") ? "zh" : "en";
}

function canonical(text) {
  return text
    .replaceAll("–", "-")
    .replaceAll("—", "-")
    .replaceAll("−", "-")
    .replaceAll("\u00A0", " ")
    .replaceAll("\uFFFD", "-")
    .replace(/\s+/g, " ")
    .trim();
}

const all = { ...zh, ...zhExtra, ...zhExtraMore, ...zhWeb, ...zhUi, ...zhWeb2, ...zhProfile, ...zhHome, ...zhNew, ...zhMisc, ...zhResult, ...zhBrand, ...zhMore2, ...zhFrames, ...zhTech, ...zhTech2, ...zhObs, ...zhCoach, ...zhDiag, ...zhDiag2, ...zhProgress, ...zhIssues, ...zhPositive };
const zhLower = Object.fromEntries(Object.entries(all).map(([k, v]) => [k.toLowerCase(), v]));
const zhCanon = Object.fromEntries(Object.entries(all).map(([k, v]) => [canonical(k), v]));

const patterns = [
  [/^(\d+) sessions?$/, "$1 次训练"],
  [/^(\d+) issues?$/, "$1 个问题"],
  [/^(\d+) frames?$/, "$1 帧"],
  [/^(\d+) practice items?$/, "$1 个练习"],
  [/^(\d+) caveats?$/, "$1 个注意事项"],
  [/^(\d+) of (\d+) done$/, "已完成 $1 / $2"],
  [/^(\d+) of (\d+) steps done$/, "已完成 $1 / $2 步"],
  [/^(\d+) right-handed, (\d+) left-handed$/, "$1 次右手，$2 次左手"],
  [/^Last API test: (.+)$/, "上次 API 测试：$1"],
  [/^Failed: (.+)$/, "失败：$1"],
  [/^Next: (.+)$/, "下一步：$1"],
  [/^mean energy (.+)$/, "平均能量 $1"],
  [/^max (.+)\/s \(screen units - not a real speed\)$/, "最大 $1/秒（屏幕单位——非真实速度）"],
  [/^(\d+) px$/, "$1 像素"],
  [/^(\d+) per window$/, "每窗口 $1 帧"],
  [/^(\d+) windows$/, "$1 个窗口"],
  [/^All (\d+) checks passed$/, "全部 $1 项检查通过"],
  [/^(\d+) of (\d+) need attention$/, "$1 / $2 项需要处理"],
  [/^(\d+) reversals?$/, "$1 次反转"],
  [/^Rally · (\d+) contacts?$/, "回合 · $1 次触球"],
  [/^shoulder (.+), hip (.+)$/, "肩部 $1，髋部 $2"],
  [/^crouch (.+)$/, "下蹲 $1"],
  [/^knees (.+) \/ (.+)$/, "膝部 $1 / $2"],
  [/^side-to-side travel ([\d.]+) of the frame$/, "左右移动占画面 $1"],
  [/^side-to-side travel ([\d.]+) of the frame, ~(\d+) changes of direction$/, "左右移动占画面 $1，约 $2 次方向变化"],
  [/^max (.+)\/s \(screen units [—-] not a real speed\)$/, "最大 $1/秒（屏幕单位——非真实速度）"],
];

function translateOne(text) {
  const direct = all[text] ?? zhLower[text.toLowerCase()] ?? zhCanon[canonical(text)];
  if (direct) return direct;
  for (const [re, replacement] of patterns) {
    if (re.test(text)) return text.replace(re, replacement);
  }
  return text;
}

function translate(lang, text) {
  if (lang !== "zh" || !text) return text;
  if (text.includes("; ")) {
    const parts = text.split("; ");
    const out = parts.map(translateOne);
    if (out.some((v, i) => v !== parts[i])) return out.join("；");
  }
  return translateOne(text);
}

export const resolvedLanguage = derived(language, ($language) => resolveLanguage($language));
export function currentLanguage() {
  return resolveLanguage(languageState.value);
}

export function tr(text) {
  return translate(resolveLanguage(languageState.value), text);
}

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
  const savedLanguage = localStorage.getItem("topspin.lang");
  const storedLanguage =
    savedLanguage === "en" || savedLanguage === "zh" || savedLanguage === "system" ? savedLanguage : "system";

  theme.set(storedTheme);
  palette.set(storedPalette);
  language.set(storedLanguage);
  languageState.value = storedLanguage;
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

export function setLanguage(value) {
  language.set(value);
  languageState.value = value;
  try {
    localStorage.setItem("topspin.lang", value);
  } catch {}
}
