# Android app (self-contained)

Native Android port of Topspin Review — **no server, no openjiuwen**. It picks a video from the
phone, runs the measure → observe → coach pipeline **on-device**, calls the **DeepSeek API**
directly, and renders the same rubrics as the web app.

See the full plan: [`docs/ANDROID_PLAN.md`](../../docs/ANDROID_PLAN.md) (appendices A–S).

## Status

**P0/P1 scaffold** — project setup, settings, DeepSeek client, report model + store, a first
pipeline slice (sampling → metrics stub → vision → report), and a Compose shell (Sessions / New /
Result). Not yet compiled; the CV (pose, ball) and the full UI are the next phases.

## Build

Open `surfaces/android` in Android Studio (Giraffe+), or from the repo root:

```
cd surfaces/android
./gradlew :app:assembleDebug
```

Requires: JDK 17, Android SDK (platform 35, build-tools 34/36). Set `sdk.dir` in `local.properties`
(or `ANDROID_HOME`).

## Configure

First run → **Settings**: `API_BASE`, `API_KEY`, `MODEL_NAME`, `VISION_MODEL_NAME` (same values as
`.env`). Use **Test connection**.

## Layout

```
app/src/main/java/com/topspinreview/android/
├── MainActivity.kt
├── App.kt                      # Application (Hilt)
├── di/AppModule.kt
├── data/                       # Settings, Report, ReportStore
├── llm/                        # DeepSeekClient, Prompts, ReportTools
├── pipeline/                   # Pipeline (measure→observe→coach), Sampler, Metrics
└── ui/                         # Theme, Nav, screens (sessions / new / result)
```
