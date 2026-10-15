package com.topspinreview.android.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.topspinreview.android.ui.theme.Accent
import com.topspinreview.android.ui.theme.Accent2
import com.topspinreview.android.ui.theme.Bad
import com.topspinreview.android.ui.theme.Good
import com.topspinreview.android.ui.theme.SpaceGrotesk
import com.topspinreview.android.ui.theme.Warn

/** The brand gradient used for hero text and logos (`from-accent to-accent2`). */
fun heroBrush(): Brush = Brush.linearGradient(listOf(Accent, Accent2))

/** gui2's control radius: `rounded-lg` (8 dp). */
private val ControlShape = RoundedCornerShape(8.dp)

/** Media radius: `rounded-[14px]` with a 2 px border, matching the web app. */
private val MediaShape = RoundedCornerShape(14.dp)

/** One-pixel hairline in the border colour. */
@Composable
fun DividerLine(modifier: Modifier = Modifier) {
    Box(modifier.fillMaxWidth().height(1.dp).background(MaterialTheme.colorScheme.outline))
}

/** A plain, muted note (gui2's `text-sm text-muted` empty/placeholder copy). */
@Composable
fun MutedNote(text: String, modifier: Modifier = Modifier) {
    Text(
        text,
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        modifier = modifier.padding(vertical = 8.dp),
    )
}

/** The rounded, bordered panel that everything sits in (gui2 `.card`). */
@Composable
fun TspCard(
    modifier: Modifier = Modifier,
    raised: Boolean = false,
    padding: PaddingValues = PaddingValues(16.dp),
    horizontalAlignment: Alignment.Horizontal = Alignment.Start,
    verticalArrangement: Arrangement.Vertical = Arrangement.Top,
    content: @Composable ColumnScope.() -> Unit,
) {
    Surface(
        modifier = modifier,
        shape = MaterialTheme.shapes.large,
        color = if (raised) MaterialTheme.colorScheme.surfaceVariant else MaterialTheme.colorScheme.surface,
        border = BorderStroke(2.dp, MaterialTheme.colorScheme.outline),
    ) {
        Column(
            Modifier.fillMaxWidth().padding(padding),
            horizontalAlignment = horizontalAlignment,
            verticalArrangement = verticalArrangement,
            content = content,
        )
    }
}

/** gui2's uppercase, wide-tracked section label. */
@Composable
fun SectionLabel(text: String, modifier: Modifier = Modifier, color: Color? = null) {
    Text(
        text = text.uppercase(),
        modifier = modifier,
        fontFamily = SpaceGrotesk,
        fontWeight = FontWeight.Bold,
        fontSize = 12.sp,
        letterSpacing = 1.4.sp,
        color = color ?: MaterialTheme.colorScheme.onSurfaceVariant,
    )
}

/** A small outlined pill (the hero eyebrow / micro badges). */
@Composable
fun EyebrowPill(text: String, modifier: Modifier = Modifier) {
    Box(
        modifier
            .clip(CircleShape)
            .background(MaterialTheme.colorScheme.surface.copy(alpha = 0.5f))
            .border(1.dp, MaterialTheme.colorScheme.outline, CircleShape)
            .padding(horizontal = 12.dp, vertical = 5.dp),
    ) {
        Text(
            text.uppercase(),
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.SemiBold,
            letterSpacing = 1.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

/** A nav pill for the header (gui2's `rounded-full px-4 py-1.5` links). */
@Composable
fun PillNav(text: String, selected: Boolean = false, onClick: () -> Unit) {
    Box(
        Modifier
            .clip(CircleShape)
            .background(if (selected) MaterialTheme.colorScheme.surface else Color.Transparent)
            .clickable { onClick() }
            .padding(horizontal = 14.dp, vertical = 7.dp),
    ) {
        Text(
            text,
            style = MaterialTheme.typography.labelLarge,
            color = if (selected) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

/** A tinted or outlined capsule chip, for metadata and tones. */
@Composable
fun MetaChip(
    text: String,
    modifier: Modifier = Modifier,
    color: Color = MaterialTheme.colorScheme.onSurfaceVariant,
    border: Color = MaterialTheme.colorScheme.outline,
    background: Color = Color.Transparent,
    borderWidth: Dp = 1.dp,
) {
    Box(
        modifier
            .clip(CircleShape)
            .background(background)
            .border(borderWidth, border, CircleShape)
            .padding(horizontal = 10.dp, vertical = 4.dp),
    ) {
        Text(text, style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Medium, color = color)
    }
}

/** A monospace time chip (`font-mono text-accent2`), like gui2's timestamp buttons. */
@Composable
fun TimeChip(text: String, modifier: Modifier = Modifier) {
    Box(
        modifier
            .clip(CircleShape)
            .border(2.dp, MaterialTheme.colorScheme.outline, CircleShape)
            .padding(horizontal = 10.dp, vertical = 4.dp),
    ) {
        Text(
            text,
            fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace,
            fontSize = 12.sp,
            color = Accent2,
        )
    }
}

/** Centered stat tile (Sessions / Open issues). */
@Composable
fun StatTile(
    value: String,
    label: String,
    modifier: Modifier = Modifier,
    valueColor: Color? = null,
) {
    TspCard(
        modifier = modifier,
        padding = PaddingValues(vertical = 16.dp, horizontal = 12.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            value,
            style = MaterialTheme.typography.headlineMedium,
            color = valueColor ?: MaterialTheme.colorScheme.onSurface,
        )
        Spacer(Modifier.height(2.dp))
        Text(
            label.uppercase(),
            style = MaterialTheme.typography.labelSmall,
            letterSpacing = 1.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

/** An image/artifact with gui2's `rounded-[14px] border-2 border-line` treatment. */
@Composable
fun MediaImage(model: Any?, contentDescription: String?, modifier: Modifier = Modifier) {
    AsyncImage(
        model = model,
        contentDescription = contentDescription,
        contentScale = ContentScale.FillWidth,
        modifier = modifier
            .fillMaxWidth()
            .clip(MediaShape)
            .border(2.dp, MaterialTheme.colorScheme.outline, MediaShape),
    )
}

/** The big gradient hero at the top of a screen, with soft glow blobs. */
@Composable
fun HeroCard(
    modifier: Modifier = Modifier,
    eyebrow: String? = null,
    title: @Composable () -> Unit,
    subtitle: String? = null,
) {
    val shape = MaterialTheme.shapes.extraLarge
    Box(
        modifier
            .fillMaxWidth()
            .clip(shape)
            .background(MaterialTheme.colorScheme.surface)
            .border(2.dp, MaterialTheme.colorScheme.outline, shape),
    ) {
        Box(
            Modifier.matchParentSize().background(
                Brush.linearGradient(
                    listOf(Accent.copy(alpha = 0.20f), Color.Transparent, Accent2.copy(alpha = 0.18f)),
                ),
            ),
        )
        Box(
            Modifier.align(Alignment.TopEnd).offset(x = 46.dp, y = (-46).dp).size(190.dp)
                .background(Brush.radialGradient(listOf(Accent.copy(alpha = 0.38f), Color.Transparent)), CircleShape),
        )
        Box(
            Modifier.align(Alignment.BottomStart).offset(x = (-40).dp, y = 44.dp).size(190.dp)
                .background(Brush.radialGradient(listOf(Accent2.copy(alpha = 0.32f), Color.Transparent)), CircleShape),
        )
        Column(Modifier.fillMaxWidth().padding(22.dp)) {
            if (eyebrow != null) {
                EyebrowPill(eyebrow)
                Spacer(Modifier.height(12.dp))
            }
            title()
            if (subtitle != null) {
                Spacer(Modifier.height(8.dp))
                Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

/** The brand mark: a gradient tile with the ping-pong emoji. */
@Composable
fun LogoBadge(modifier: Modifier = Modifier, size: Dp = 30.dp) {
    Box(
        modifier.size(size).clip(RoundedCornerShape(size / 3)).background(heroBrush()),
        contentAlignment = Alignment.Center,
    ) {
        Text("🏓", fontSize = (size.value * 0.5f).sp)
    }
}

/** A custom top bar matching the web header (logo, title, pill nav, actions). */
@Composable
fun TspTopBar(
    modifier: Modifier = Modifier,
    title: String? = null,
    titleContent: (@Composable RowScope.() -> Unit)? = null,
    onBack: (() -> Unit)? = null,
    actions: @Composable RowScope.() -> Unit = {},
) {
    Column(modifier.fillMaxWidth().background(MaterialTheme.colorScheme.background).statusBarsPadding()) {
        Row(
            Modifier.fillMaxWidth().height(60.dp).padding(horizontal = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            if (onBack != null) {
                IconButton(onClick = onBack) {
                    Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = MaterialTheme.colorScheme.onSurface)
                }
                Spacer(Modifier.width(4.dp))
            } else {
                LogoBadge(Modifier.padding(horizontal = 8.dp))
            }
            if (titleContent != null) {
                // The content supplies its own flexible width; don't add a competing spacer.
                titleContent()
            } else {
                if (title != null) Text(title, style = MaterialTheme.typography.titleLarge, maxLines = 1)
                Spacer(Modifier.weight(1f))
            }
            actions()
        }
        DividerLine()
    }
}

/** gui2's underline tab bar, horizontally scrollable, with a hint line below. */
@Composable
fun TspTabBar(
    items: List<String>,
    selectedIndex: Int,
    onSelect: (Int) -> Unit,
    modifier: Modifier = Modifier,
    hint: String? = null,
) {
    Column(modifier.fillMaxWidth()) {
        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())) {
            items.forEachIndexed { i, label ->
                val selected = i == selectedIndex
                Column(
                    Modifier.clickable { onSelect(i) }.width(IntrinsicSize.Max),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Text(
                        label,
                        maxLines = 1,
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = if (selected) FontWeight.Bold else FontWeight.Medium,
                        color = if (selected) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp),
                    )
                    Box(
                        Modifier.fillMaxWidth().height(3.dp).clip(RoundedCornerShape(3.dp))
                            .background(if (selected) Accent else Color.Transparent),
                    )
                }
            }
        }
        DividerLine()
        if (hint != null) {
            Text(
                hint,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            )
        }
    }
}

/**
 * A Material 3 single-choice segmented control for a few short sub-sections. Shares the full
 * width equally and the segments shrink to fit — no scrolling.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TspSegmented(
    options: List<String>,
    selectedIndex: Int,
    onSelect: (Int) -> Unit,
    modifier: Modifier = Modifier,
) {
    if (options.size <= 1) return
    SingleChoiceSegmentedButtonRow(modifier.fillMaxWidth()) {
        options.forEachIndexed { i, label ->
            SegmentedButton(
                selected = i == selectedIndex,
                onClick = { onSelect(i) },
                shape = SegmentedButtonDefaults.itemShape(index = i, count = options.size),
                modifier = Modifier.height(32.dp),
            ) {
                Text(
                    label,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    style = MaterialTheme.typography.labelMedium,
                )
            }
        }
    }
}

/** Filled accent button (gui2 `rounded-lg bg-accent`). */
@Composable
fun PrimaryButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    icon: (@Composable () -> Unit)? = null,
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = modifier.height(48.dp),
        shape = ControlShape,
        colors = ButtonDefaults.buttonColors(
            containerColor = Accent,
            contentColor = Color.White,
            disabledContainerColor = Accent.copy(alpha = 0.35f),
            disabledContentColor = Color.White.copy(alpha = 0.7f),
        ),
    ) {
        if (icon != null) {
            icon()
            Spacer(Modifier.width(8.dp))
        }
        Text(text, style = MaterialTheme.typography.labelLarge)
    }
}

/** Outlined, low-emphasis button (gui2 `rounded-lg border-2 border-line`). */
@Composable
fun GhostButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
) {
    OutlinedButton(
        onClick = onClick,
        enabled = enabled,
        modifier = modifier.height(46.dp),
        shape = ControlShape,
        border = BorderStroke(2.dp, MaterialTheme.colorScheme.outline),
        colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.onSurface),
    ) {
        Text(text, style = MaterialTheme.typography.labelLarge)
    }
}

/** A gradient progress bar (`from-accent to-accent2`), like gui2's live feed. */
@Composable
fun GradientProgress(fraction: Float, modifier: Modifier = Modifier, height: Dp = 8.dp) {
    Box(
        modifier.fillMaxWidth().height(height).clip(RoundedCornerShape(height / 2)).background(MaterialTheme.colorScheme.surfaceVariant),
    ) {
        Box(
            Modifier
                .fillMaxWidth(fraction.coerceIn(0f, 1f))
                .height(height)
                .clip(RoundedCornerShape(height / 2))
                .background(heroBrush()),
        )
    }
}
