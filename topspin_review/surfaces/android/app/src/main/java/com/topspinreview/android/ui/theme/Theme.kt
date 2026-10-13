package com.topspinreview.android.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Design tokens from the web app (docs/ANDROID_PLAN.md · Appendix H).
val Accent = Color(0xFF4F46E5)
val Accent2 = Color(0xFF818CF8)
val Good = Color(0xFF34D399)
val Bad = Color(0xFFFB7185)
val Warn = Color(0xFFFBBF24)

private val DarkScheme = darkColorScheme(
    primary = Accent, secondary = Accent2, background = Color(0xFF0B0B0F),
    surface = Color(0xFF15151D), onBackground = Color(0xFFECECF2), onSurface = Color(0xFFECECF2),
    error = Bad,
)
private val LightScheme = lightColorScheme(
    primary = Accent, secondary = Accent2, background = Color(0xFFFBFBFD),
    surface = Color(0xFFF4F4F8), onBackground = Color(0xFF12121A), onSurface = Color(0xFF12121A),
    error = Bad,
)

@Composable
fun TopspinTheme(darkTheme: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = if (darkTheme) DarkScheme else LightScheme, content = content)
}
