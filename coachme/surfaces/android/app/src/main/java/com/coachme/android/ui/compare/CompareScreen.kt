package com.coachme.android.ui.compare

import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import com.coachme.android.ui.components.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.delay
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import com.coachme.android.data.Report
import com.coachme.android.data.ReportStore
import com.coachme.android.domain.Compare
import com.coachme.android.ui.components.GhostButton
import com.coachme.android.ui.components.HeroCard
import com.coachme.android.ui.components.PrimaryButton
import com.coachme.android.ui.components.SectionLabel
import com.coachme.android.ui.components.MutedNote
import com.coachme.android.ui.components.CoachCard
import com.coachme.android.ui.components.CoachSegmented
import com.coachme.android.ui.components.CoachTopBar
import com.coachme.android.ui.i18n.tr
import com.coachme.android.ui.theme.Accent2
import com.coachme.android.ui.theme.Bad
import com.coachme.android.ui.theme.Good
import com.coachme.android.ui.theme.Warn
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class CompareViewModel @Inject constructor(private val store: ReportStore) : ViewModel() {
    private val _reports = MutableStateFlow<List<Report>>(emptyList())
    val reports = _reports.asStateFlow()
    private val _diff = MutableStateFlow<Compare.Diff?>(null)
    val diff = _diff.asStateFlow()

    init { viewModelScope.launch { _reports.value = store.list() } }
    fun compare(older: Report, newer: Report) { _diff.value = Compare.compare(older, newer) }
}

@Composable
fun CompareScreen(onBack: () -> Unit, vm: CompareViewModel = hiltViewModel()) {
    val reports by vm.reports.collectAsStateWithLifecycle()
    val diff by vm.diff.collectAsStateWithLifecycle()
    var a by remember { mutableStateOf<Report?>(null) }
    var b by remember { mutableStateOf<Report?>(null) }

    var tab by remember { mutableStateOf(0) }
    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = { CoachTopBar(title = "Progress", onBack = onBack) },
    ) { pad ->
        Column(Modifier.fillMaxSize().padding(pad)) {
            CoachSegmented(
                options = listOf("Trends", "Compare"),
                selectedIndex = tab,
                onSelect = { tab = it },
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
            )
            if (tab == 0) {
                TrendsContent(reports)
            } else {
        Column(
            Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            PickerCard("Earlier", reports, a) { a = it }
            PickerCard("Later", reports, b) { b = it }

            PrimaryButton(
                "Compare",
                { val x = a; val y = b; if (x != null && y != null) vm.compare(x, y) },
                Modifier.fillMaxWidth(),
                enabled = a != null && b != null && a?.stem != b?.stem,
            )

            val ra = a; val rb = b
            if (ra != null && rb != null && ra.source.isNotBlank() && rb.source.isNotBlank()) {
                CoachCard(modifier = Modifier.fillMaxWidth()) {
                    SectionLabel("Clips")
                    Spacer(Modifier.height(10.dp))
                    ComparePlayers(ra.source, rb.source)
                }
            }

            diff?.let { d ->
                CoachCard(modifier = Modifier.fillMaxWidth()) {
                    SectionLabel("What changed")
                    Spacer(Modifier.height(8.dp))
                    Text(
                        d.text.ifBlank { "No comparable change." },
                        style = MaterialTheme.typography.bodyLarge,
                    )
                }
                if (d.metricDeltas.isNotEmpty()) {
                    CoachCard(modifier = Modifier.fillMaxWidth()) {
                        SectionLabel("Metric deltas (later − earlier)")
                        Spacer(Modifier.height(10.dp))
                        d.metricDeltas.forEach { (k, v) ->
                            Row(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                                Text(k, Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium)
                                val tone = when {
                                    v > 0 -> Good
                                    v < 0 -> Bad
                                    else -> MaterialTheme.colorScheme.onSurfaceVariant
                                }
                                Text(
                                    "${if (v > 0) "+" else ""}${"%.3f".format(v)}",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = tone,
                                )
                            }
                        }
                    }
                }
            }
        }
            }
        }
    }
}

@Composable
private fun TrendsContent(reports: List<Report>) {
    val counts = remember(reports) {
        val m = mutableMapOf<String, Int>()
        for (r in reports) for (i in r.issues) {
            val k = i.issue.trim().take(120)
            if (k.isNotEmpty()) m[k] = (m[k] ?: 0) + 1
        }
        m.entries.filter { it.value >= 2 }.sortedByDescending { it.value }.take(8).map { it.key to it.value }
    }
    val drills = remember(reports) { reports.sumOf { it.drills.size } }
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        CoachCard(modifier = Modifier.fillMaxWidth()) {
            SectionLabel("Trends")
            if (counts.isEmpty()) {
                Spacer(Modifier.height(6.dp))
                MutedNote("No recurring issues yet — analyze a few more sessions.")
            } else {
                Spacer(Modifier.height(10.dp))
                val maxCount = counts.first().second
                counts.forEach { (text, count) ->
                    Row(
                        Modifier.fillMaxWidth().padding(vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Box(
                            Modifier.weight(1f).height(18.dp).clip(MaterialTheme.shapes.small)
                                .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.1f)),
                        ) {
                            Box(
                                Modifier.fillMaxWidth(count.toFloat() / maxCount).fillMaxHeight()
                                    .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.35f)),
                            )
                            Text(
                                text,
                                style = MaterialTheme.typography.labelSmall,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                                modifier = Modifier.align(Alignment.CenterStart).padding(horizontal = 6.dp),
                            )
                        }
                        Text("$count×", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
            if (drills > 0) {
                Spacer(Modifier.height(8.dp))
                Text(
                    "$drills ${tr("total drills across all sessions")}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun ComparePlayers(sourceA: String, sourceB: String) {
    val ctx = LocalContext.current
    fun uriOf(s: String): Uri =
        if (s.startsWith("content:") || s.startsWith("http")) Uri.parse(s) else Uri.fromFile(java.io.File(s))

    val exoA = remember {
        androidx.media3.exoplayer.ExoPlayer.Builder(ctx).build().apply {
            setMediaItem(androidx.media3.common.MediaItem.fromUri(uriOf(sourceA)))
            prepare()
            playWhenReady = false
        }
    }
    val exoB = remember {
        androidx.media3.exoplayer.ExoPlayer.Builder(ctx).build().apply {
            setMediaItem(androidx.media3.common.MediaItem.fromUri(uriOf(sourceB)))
            prepare()
            playWhenReady = false
        }
    }
    DisposableEffect(Unit) { onDispose { exoA.release(); exoB.release() } }

    var split by remember { mutableFloatStateOf(0.5f) }
    var playing by remember { mutableStateOf(false) }
    var progress by remember { mutableFloatStateOf(0f) }

    fun seekBoth(fraction: Float) {
        val f = fraction.coerceIn(0f, 1f)
        progress = f
        if (exoA.duration > 0) exoA.seekTo((f * exoA.duration).toLong())
        if (exoB.duration > 0) exoB.seekTo((f * exoB.duration).toLong())
    }

    fun playBoth() {
        val fraction = if (exoA.duration > 0) exoA.currentPosition.toFloat() / exoA.duration else progress
        if (exoB.duration > 0) exoB.seekTo((fraction * exoB.duration).toLong())
        exoA.play()
        exoB.play()
        playing = true
    }

    fun pauseBoth() {
        exoA.pause()
        exoB.pause()
        playing = false
    }

    LaunchedEffect(playing) {
        while (playing) {
            if (exoA.duration > 0) progress = (exoA.currentPosition.toFloat() / exoA.duration).coerceIn(0f, 1f)
            delay(200)
        }
    }

    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        BoxWithConstraints(
            Modifier.fillMaxWidth().aspectRatio(16f / 9f).clip(RoundedCornerShape(14.dp))
                .background(Color.Black),
        ) {
            androidx.compose.ui.viewinterop.AndroidView(
                factory = { androidx.media3.ui.PlayerView(it).apply { player = exoB; useController = false } },
                modifier = Modifier.fillMaxSize(),
            )
            androidx.compose.ui.viewinterop.AndroidView(
                factory = { androidx.media3.ui.PlayerView(it).apply { player = exoA; useController = false } },
                modifier = Modifier.fillMaxSize().drawWithContent {
                    clipRect(right = size.width * split) { this@drawWithContent.drawContent() }
                },
            )
            Box(
                Modifier.fillMaxHeight().width(2.dp).offset(x = maxWidth * split - 1.dp)
                    .background(Color.White),
            )
            Box(
                Modifier.fillMaxSize().pointerInput(Unit) {
                    detectHorizontalDragGestures { change, _ ->
                        split = (change.position.x / size.width).coerceIn(0.05f, 0.95f)
                    }
                },
            )
            Text(
                "Earlier",
                style = MaterialTheme.typography.labelSmall,
                color = Color.White,
                modifier = Modifier.align(Alignment.TopStart).padding(8.dp)
                    .clip(RoundedCornerShape(50)).background(Color.Black.copy(alpha = 0.55f))
                    .padding(horizontal = 8.dp, vertical = 3.dp),
            )
            Text(
                "Later",
                style = MaterialTheme.typography.labelSmall,
                color = Color.White,
                modifier = Modifier.align(Alignment.TopEnd).padding(8.dp)
                    .clip(RoundedCornerShape(50)).background(Accent2.copy(alpha = 0.75f))
                    .padding(horizontal = 8.dp, vertical = 3.dp),
            )
        }

        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            GhostButton(if (playing) "Pause" else "Play", { if (playing) pauseBoth() else playBoth() })
            Slider(
                value = progress,
                onValueChange = { seekBoth(it) },
                modifier = Modifier.weight(1f),
            )
        }
        Text(
            "Drag the divider — earlier on the left, later on the right. Playback is progress-synced.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun PickerCard(label: String, reports: List<Report>, selected: Report?, onPick: (Report) -> Unit) {
    var open by remember { mutableStateOf(false) }
    CoachCard(modifier = Modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                SectionLabel(label)
                Spacer(Modifier.height(4.dp))
                Text(
                    selected?.stem?.ifBlank { selected.source } ?: "Choose a session",
                    style = MaterialTheme.typography.titleMedium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            Box {
                GhostButton("Choose", { open = true })
                DropdownMenu(expanded = open, onDismissRequest = { open = false }) {
                    reports.forEach { r ->
                        DropdownMenuItem(
                            text = { Text(r.stem.ifBlank { r.source }) },
                            onClick = { onPick(r); open = false },
                        )
                    }
                }
            }
        }
    }
}
