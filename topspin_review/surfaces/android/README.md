# Android app (self-contained)

Native Android port of Topspin Review — **no server, no openjiuwen**. It picks a video from the
phone, runs the measure → observe → coach pipeline **on-device**, calls the **DeepSeek API**
directly, and renders the same rubrics as the web app.

See the full plan: [`docs/ANDROID_PLAN.md`](../../docs/ANDROID_PLAN.md) (appendices A–S).

## Status

**P0–P4 scaffold** — project setup, settings, DeepSeek client, report model + store, sampling, the
full **measure** stage (activity + subject/mechanics + `footwork_series` + motion/position maps),
**pose** (MediaPipe PoseLandmarker: skeleton, angles, 3D, fast-hand, footwork), **ball** (ONNX YOLO +
tracker: path, stats, segments, 3D trajectory), the observe + coach passes, and a Compose shell
(Sessions / New / Result with Analysis showing maps + charts + pose + tracked object, Observations,
Coaching + Ask, Diagnostics). Not yet compiled; **P5/P6** (player + telestration, trim/GIF/reel/card,
compare, key moments/clips, full Diagnostics, readiness, voice, localization) remain.

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
app/src/main/java/com/topspinreview/android/
├── MainActivity.kt
├── App.kt                      # Application (Hilt)
├── di/AppModule.kt
├── data/                       # Settings, Report, ReportStore
├── llm/                        # DeepSeekClient, Prompts, ReportTools
├── pipeline/                   # Pipeline (measure→observe→coach), Sampler, Metrics
└── ui/                         # Theme, Nav, screens (sessions / new / result)
```
