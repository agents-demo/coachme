package com.topspinreview.android.ui.sessions

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Restore
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SnackbarResult
import androidx.compose.material3.SwipeToDismissBox
import androidx.compose.material3.SwipeToDismissBoxValue
import androidx.compose.material3.Text
import androidx.compose.material3.rememberSwipeToDismissBoxState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.LifecycleEventEffect
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import coil.compose.AsyncImage
import com.topspinreview.android.data.Report
import com.topspinreview.android.data.ReportStore
import com.topspinreview.android.pipeline.PendingRun
import com.topspinreview.android.pipeline.Pipeline
import com.topspinreview.android.ui.components.GhostButton
import com.topspinreview.android.ui.components.HeroCard
import com.topspinreview.android.ui.components.MetaChip
import com.topspinreview.android.ui.components.PrimaryButton
import com.topspinreview.android.ui.components.SectionLabel
import com.topspinreview.android.ui.components.StatTile
import com.topspinreview.android.ui.components.TspCard
import com.topspinreview.android.ui.components.TspTopBar
import com.topspinreview.android.ui.components.heroBrush
import com.topspinreview.android.ui.theme.Accent
import com.topspinreview.android.ui.theme.Accent2
import com.topspinreview.android.ui.theme.Bad
import com.topspinreview.android.ui.theme.Warn
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.time.LocalDate
import java.time.temporal.ChronoUnit
import javax.inject.Inject

@HiltViewModel
class SessionsViewModel @Inject constructor(
    private val store: ReportStore,
    private val pipeline: Pipeline,
) : ViewModel() {
    private var all: List<Report> = emptyList()
    private val pending = linkedMapOf<String, Report>()
    private val _reports = MutableStateFlow<List<Report>>(emptyList())
    val reports: StateFlow<List<Report>> = _reports.asStateFlow()

    private val _interrupted = MutableStateFlow<PendingRun?>(null)
    val interrupted: StateFlow<PendingRun?> = _interrupted.asStateFlow()

    init { refresh() }

    private fun keyOf(r: Report) = r.stem.ifEmpty { r.source }
    private fun publish() { _reports.value = all.filter { keyOf(it) !in pending } }

    fun refresh() = viewModelScope.launch {
        all = store.list(); pending.clear(); publish()
        _interrupted.value = withContext(Dispatchers.IO) { pipeline.pendingRun() }
    }

    fun discardInterrupted() = viewModelScope.launch {
        val stem = _interrupted.value?.stem ?: return@launch
        withContext(Dispatchers.IO) { pipeline.discardRun(stem) }
        _interrupted.value = withContext(Dispatchers.IO) { pipeline.pendingRun() }
    }

    /** Optimistically hide the session; commit the delete if not undone within a few seconds. */
    fun stageDelete(report: Report) {
        pending[keyOf(report)] = report
        publish()
        viewModelScope.launch {
            delay(5000)
            val key = keyOf(report)
            if (pending.containsKey(key)) {
                store.delete(report.stem)
                pending.remove(key)
                all = all.filterNot { keyOf(it) == key }
                publish()
            }
        }
    }

    fun undo(report: Report) { pending.remove(keyOf(report)); publish() }
}

/** Best available thumbnail for a session (pose → motion → frames → source photo). */
private fun thumbOf(r: Report): String? =
    r.artifacts["pose"] ?: r.artifacts["motion"] ?: r.artifacts["frames"]
        ?: if (isPhoto(r)) r.source else null

private fun isPhoto(r: Report): Boolean =
    r.source.matches(Regex(".*\\.(png|jpe?g|bmp|webp|gif)$", RegexOption.IGNORE_CASE))

private val DATE_GROUPS = listOf("Today", "This week", "Earlier")

private fun dateBucket(date: String): String {
    val d = runCatching { LocalDate.parse(date) }.getOrNull() ?: return "Earlier"
    val days = ChronoUnit.DAYS.between(d, LocalDate.now())
    return when {
        days <= 0 -> "Today"
        days <= 6 -> "This week"
        else -> "Earlier"
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SessionsScreen(
    onOpen: (String) -> Unit,
    onNew: () -> Unit,
    onSettings: () -> Unit,
    onCompare: () -> Unit,
    onResume: (String) -> Unit,
    vm: SessionsViewModel = hiltViewModel(),
) {
    val reports by vm.reports.collectAsStateWithLifecycle()
    val interrupted by vm.interrupted.collectAsStateWithLifecycle()
    val totalIssues = reports.sumOf { it.issues.size }
    val snackbar = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    var menuOpen by remember { mutableStateOf(false) }

    LifecycleEventEffect(Lifecycle.Event.ON_RESUME) { vm.refresh() }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TspTopBar(title = "Topspin Review") {
                Box {
                    IconButton(onClick = { menuOpen = true }) { Icon(Icons.Filled.MoreVert, "More options") }
                    DropdownMenu(expanded = menuOpen, onDismissRequest = { menuOpen = false }) {
                        DropdownMenuItem(
                            text = { Text("Compare sessions") },
                            enabled = reports.size >= 2,
                            onClick = { menuOpen = false; onCompare() },
                        )
                        DropdownMenuItem(
                            text = { Text("Settings") },
                            onClick = { menuOpen = false; onSettings() },
                        )
                    }
                }
            }
        },
        snackbarHost = { SnackbarHost(snackbar) },
        floatingActionButton = {
            FloatingActionButton(onClick = onNew, containerColor = Accent, contentColor = Color.White) {
                Icon(Icons.Filled.Add, contentDescription = "New analysis")
            }
        },
    ) { pad ->
        LazyColumn(
            Modifier.fillMaxSize().padding(pad),
            contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 16.dp, bottom = 96.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            item {
                HeroCard(
                    eyebrow = "Vision-powered coaching",
                    title = {
                        Column {
                            Text("Turn a session into a", style = MaterialTheme.typography.displaySmall)
                            Text(
                                "coaching report",
                                style = MaterialTheme.typography.displaySmall.copy(brush = heroBrush()),
                            )
                        }
                    },
                    subtitle = "Pick a clip from your phone, analyze it in-app, and get measured form & footwork insights, the things to fix, and drills.",
                )
            }

            interrupted?.let { run ->
                item(key = "interrupted") {
                    InterruptedCard(
                        run = run,
                        onResume = { onResume(run.stem) },
                        onDiscard = { vm.discardInterrupted() },
                    )
                }
            }

            if (reports.isNotEmpty()) {
                item(key = "stats") {
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        StatTile("${reports.size}", "Sessions", Modifier.weight(1f))
                        StatTile("$totalIssues", "Open issues", Modifier.weight(1f), valueColor = Warn)
                    }
                }
            }

            if (reports.isEmpty()) {
                item(key = "empty") { EmptySessions(onNew) }
            } else {
                val grouped = reports.groupBy { dateBucket(it.date) }
                DATE_GROUPS.forEach { group ->
                    val rows = grouped[group] ?: return@forEach
                    item(key = "header_$group") { SectionLabel(group) }
                    items(rows, key = { it.stem.ifEmpty { it.source } }) { r ->
                    val dismissState = rememberSwipeToDismissBoxState(
                        confirmValueChange = { value ->
                            if (value == SwipeToDismissBoxValue.EndToStart) {
                                vm.stageDelete(r)
                                scope.launch {
                                    val res = snackbar.showSnackbar(
                                        message = "Session removed",
                                        actionLabel = "Undo",
                                        duration = SnackbarDuration.Short,
                                    )
                                    if (res == SnackbarResult.ActionPerformed) vm.undo(r)
                                }
                                true
                            } else {
                                false
                            }
                        },
                    )
                    SwipeToDismissBox(
                        state = dismissState,
                        enableDismissFromStartToEnd = false,
                        backgroundContent = { SwipeDeleteBackground() },
                    ) {
                        SessionCard(report = r, onOpen = { onOpen(r.stem) })
                    }
                }
                }
            }
        }
    }
}

@Composable
private fun InterruptedCard(run: PendingRun, onResume: () -> Unit, onDiscard: () -> Unit) {
    TspCard(modifier = Modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                Modifier.size(44.dp).clip(RoundedCornerShape(14.dp)).background(Accent.copy(alpha = 0.16f)),
                contentAlignment = Alignment.Center,
            ) {
                Icon(Icons.Filled.Restore, contentDescription = null, tint = Accent, modifier = Modifier.size(22.dp))
            }
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text("Unfinished analysis", style = MaterialTheme.typography.titleMedium)
                Text(
                    run.stem,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1,
                )
                Text(
                    "${run.doneCount} of ${run.totalCount} steps done",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
        Spacer(Modifier.height(14.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            GhostButton("Discard", onDiscard, Modifier.weight(1f))
            PrimaryButton(
                "Resume",
                onResume,
                Modifier.weight(1.4f),
                icon = { Icon(Icons.Filled.PlayArrow, contentDescription = null, modifier = Modifier.size(18.dp)) },
            )
        }
    }
}

@Composable
private fun EmptySessions(onNew: () -> Unit) {
    TspCard(modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
            Text("🏓", fontSize = 40.sp)
            Spacer(Modifier.height(8.dp))
            Text("No sessions yet", style = MaterialTheme.typography.titleLarge)
            Spacer(Modifier.height(4.dp))
            Text(
                "Analyze a clip and your coaching reports will show up here.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(16.dp))
            PrimaryButton("Analyze a clip", onNew, Modifier.fillMaxWidth())
        }
    }
}

@Composable
private fun SwipeDeleteBackground() {
    Box(
        Modifier
            .fillMaxSize()
            .clip(MaterialTheme.shapes.large)
            .background(Bad.copy(alpha = 0.85f))
            .padding(end = 24.dp),
        contentAlignment = Alignment.CenterEnd,
    ) {
        Icon(Icons.Filled.Delete, contentDescription = "Delete", tint = Color.White)
    }
}

@Composable
private fun SessionCard(report: Report, onOpen: () -> Unit) {
    val poster = thumbOf(report)
    TspCard(
        modifier = Modifier.fillMaxWidth().clickable { onOpen() },
        padding = PaddingValues(0.dp),
    ) {
        Box(Modifier.fillMaxWidth()) {
            Box(
                Modifier
                    .fillMaxWidth()
                    .aspectRatio(16f / 9f)
                    .background(Brush.linearGradient(listOf(Accent.copy(alpha = 0.25f), Accent2.copy(alpha = 0.25f)))),
                contentAlignment = Alignment.Center,
            ) {
                if (poster != null) {
                    AsyncImage(
                        model = File(poster),
                        contentDescription = null,
                        contentScale = ContentScale.Crop,
                        modifier = Modifier.fillMaxSize(),
                    )
                } else {
                    Text("🏓", fontSize = 46.sp)
                }
            }

            if (isPhoto(report)) {
                Box(
                    Modifier.align(Alignment.BottomEnd).padding(8.dp)
                        .clip(CircleShape).background(Color(0xCC0B0B0F)).padding(horizontal = 8.dp, vertical = 3.dp),
                ) {
                    Text("PHOTO", style = MaterialTheme.typography.labelSmall, letterSpacing = 1.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            } else {
                Box(
                    Modifier.align(Alignment.BottomStart).padding(8.dp)
                        .size(28.dp).clip(CircleShape).background(Color(0xCC0B0B0F)),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(Icons.Filled.PlayArrow, contentDescription = null, tint = Color.White, modifier = Modifier.size(16.dp))
                }
            }
        }

        Column(Modifier.fillMaxWidth().padding(12.dp)) {
            Text(
                report.stem.ifBlank { report.source },
                style = MaterialTheme.typography.titleMedium,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Spacer(Modifier.height(2.dp))
            Text(
                "${report.sport.ifBlank { "session" }} · ${report.date.ifBlank { "undated" }}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(6.dp))
            Text(
                report.summary.ifBlank { report.focus }.ifBlank { "—" },
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                val issues = report.issues.size
                MetaChip("$issues issue${if (issues == 1) "" else "s"}")
                if (report.artifacts["pose"] != null || report.artifacts["pose_hero"] != null) MetaChip("pose")
                if (report.focus.isNotBlank()) {
                    Text(
                        report.focus,
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f),
                    )
                }
            }
        }
    }
}
