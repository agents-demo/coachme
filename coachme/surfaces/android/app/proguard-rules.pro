# kotlinx.serialization
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.**
-keepclassmembers class **$$serializer { *; }
-keepclasseswithmembers class * { kotlinx.serialization.KSerializer serializer(...); }

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**

# MediaPipe Tasks
-keep class com.google.mediapipe.** { *; }

# ONNX Runtime
-keep class ai.onnxruntime.** { *; }

# Our models
-keep class com.coachme.android.data.** { *; }
