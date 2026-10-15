package com.topspinreview.android.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

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

@Composable
fun TopspinTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkScheme else LightScheme,
        typography = TspTypography,
        shapes = TspShapes,
        content = content,
    )
}
