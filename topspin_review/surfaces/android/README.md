# Android app (self-contained)

Native Android port of Topspin Review — **no server, no openjiuwen**. It picks a video from the
phone, runs the measure → observe → coach pipeline **on-device**, calls the **DeepSeek API**
directly, and renders the same rubrics as the web app.

See the full plan: [`docs/ANDROID_PLAN.md`](../../docs/ANDROID_PLAN.md) (appendices A–S).

## Status

**P0–P2 scaffold** — project setup, settings, DeepSeek client, report model + store, sampling, the
**measure** stage (activity + subject region/track + mechanics + `footwork_series` + motion/position
maps), the observe + coach passes, and a Compose shell (Sessions / New / Result with Analysis maps +
side-to-side chart, Observations, Coaching+Ask, Diagnostics). Not yet compiled; **pose (MediaPipe)**
and **ball (ONNX)** and the remaining UI (player/telestration, trim/reel/card, compare, moments) are
the next phases.

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
