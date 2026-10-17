package com.topspinreview.android.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

/**
 * The gui2 palette mapped onto Material 3 roles:
 * background = ink, surface = panel, surfaceVariant = raised panel,
 * outline = line, onSurfaceVariant = muted, primary = accent.
 */
private val DarkScheme = darkColorScheme(
    primary = Accent,
    onPrimary = Color.White,
    primaryContainer = AccentContainerDark,
    onPrimaryContainer = Color(0xFFDDE1FF),
    secondary = Accent2,
    onSecondary = Color.White,
    secondaryContainer = Accent2ContainerDark,
    onSecondaryContainer = Color(0xFFE0E3FF),
    tertiary = Good,
    onTertiary = InkDark,
    tertiaryContainer = GoodContainerDark,
    onTertiaryContainer = Color(0xFFB6F0DC),
    error = Bad,
    onError = Color.White,
    errorContainer = Color(0xFF4C1D24),
    onErrorContainer = Color(0xFFFFD9DE),
    background = InkDark,
    onBackground = TextDark,
    surface = PanelDark,
    onSurface = TextDark,
    surfaceVariant = Panel2Dark,
    onSurfaceVariant = MutedDark,
    inverseSurface = TextDark,
    inverseOnSurface = InkDark,
    outline = LineDark,
    outlineVariant = LineDark,
    scrim = Color(0xCC000000),
    surfaceTint = Accent,
)

private val LightScheme = lightColorScheme(
    primary = Accent,
    onPrimary = Color.White,
    primaryContainer = AccentContainerLight,
    onPrimaryContainer = Color(0xFF1E1B4B),
    secondary = Accent2,
    onSecondary = Color.White,
    secondaryContainer = Accent2ContainerLight,
    onSecondaryContainer = Color(0xFF23264D),
    tertiary = Good,
    onTertiary = Color.White,
    tertiaryContainer = GoodContainerLight,
    onTertiaryContainer = Color(0xFF075040),
    error = Bad,
    onError = Color.White,
    errorContainer = Color(0xFFFFD9DE),
    onErrorContainer = Color(0xFF7A1626),
    background = InkLight,
    onBackground = TextLight,
    surface = PanelLight,
    onSurface = TextLight,
    surfaceVariant = Panel2Light,
    onSurfaceVariant = MutedLight,
    inverseSurface = TextLight,
    inverseOnSurface = InkLight,
    outline = LineLight,
    outlineVariant = LineLight,
    scrim = Color(0x33000000),
    surfaceTint = Accent,
)

/**
 * Sport mode: same surface palette, orange primary replaces indigo.
 * Feels more kinetic and athletic than the default SaaS-adjacent indigo.
 */
private val SportDarkScheme = darkColorScheme(
    primary = SportAccent,
    onPrimary = Color.White,
    primaryContainer = SportAccentContainerDark,
    onPrimaryContainer = Color(0xFFFFDDBA),
    secondary = SportAccent2,
    onSecondary = Color.White,
    secondaryContainer = SportAccent2ContainerDark,
    onSecondaryContainer = Color(0xFFFEF3C7),
    tertiary = Good,
    onTertiary = InkDark,
    tertiaryContainer = GoodContainerDark,
    onTertiaryContainer = Color(0xFFB6F0DC),
    error = Bad,
    onError = Color.White,
    errorContainer = Color(0xFF4C1D24),
    onErrorContainer = Color(0xFFFFD9DE),
    background = InkDark,
    onBackground = TextDark,
    surface = PanelDark,
    onSurface = TextDark,
    surfaceVariant = Panel2Dark,
    onSurfaceVariant = MutedDark,
    inverseSurface = TextDark,
    inverseOnSurface = InkDark,
    outline = LineDark,
    outlineVariant = LineDark,
    scrim = Color(0xCC000000),
    surfaceTint = SportAccent,
)

private val SportLightScheme = lightColorScheme(
    primary = SportAccent,
    onPrimary = Color.White,
    primaryContainer = SportAccentContainerLight,
    onPrimaryContainer = Color(0xFF431407),
    secondary = SportAccent2,
    onSecondary = Color.White,
    secondaryContainer = SportAccent2ContainerLight,
    onSecondaryContainer = Color(0xFF3B1A0A),
    tertiary = Good,
    onTertiary = Color.White,
    tertiaryContainer = GoodContainerLight,
    onTertiaryContainer = Color(0xFF075040),
    error = Bad,
    onError = Color.White,
    errorContainer = Color(0xFFFFD9DE),
    onErrorContainer = Color(0xFF7A1626),
    background = InkLight,
    onBackground = TextLight,
    surface = PanelLight,
    onSurface = TextLight,
    surfaceVariant = Panel2Light,
    onSurfaceVariant = MutedLight,
    inverseSurface = TextLight,
    inverseOnSurface = InkLight,
    outline = LineLight,
    outlineVariant = LineLight,
    scrim = Color(0x33000000),
    surfaceTint = SportAccent,
)

@Composable
fun TopspinTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    style: String = "sport",
    content: @Composable () -> Unit,
) {
    val context = LocalContext.current
    val colorScheme = when {
        style == "dynamic" && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val scheme = if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
            val line = if (darkTheme) LineDark else LineLight
            scheme.copy(outline = line, outlineVariant = line)
        }
        style == "indigo" -> if (darkTheme) DarkScheme else LightScheme
        else -> if (darkTheme) SportDarkScheme else SportLightScheme
    }
    MaterialTheme(
        colorScheme = colorScheme,
        typography = TspTypography,
        shapes = TspShapes,
        content = content,
    )
}
