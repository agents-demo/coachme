# Android app (self-contained)

Native Android port of CoachMe — **no server, no openjiuwen**. It picks a video from the
phone, runs the measure → observe → coach pipeline **on-device**, calls the **DeepSeek API**
directly, and renders the same rubrics as the web app.

## Status

Feature-complete port: settings (tabs, secure key storage, readiness, backup/reset), report model +
store, sampling, measure (activity, subject/mechanics, `footwork_series`, maps), pose (skeleton,
angles, 3D, fast-hand, footwork), ball (ONNX YOLO + tracker), observe + coach passes, and the Compose
app (Sessions / New / Result, telestration, frame-step and speed controls, trim/GIF/vertical/reel/
share card, compare, diagnostics, Ask with voice).

Remaining: release setup (signing, store listing) and localization polish (accessibility strings,
resource migration, more locales). English and Chinese are supported with a Settings override;
report/QA language follows the selected language.

## Models (required)

The on-device models are **not committed** (large). Copy them into `app/src/main/assets/`:

```
copy runtime\data\models\pose_landmarker_lite.task  surfaces\android\app\src\main\assets\
copy runtime\data\models\ball.onnx                  surfaces\android\app\src\main\assets\
```

(pose comes from `integrations/pose.py`'s download; ball from `scripts/fetch_ball_model.py`.)

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
app/src/main/java/com/coachme/android/
├── MainActivity.kt
├── App.kt                      # Application (Hilt)
├── di/AppModule.kt
├── data/                       # Settings, Report, ReportStore
├── llm/                        # DeepSeekClient, Prompts, ReportTools
├── pipeline/                   # Pipeline (measure→observe→coach), Sampler, Metrics
└── ui/                         # Theme, Nav, screens (sessions / new / result)
```
