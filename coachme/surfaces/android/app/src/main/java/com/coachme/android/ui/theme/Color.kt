package com.coachme.android.ui.theme

import androidx.compose.ui.graphics.Color

// ---------------------------------------------------------------------------
// Brand accents — the exact gui2 Tailwind palette (tailwind.config.cjs).
// ---------------------------------------------------------------------------
val Accent = Color(0xFF4F46E5)
val Accent2 = Color(0xFF818CF8)
val Good = Color(0xFF34D399)
val Bad = Color(0xFFFB7185)
val Warn = Color(0xFFFBBF24)

// ---------------------------------------------------------------------------
// Surfaces — dark is the default (gui2 app.css :root), light overrides it.
// ---------------------------------------------------------------------------
val InkDark = Color(0xFF0B0B0F)
val PanelDark = Color(0xFF15151D)
val Panel2Dark = Color(0xFF1C1C27)
val LineDark = Color(0xFF26262F)
val TextDark = Color(0xFFECECF2)
val MutedDark = Color(0xFF9CA3AF)

val InkLight = Color(0xFFFBFBFD)
val PanelLight = Color(0xFFF4F4F8)
val Panel2Light = Color(0xFFEAEAF3)
val LineLight = Color(0xFFE2E2EC)
val TextLight = Color(0xFF12121A)
val MutedLight = Color(0xFF64748B)

// Container tints (for chips / selected states) — indigo-tinted like the web hero.
val AccentContainerDark = Color(0xFF27235C)
val AccentContainerLight = Color(0xFFE0E7FF)
val Accent2ContainerDark = Color(0xFF2A2C4A)
val Accent2ContainerLight = Color(0xFFE7E9FF)
val GoodContainerDark = Color(0xFF113B2F)
val GoodContainerLight = Color(0xFFD7F5E9)

// The annotation ink used by the telestration tool.
val Telestration = Color(0xFFF97316)

// ---------------------------------------------------------------------------
// Sport mode palette — kinetic orange replaces indigo for a more athletic feel.
// ---------------------------------------------------------------------------
val SportAccent = Color(0xFFF97316)          // vivid orange (same as Telestration)
val SportAccent2 = Color(0xFFFB923C)         // orange/400, lighter companion
val SportAccentContainerDark = Color(0xFF431407)
val SportAccentContainerLight = Color(0xFFFFEDD5)
val SportAccent2ContainerDark = Color(0xFF3B1A0A)
val SportAccent2ContainerLight = Color(0xFFFEF3C7)
