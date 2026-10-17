import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.serialization")
    id("org.jetbrains.kotlin.plugin.compose")
    id("com.google.dagger.hilt.android")
    id("kotlin-kapt")
}

// Optional build-time defaults (API key etc.) from a gitignored secret.properties.
val secretProps = Properties().apply {
    val f = rootProject.file("secret.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}
fun secret(k: String) = secretProps.getProperty(k, "")

android {
    namespace = "com.topspinreview.android"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.topspinreview.android"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
        ndk { abiFilters += listOf("arm64-v8a", "armeabi-v7a") }

        buildConfigField("String", "DEFAULT_API_BASE", "\"${secret("apiBase")}\"")
        buildConfigField("String", "DEFAULT_TEXT_MODEL", "\"${secret("textModel")}\"")
        buildConfigField("String", "DEFAULT_VISION_MODEL", "\"${secret("visionModel")}\"")
    }

    buildTypes {
        debug {
            buildConfigField("String", "DEFAULT_API_KEY", "\"${secret("apiKey")}\"")
        }
        release {
            isMinifyEnabled = true
            buildConfigField("String", "DEFAULT_API_KEY", "\"\"")
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    buildFeatures { compose = true; buildConfig = true }
    packaging {
        resources.excludes += "/META-INF/{AL2.0,LGPL2.1}"
        // youtubedl-android reads its bundled python/ffmpeg out of lib/<abi> at runtime, so the
        // native libraries must be extracted to disk (see its README: android:extractNativeLibs).
        jniLibs { useLegacyPackaging = true }
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.09.03")
    implementation(composeBom)
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.activity:activity-compose:1.9.3")
    implementation("androidx.navigation:navigation-compose:2.8.4")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.2")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.2")
    implementation("androidx.core:core-ktx:1.13.1")

    implementation("androidx.datastore:datastore-preferences:1.1.7")
    implementation("androidx.security:security-crypto:1.0.0")
    implementation("androidx.work:work-runtime-ktx:2.9.0")

    // Media (playback + cutting)
    implementation("androidx.media3:media3-exoplayer:1.5.1")
    implementation("androidx.media3:media3-ui:1.5.1")
    implementation("androidx.media3:media3-transformer:1.5.1")
    implementation("androidx.media3:media3-effect:1.5.1")

    // HTTP + JSON
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.3")
    implementation("io.coil-kt:coil-compose:2.6.0")

    // Analyze a YouTube (or other yt-dlp-supported) link (bundles yt-dlp + ffmpeg).
    implementation("io.github.junkfood02.youtubedl-android:library:0.18.1")
    implementation("io.github.junkfood02.youtubedl-android:ffmpeg:0.18.1")

    // On-device ML (versions chosen for Android 16 KB page-size alignment)
    implementation("com.google.mediapipe:tasks-vision:0.10.35")
    implementation("com.microsoft.onnxruntime:onnxruntime-android:1.31.0")

    implementation("com.google.dagger:hilt-android:2.51.1")
    kapt("com.google.dagger:hilt-android-compiler:2.51.1")
    implementation("androidx.hilt:hilt-navigation-compose:1.2.0")

    testImplementation("junit:junit:4.13.2")
}
