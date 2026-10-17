package com.topspinreview.android.ui.result

import androidx.compose.animation.AnimatedVisibilityScope
import androidx.compose.animation.Crossfade
import androidx.compose.animation.ExperimentalSharedTransitionApi
import androidx.compose.animation.SharedTransitionScope
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.sizeIn
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.automirrored.filled.TrendingUp
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.Chat
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Code
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Gif
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Insights
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.Movie
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.PictureAsPdf
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.PlayCircle
import androidx.compose.material.icons.filled.Share
import androidx.compose.material.icons.filled.SportsTennis
import androidx.compose.material.icons.filled.School
import androidx.compose.material.icons.filled.Videocam
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CheckboxDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledIconButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.OutlinedTextField
import com.topspinreview.android.ui.components.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import coil.compose.AsyncImage
import com.topspinreview.android.data.Report
import com.topspinreview.android.data.ReportStore
import com.topspinreview.android.domain.Drills
import com.topspinreview.android.domain.Outputs
import com.topspinreview.android.domain.Reporting
import com.topspinreview.android.llm.DeepSeekClient
import com.topspinreview.android.llm.Prompts
import com.topspinreview.android.ui.MicButton
import com.topspinreview.android.ui.SpeakButton
import com.topspinreview.android.ui.components.DividerLine
import com.topspinreview.android.ui.components.MutedNote
import com.topspinreview.android.ui.components.GhostButton
import com.topspinreview.android.ui.components.MetaChip
import com.topspinreview.android.ui.components.GradientProgress
import com.topspinreview.android.ui.components.MediaImage
import com.topspinreview.android.ui.components.PrimaryButton
import com.topspinreview.android.ui.components.SectionLabel
import com.topspinreview.android.ui.components.TspCard
import com.topspinreview.android.ui.components.TspSegmented
import com.topspinreview.android.ui.components.TspTopBar
import com.topspinreview.android.ui.theme.Bad
import com.topspinreview.android.ui.theme.Good
import com.topspinreview.android.ui.theme.SpaceGrotesk
import com.topspinreview.android.ui.theme.Warn
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import java.io.File
import javax.inject.Inject

@HiltViewModel
class ResultViewModel @Inject constructor(
    private val store: ReportStore,
    private val client: DeepSeekClient,
    private val json: kotlinx.serialization.json.Json,
) : ViewModel() {
    private val _report = MutableStateFlow<Report?>(null)
    val report = _report.asStateFlow()
    private val _loading = MutableStateFlow(true)
    val loading = _loading.asStateFlow()
    private val _answers = MutableStateFlow<List<Pair<String, String>>>(emptyList())
    val answers = _answers.asStateFlow()
    private val _asking = MutableStateFlow(false)
    val asking = _asking.asStateFlow()

    fun load(stem: String) = viewModelScope.launch {
        _loading.value = true
        val r = withContext(Dispatchers.IO) { store.load(stem) }
        _report.value = r
        _loading.value = false
    }

    fun saveAnnotations(annotations: JsonArray) {
        val r = _report.value ?: return
        store.saveAnnotations(r.stem, annotations)
        _report.value = r.copy(annotations = annotations)
    }

    /** Clear the run caveats for this session (persisted, so they don't reappear). */
    fun dismissWarnings() {
        val r = _report.value ?: return
        if (r.warnings.isEmpty()) return
        val updated = r.copy(warnings = emptyList())
        store.save(r.stem, updated)
        _report.value = updated
    }

    fun ask(question: String) = viewModelScope.launch {
        val r = _report.value ?: return@launch
        _asking.value = true
        val context = buildJsonObject {
            put("summary", r.summary); put("focus", r.focus)
            put("issues", buildJsonArray {
                r.issues.forEach { i ->
                    add(buildJsonObject {
                        put("issue", i.issue); put("confidence", i.confidence)
                        put("evidence_times", buildJsonArray { i.evidence_times.forEach { add(JsonPrimitive(it)) } })
                    })
                }
            })
            put("drills", buildJsonArray { r.drills.forEach { add(JsonPrimitive(it)) } })
            put("metrics", r.metrics)
        }
        val answer = runCatching {
            client.text(Prompts.QA_SYSTEM, "Report:\n$context\n\nQuestion: $question")
        }.getOrElse { "Could not answer: ${it.message}" }
        _answers.value = _answers.value + (question to answer)
        _asking.value = false
    }
}

private val TABS = listOf("Video", "Analysis", "Observe", "Coaching")
private val MAIN_ICONS = listOf(
    Icons.Filled.PlayCircle,
    Icons.Filled.Insights,
    Icons.Filled.Visibility,
    Icons.Filled.School,
)

@OptIn(ExperimentalSharedTransitionApi::class)
@Composable
fun ResultScreen(
    stem: String,
    sharedTransitionScope: SharedTransitionScope,
    animatedVisibilityScope: AnimatedVisibilityScope,
    onBack: () -> Unit,
    onOpenDiagnostics: (String) -> Unit = {},
    onRetryAnalysis: (String) -> Unit = {},
    vm: ResultViewModel = hiltViewModel(),
) {
    val report by vm.report.collectAsStateWithLifecycle()
    val loading by vm.loading.collectAsStateWithLifecycle()
    var tab by remember { mutableStateOf(0) } // Video
    var seekMs by remember { mutableStateOf<Long?>(null) }
    val answers by vm.answers.collectAsStateWithLifecycle()
    val asking by vm.asking.collectAsStateWithLifecycle()
    var askOpen by remember { mutableStateOf(false) }
    val haptics = LocalHapticFeedback.current
    val ctx = androidx.compose.ui.platform.LocalContext.current
    val drillsDone = remember(stem) {
        val prefs = ctx.getSharedPreferences("topspin_drills", 0)
        val saved = prefs.getString("drills_$stem", "").orEmpty()
            .split(",")
            .mapNotNull { it.toIntOrNull() }
        mutableStateMapOf<Int, Boolean>().apply { saved.forEach { put(it, true) } }
    }

    androidx.compose.runtime.LaunchedEffect(stem) { vm.load(stem) }

    Scaffold(
        modifier = with(sharedTransitionScope) {
            Modifier.sharedBounds(
                rememberSharedContentState(key = "card_$stem"),
                animatedVisibilityScope = animatedVisibilityScope,
            )
        },
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TspTopBar(
                onBack = onBack,
                titleContent = {
                    val name = report?.stem?.ifBlank { stem } ?: stem
                    val meta = listOfNotNull(
                        report?.sport?.takeIf { it.isNotBlank() },
                        report?.date?.takeIf { it.isNotBlank() },
                    ).joinToString(" · ")
                    Column(Modifier.weight(1f)) {
                        Text(
                            name,
                            style = MaterialTheme.typography.titleLarge,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                        if (meta.isNotBlank()) {
                            Text(
                                meta,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                        }
                    }
                },
                actions = {
                    IconButton(onClick = { askOpen = true }) {
                        Icon(Icons.Filled.Chat, contentDescription = "Ask the coach")
                    }
                    var menuOpen by remember { mutableStateOf(false) }
                    Box {
                        IconButton(onClick = { menuOpen = true }) {
                            Icon(Icons.Filled.MoreVert, contentDescription = "More options")
                        }
                        DropdownMenu(expanded = menuOpen, onDismissRequest = { menuOpen = false }) {
                            DropdownMenuItem(
                                text = { Text("Share card") },
                                enabled = report != null,
                                onClick = { menuOpen = false; report?.let { ShareCard.share(ctx, it) } },
                            )
                            DropdownMenuItem(
                                text = { Text("Diagnostics") },
                                onClick = { menuOpen = false; onOpenDiagnostics(stem) },
                            )
                        }
                    }
                },
            )
        },
        bottomBar = {
            Column {
                DividerLine()
                NavigationBar(containerColor = MaterialTheme.colorScheme.background) {
                    TABS.forEachIndexed { i, label ->
                        NavigationBarItem(
                            selected = tab == i,
                            onClick = { tab = i; haptics.performHapticFeedback(HapticFeedbackType.TextHandleMove) },
                            icon = { Icon(MAIN_ICONS[i], contentDescription = null) },
                            label = {
                                Text(
                                    label,
                                    style = MaterialTheme.typography.labelSmall,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                )
                            },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = MaterialTheme.colorScheme.primary,
                                selectedTextColor = MaterialTheme.colorScheme.primary,
                                indicatorColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.16f),
                                unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant,
                            ),
                        )
                    }
                }
            }
        },
    ) { pad ->
        val r = report
        Column(Modifier.fillMaxSize().padding(pad)) {
            if (loading) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(color = MaterialTheme.colorScheme.primary)
                }
            } else if (r == null) {
                MutedNote("Report not found.", Modifier.padding(horizontal = 16.dp))
            } else {
                val clipWarnings = (r.quality["warnings"] as? JsonArray)?.mapNotNull { it.toString().trim('"') } ?: emptyList()
                val runCaveats = r.warnings.filter { it !in clipWarnings }
                if (runCaveats.isNotEmpty()) {
                    CaveatsBanner(
                        warnings = runCaveats,
                        onRetry = { onRetryAnalysis(stem) },
                        onDismiss = vm::dismissWarnings,
                    )
                }
                Crossfade(targetState = tab, modifier = Modifier.fillMaxSize(), label = "tab") { t ->
                    when (t) {
                        0 -> VideoTab(r, vm::saveAnnotations, seekMs = seekMs, onSeekConsumed = { seekMs = null })
                        1 -> AnalysisTab(r)
                        2 -> ObservationsTab(r)
                        else -> CoachingTab(r, drillsDone)
                    }
                }
            }
        }
    }

    if (askOpen) {
        AskSheet(
            answers = answers,
            asking = asking,
            onAsk = vm::ask,
            onDismiss = { askOpen = false },
        )
    }
}

// ---------------------------------------------------------------------------
// Reusable bits
// ---------------------------------------------------------------------------

@Composable
private fun RowScope.Metric(value: String, label: String, weight: Float = 1f, color: Color? = null) {
    Column(Modifier.weight(weight)) {
        Text(value, style = MaterialTheme.typography.headlineSmall, color = color ?: MaterialTheme.colorScheme.onSurface)
        Text(
            label.uppercase(),
            style = MaterialTheme.typography.labelSmall,
            letterSpacing = 1.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

/** A titled block: section label + hint, then a card holding the visual + provenance. */
@Composable
private fun ItemCard(
    label: String,
    hint: String? = null,
    prov: Outputs.Info? = null,
    content: @Composable ColumnScope.() -> Unit,
) {
    Column(Modifier.fillMaxWidth()) {
        SectionLabel(label)
        if (hint != null) {
            Spacer(Modifier.height(4.dp))
            Text(hint, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Spacer(Modifier.height(10.dp))
        TspCard(modifier = Modifier.fillMaxWidth()) {
            content()
            if (prov != null) {
                Spacer(Modifier.height(8.dp))
                Prov(prov)
            }
        }
    }
}

/** A collapsible "details" line with the technical method + engine + source. */
@Composable
private fun Prov(info: Outputs.Info) {
    var open by remember { mutableStateOf(false) }
    Column {
        Text(
            if (open) "hide details" else "details",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.secondary,
            modifier = Modifier
                .clip(RoundedCornerShape(6.dp))
                .clickable { open = !open }
                .padding(vertical = 2.dp),
        )
        if (open) {
            Spacer(Modifier.height(4.dp))
            Text(info.method, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(2.dp))
            Text("${info.detail} · ${info.engine}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.secondary)
        }
    }
}

// ---------------------------------------------------------------------------
// Analysis
// ---------------------------------------------------------------------------

private val ANALYSIS_SUBTABS = listOf("Movement", "Pose", "Object")

@Composable
private fun AnalysisTab(r: Report) {
    var sub by remember { mutableStateOf(0) }
    Column(Modifier.fillMaxSize()) {
        TspSegmented(ANALYSIS_SUBTABS, sub, { sub = it }, Modifier.padding(horizontal = 16.dp, vertical = 8.dp))
        val m = r.metrics
        val mech = m["mechanics"] as? JsonObject
        val foot = m["footwork_series"] as? JsonArray
        val poseSummary = m["pose_summary"] as? JsonObject
        val poseAngles = m["pose_angles"] as? JsonArray
        val pose3d = m["pose3d"] as? JsonArray
        val strokes = m["strokes"] as? JsonArray
        val ball = m["ball"] as? JsonObject

        Column(
            Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            when (sub) {
                0 -> {
                    if (foot != null && foot.size > 1) {
                        val lateral = (mech?.get("lower_lateral_range")?.toString()?.toDoubleOrNull() ?: 0.0) * 100
                        val changes = mech?.get("lower_direction_changes")?.toString() ?: "0"
                        ItemCard(
                            "Side-to-side movement",
                            "Your lower body's left–right position through the clip; the shaded band is the travel range.",
                            Outputs.lateral,
                        ) {
                            Row(horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                                Metric("${lateral.toInt()}%", "Travel (band)")
                                Metric(changes, "Direction changes")
                            }
                            Spacer(Modifier.height(12.dp))
                            FootworkChart(foot)
                        }
                    }
                    r.artifacts["motion"]?.let {
                        ItemCard("Movement map", "Red = where the picture changed most — where the action happened.", Outputs.motionMap) {
                            MediaImage(File(it), "Movement map")
                        }
                    }
                    r.artifacts["heatmap"]?.let {
                        ItemCard("Position map", "Where you spent the most time within the frame.", Outputs.positionMap) {
                            MediaImage(File(it), "Position map")
                        }
                    }
                    if (foot == null && r.artifacts["motion"] == null && r.artifacts["heatmap"] == null) NoData("No movement data for this run.")
                }
                1 -> {
                    r.artifacts["pose"]?.let {
                        ItemCard("Skeleton", "Your body's joints, detected on a sampled frame.", Outputs.skeleton) {
                            MediaImage(File(it), "Skeleton")
                        }
                    }
                    if (poseSummary != null && poseSummary.isNotEmpty()) {
                        ItemCard("Body angles", "Joint angles over the clip, in degrees (mean shown).", Outputs.angles) {
                            poseAngles?.let { PoseAngleChart(it) }
                            Spacer(Modifier.height(10.dp))
                            Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                                poseSummary["l_knee_mean"]?.let { Metric(it.toString(), "L knee") }
                                poseSummary["r_knee_mean"]?.let { Metric(it.toString(), "R knee") }
                                poseSummary["l_elbow_mean"]?.let { Metric(it.toString(), "L elbow") }
                                poseSummary["r_elbow_mean"]?.let { Metric(it.toString(), "R elbow") }
                            }
                        }
                    }
                    if (pose3d != null && pose3d.size > 0) {
                        ItemCard("Body 3D", "Your body as a rotatable 3D stick figure; depth from one camera is approximate.", Outputs.pose3d) {
                            Pose3DView(pose3d)
                            Spacer(Modifier.height(6.dp))
                            Text("Drag to rotate.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                    if (strokes != null && strokes.isNotEmpty()) {
                        ItemCard("Fast-hand events", "Moments a hand moved fastest, and which hand.", Outputs.strokes) {
                            Row(
                                Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                            ) {
                                strokes.forEach { s ->
                                    val o = s as? JsonObject
                                    val hand = o?.get("hand")?.toString()?.trim('"') ?: "?"
                                    val t = o?.get("t")?.toString() ?: "?"
                                    MetaChip("$hand · ${t}s", color = MaterialTheme.colorScheme.secondary, border = MaterialTheme.colorScheme.secondary.copy(alpha = 0.4f))
                                }
                            }
                        }
                    }
                    if (r.artifacts["pose"] == null && poseSummary == null && pose3d == null) NoData("No pose data for this run.")
                }
                else -> {
                    r.artifacts["ball"]?.let {
                        ItemCard("Object path", "The route the tracked object took — a rough guide.", Outputs.objectPath) {
                            MediaImage(File(it), "Object path")
                        }
                    }
                    (ball?.get("stats") as? JsonObject)?.let { o ->
                        ItemCard("Tracked object", "How much of the clip the object was visible and how fast it moved.") {
                            Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                                o["visible_frames"]?.let { Metric(it.toString(), "Frames tracked") }
                                o["max_speed"]?.let { Metric(it.toString(), "Max speed") }
                                (ball["segments"] as? JsonArray)?.let { Metric(it.size.toString(), "Active spans") }
                            }
                        }
                    }
                    (ball?.get("trajectory3d") as? JsonArray)?.let { traj ->
                        if (traj.size > 2) {
                            ItemCard("Object trajectory", "The object's route in 3D; the shape is useful, distances aren't.", Outputs.trajectory3d) {
                                Trajectory3DView(traj)
                                Spacer(Modifier.height(6.dp))
                                Text("Drag to rotate.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        }
                    }
                    if (r.artifacts["ball"] == null && ball == null) NoData("No tracked object in this clip.")
                }
            }
        }
    }
}

@Composable
private fun NoData(text: String) {
    TspCard(modifier = Modifier.fillMaxWidth()) {
        Column(
            Modifier.fillMaxWidth().padding(vertical = 12.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Icon(
                Icons.Filled.Info,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.size(22.dp),
            )
            Spacer(Modifier.height(8.dp))
            Text(
                text,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center,
            )
        }
    }
}

// ---------------------------------------------------------------------------
// Observations
// ---------------------------------------------------------------------------

@Composable
private fun ObservationsTab(r: Report) {
    var sub by remember { mutableStateOf(0) }
    Column(Modifier.fillMaxSize()) {
        TspSegmented(listOf("Findings", "Key moments"), sub, { sub = it }, Modifier.padding(horizontal = 16.dp, vertical = 8.dp))
        if (sub == 0) Findings(r) else KeyMoments(r)
    }
}

@Composable
private fun Findings(r: Report) {
    val findings = (r.tt_reading?.get("findings") as? JsonArray) ?: JsonArray(emptyList())
    val activity = r.metrics["activity"] as? JsonArray
    val segments = (r.metrics["ball"] as? JsonObject)?.get("segments") as? JsonArray
    val poseAngles = r.metrics["pose_angles"] as? JsonArray
    val trajectory = (r.metrics["ball"] as? JsonObject)?.get("trajectory3d") as? JsonArray

    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        val present = listOf("Play", "Player", "Ball").map { grp ->
            grp to findings.filter { (it as? JsonObject)?.get("group")?.toString()?.trim('"') == grp }
        }.filter { it.second.isNotEmpty() }
        if (present.isEmpty()) {
            item { NoData("No observations available for this run.") }
        }
        present.forEach { (grp, rows) ->
            item {
                TspCard(modifier = Modifier.fillMaxWidth()) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            Modifier.size(30.dp).clip(CircleShape).background(MaterialTheme.colorScheme.primary.copy(alpha = 0.14f)),
                            contentAlignment = Alignment.Center,
                        ) {
                            Icon(groupIcon(grp), contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(17.dp))
                        }
                        Spacer(Modifier.width(10.dp))
                        SectionLabel(grp, color = MaterialTheme.colorScheme.primary)
                        Spacer(Modifier.weight(1f))
                        MetaChip("${rows.size}")
                    }
                    if (findingsHasVisual(grp, r, activity, segments, poseAngles, trajectory)) {
                        Spacer(Modifier.height(14.dp))
                        GroupVisual(grp, r, activity, segments, poseAngles, trajectory)
                        Spacer(Modifier.height(16.dp))
                        DividerLine()
                        Spacer(Modifier.height(16.dp))
                    } else {
                        Spacer(Modifier.height(12.dp))
                    }
                    rows.forEachIndexed { i, f ->
                        val o = f as JsonObject
                        if (i > 0) { Spacer(Modifier.height(12.dp)); DividerLine(); Spacer(Modifier.height(12.dp)) }
                        val label = o["label"]?.toString()?.trim('"').orEmpty()
                        val value = o["value"]?.toString()?.trim('"').orEmpty()
                        val note = o["note"]?.toString()?.trim('"').orEmpty()
                        Text(label, style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.SemiBold)
                        if (value.isNotBlank()) {
                            Spacer(Modifier.height(2.dp))
                            Text(value, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        if (note.isNotBlank()) {
                            Spacer(Modifier.height(2.dp))
                            Text(note, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.8f))
                        }
                    }
                }
            }
        }
    }
}

private fun findingsHasVisual(
    grp: String,
    r: Report,
    activity: JsonArray?,
    segments: JsonArray?,
    poseAngles: JsonArray?,
    trajectory: JsonArray?,
): Boolean = when (grp) {
    "Play" -> (activity != null && activity.size > 1) || (segments != null && segments.isNotEmpty())
    "Player" -> r.artifacts["pose"] != null || (poseAngles != null && poseAngles.size > 1)
    "Ball" -> r.artifacts["ball"] != null || (trajectory != null && trajectory.size > 2)
    else -> false
}

/** The measured visuals that back a findings group (mirrors gui2's embedded charts). */
@Composable
private fun GroupVisual(
    grp: String,
    r: Report,
    activity: JsonArray?,
    segments: JsonArray?,
    poseAngles: JsonArray?,
    trajectory: JsonArray?,
) {
    when (grp) {
        "Play" -> {
            if (activity != null && activity.size > 1) {
                VisualLabel("Movement over time", "Energy moment-to-moment — a peak is a burst of action.")
                Spacer(Modifier.height(8.dp))
                EnergyChart(activity)
            }
            if (segments != null && segments.isNotEmpty()) {
                if (activity != null && activity.size > 1) Spacer(Modifier.height(16.dp))
                VisualLabel("Active spans", "When the ball was in play.")
                Spacer(Modifier.height(8.dp))
                SegmentsBar(segments, lastT(activity ?: JsonArray(emptyList())))
            }
        }
        "Player" -> {
            r.artifacts["pose"]?.let {
                MediaImage(File(it), "Skeleton")
                Spacer(Modifier.height(14.dp))
            }
            if (poseAngles != null && poseAngles.size > 1) {
                PoseAngleChart(poseAngles)
                Spacer(Modifier.height(6.dp))
                Text(
                    "Joint angles over the clip, from the sampled frames — pose estimates, not clinical measurements.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
        "Ball" -> {
            r.artifacts["ball"]?.let {
                MediaImage(File(it), "Tracked path")
                Spacer(Modifier.height(14.dp))
            }
            if (trajectory != null && trajectory.size > 2) {
                Trajectory3DView(trajectory)
                Spacer(Modifier.height(6.dp))
                Text(
                    "The object's route in 3D; drag to rotate. The shape is useful, distances aren't.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun VisualLabel(title: String, hint: String) {
    Column {
        Text(title, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
        Spacer(Modifier.height(2.dp))
        Text(hint, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun KeyMoments(r: Report) {
    val ctx = androidx.compose.ui.platform.LocalContext.current
    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        if (r.issues.isEmpty()) {
            item { NoData("No timestamped issues in this report.") }
        } else {
            item {
                TspCard(modifier = Modifier.fillMaxWidth()) {
                    SectionLabel("Key moments")
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "The notable seconds — tap a time to export that moment.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            items(r.issues) { issue ->
                TspCard(modifier = Modifier.fillMaxWidth()) {
                    Text(issue.issue, style = MaterialTheme.typography.bodyLarge)
                    val times = issue.evidence_times
                    if (times.isNotEmpty() || issue.confidence.isNotBlank()) {
                        Spacer(Modifier.height(10.dp))
                        Row(
                            Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            confidenceChip(issue.confidence)
                            times.forEach { t ->
                                ClipChip("▶ ${fmtTime(t)}") { clipAndShare(ctx, r.source, t - 1.0, t + 2.0) }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun confidenceChip(conf: String) {
    val tone = when (conf.lowercase()) {
        "high" -> Bad
        "medium" -> Warn
        else -> MaterialTheme.colorScheme.onSurfaceVariant
    }
    MetaChip(conf.ifBlank { "low" }, color = tone, border = tone.copy(alpha = 0.5f), borderWidth = 2.dp)
}

/** A small, tappable pill (lighter than a full ghost button). */
@Composable
private fun ClipChip(label: String, onClick: () -> Unit) {
    Box(
        Modifier
            .sizeIn(minWidth = 48.dp, minHeight = 48.dp)
            .clickable { onClick() },
        contentAlignment = Alignment.Center,
    ) {
        Box(
            Modifier
                .clip(CircleShape)
                .border(2.dp, MaterialTheme.colorScheme.outline, CircleShape)
                .padding(horizontal = 12.dp, vertical = 5.dp),
        ) {
            Text(
                label,
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Medium,
                color = MaterialTheme.colorScheme.onSurface,
            )
        }
    }
}

private fun groupIcon(name: String) = when (name) {
    "Player" -> Icons.Filled.Person
    "Ball" -> Icons.Filled.SportsTennis
    else -> Icons.Filled.PlayArrow
}

// ---------------------------------------------------------------------------
// Coaching
// ---------------------------------------------------------------------------

private val COACH_SUBTABS = listOf("Advice", "Practice", "Export")

@Composable
private fun CoachingTab(
    r: Report,
    drillsDone: MutableMap<Int, Boolean>,
) {
    var sub by remember { mutableStateOf(0) }
    Column(Modifier.fillMaxSize()) {
        TspSegmented(COACH_SUBTABS, sub, { sub = it }, Modifier.padding(horizontal = 16.dp, vertical = 8.dp))
        when (sub) {
            0 -> Advice(r)
            1 -> Practice(r, drillsDone)
            else -> Export(r)
        }
    }
}

@Composable
private fun Advice(r: Report) {
    val summaryText = buildString {
        if (r.sport.isNotBlank()) append("${r.sport} on ${r.date.ifBlank { "an unknown date" }}. ")
        if (r.focus.isNotBlank()) append("Focus next session: ${r.focus}. ")
        r.issues.take(3).forEach { append("${it.issue}. ") }
        append(r.summary)
    }.trim()

    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            Row(verticalAlignment = Alignment.CenterVertically) {
                SectionLabel("Advice")
                Spacer(Modifier.weight(1f))
                SpeakButton(summaryText)
            }
        }
        if (r.focus.isNotBlank()) {
            item {
                TintedCard(border = Good.copy(alpha = 0.4f), background = Good.copy(alpha = 0.1f)) {
                    SectionLabel("Focus next session", color = Good)
                    Spacer(Modifier.height(6.dp))
                    Text(r.focus, style = MaterialTheme.typography.titleMedium)
                }
            }
        }
        if (r.strengths.isNotEmpty()) {
            item {
                TintedCard(border = Good.copy(alpha = 0.3f), background = Good.copy(alpha = 0.05f)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Filled.CheckCircle, contentDescription = null, tint = Good, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(8.dp))
                        Text(
                            "What's working",
                            fontFamily = SpaceGrotesk,
                            fontWeight = FontWeight.Bold,
                            style = MaterialTheme.typography.titleMedium,
                            color = Good,
                        )
                    }
                    Spacer(Modifier.height(8.dp))
                    r.strengths.forEach { Bullet(it) }
                }
            }
        }
        if (r.issues.isNotEmpty()) {
            item {
                TintedCard(border = Warn.copy(alpha = 0.3f), background = Warn.copy(alpha = 0.05f)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Filled.Bolt, contentDescription = null, tint = Warn, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(8.dp))
                        Text(
                            "What to improve",
                            fontFamily = SpaceGrotesk,
                            fontWeight = FontWeight.Bold,
                            style = MaterialTheme.typography.titleMedium,
                            color = Warn,
                        )
                    }
                    Spacer(Modifier.height(8.dp))
                    r.issues.forEach { Bullet(it.issue) }
                }
            }
        }
        if (r.summary.isNotBlank() || r.progress.isNotBlank()) {
            item {
                TspCard(modifier = Modifier.fillMaxWidth()) {
                    SectionLabel("Read more")
                    if (r.summary.isNotBlank()) {
                        Spacer(Modifier.height(8.dp))
                        Text(r.summary, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    if (r.progress.isNotBlank()) {
                        Spacer(Modifier.height(10.dp))
                        Text("Since last time", style = MaterialTheme.typography.titleSmall)
                        Spacer(Modifier.height(2.dp))
                        Text(r.progress, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        }
        val clipWarnings = (r.quality["warnings"] as? JsonArray)?.mapNotNull { it.toString().trim('"') } ?: emptyList()
        val caveats = r.limitations.filter { it !in clipWarnings }
        if (clipWarnings.isNotEmpty() || caveats.isNotEmpty()) {
            item {
                TspCard(modifier = Modifier.fillMaxWidth()) {
                    SectionLabel("About this analysis")
                    if (clipWarnings.isNotEmpty()) {
                        Spacer(Modifier.height(8.dp))
                        Text("Your clip", style = MaterialTheme.typography.titleSmall)
                        Spacer(Modifier.height(2.dp))
                        clipWarnings.forEach { Bullet(it) }
                    }
                    if (caveats.isNotEmpty()) {
                        Spacer(Modifier.height(10.dp))
                        Text("Limits", style = MaterialTheme.typography.titleSmall)
                        Spacer(Modifier.height(2.dp))
                        caveats.forEach { Bullet(it) }
                    }
                }
            }
        }
    }
}
@Composable
private fun TintedCard(border: Color, background: Color, content: @Composable ColumnScope.() -> Unit) {
    val shape = MaterialTheme.shapes.large
    Box(
        Modifier
            .fillMaxWidth()
            .clip(shape)
            .background(background)
            .border(2.dp, border, shape)
            .padding(16.dp),
    ) {
        Column(content = content)
    }
}

@Composable
private fun Bullet(text: String) {
    Row(Modifier.padding(vertical = 3.dp)) {
        Text("•", color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(end = 8.dp))
        Text(text, style = MaterialTheme.typography.bodyMedium)
    }
}

/** A always-visible strip reminding the user why this report is lower-confidence. */
@Composable
private fun CaveatsBanner(warnings: List<String>, onRetry: () -> Unit, onDismiss: () -> Unit) {
    Box(Modifier.fillMaxWidth().padding(start = 16.dp, end = 16.dp, top = 12.dp)) {
        TintedCard(border = Warn.copy(alpha = 0.4f), background = Warn.copy(alpha = 0.08f)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    "Partial run",
                    fontFamily = SpaceGrotesk,
                    fontWeight = FontWeight.Bold,
                    style = MaterialTheme.typography.titleSmall,
                    color = Warn,
                )
                Spacer(Modifier.weight(1f))
                MetaChip(
                    "${warnings.size} caveat${if (warnings.size == 1) "" else "s"}",
                    color = Warn,
                    border = Warn.copy(alpha = 0.5f),
                )
                IconButton(onClick = onDismiss, modifier = Modifier.size(32.dp)) {
                    Icon(Icons.Filled.Close, contentDescription = "Dismiss", tint = Warn, modifier = Modifier.size(18.dp))
                }
            }
            Spacer(Modifier.height(6.dp))
            warnings.forEach { Bullet(it) }
            Spacer(Modifier.height(4.dp))
            TextButton(onClick = onRetry, colors = ButtonDefaults.textButtonColors(contentColor = Warn)) {
                Text("Retry the failed step", style = MaterialTheme.typography.labelLarge)
            }
        }
    }
}

@Composable
private fun Practice(r: Report, done: MutableMap<Int, Boolean>) {
    val prefs = androidx.compose.ui.platform.LocalContext.current.getSharedPreferences("topspin_drills", 0)
    if (r.drills.isEmpty()) {
        MutedNote("No practice items for this session.", Modifier.padding(16.dp))
        return
    }
    val doneCount = done.count { it.value }
    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("$doneCount of ${r.drills.size} done", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Spacer(Modifier.weight(1f))
            }
            Spacer(Modifier.height(8.dp))
            GradientProgress(doneCount.toFloat() / r.drills.size)
        }
        items(r.drills.size) { i ->
            val d = r.drills[i]
            val det = Drills.lookup(d)
            val checked = done[i] == true
            TspCard(
                modifier = Modifier.fillMaxWidth(),
                raised = checked,
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(
                        checked = checked,
                        onCheckedChange = { checked ->
                            done[i] = checked
                            val ids = done.filterValues { it }.keys.sorted().joinToString(",")
                            prefs.edit().putString("drills_${r.stem}", ids).apply()
                        },
                        colors = CheckboxDefaults.colors(checkedColor = MaterialTheme.colorScheme.primary),
                    )
                    Column(Modifier.weight(1f).padding(start = 6.dp)) {
                        Text(
                            "${i + 1}. $d",
                            style = MaterialTheme.typography.bodyLarge,
                            color = if (checked) MaterialTheme.colorScheme.onSurfaceVariant else MaterialTheme.colorScheme.onSurface,
                        )
                        if (det != null) {
                            Spacer(Modifier.height(4.dp))
                            Text("${det.name} · ${det.cue}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text("Next: ${det.progression}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.secondary)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun Export(r: Report) {
    val ctx = androidx.compose.ui.platform.LocalContext.current
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        val times = r.issues.flatMap { it.evidence_times }
        TspCard(modifier = Modifier.fillMaxWidth()) {
            SectionLabel("Share")
            Spacer(Modifier.height(6.dp))
            ExportRow("Share card", "A PNG summary of the report", Icons.Filled.Share) { ShareCard.share(ctx, r) }
            ExportRow("Original clip", "Share the source video", Icons.Filled.Videocam) { shareSource(ctx, r.source) }
            if (times.isNotEmpty()) {
                ExportRow("Highlight reel", "An mp4 of the key moments", Icons.Filled.Movie) { exportReel(ctx, r.source, times) }
            }
        }
        TspCard(modifier = Modifier.fillMaxWidth()) {
            SectionLabel("Export")
            Spacer(Modifier.height(6.dp))
            ExportRow("Markdown", "A plain-text version", Icons.Filled.Description) { Reporting.share(ctx, r, "md") }
            ExportRow("HTML", "Open in your browser", Icons.Filled.Code) { Reporting.share(ctx, r, "html") }
            ExportRow("Print / PDF", "Save via the system dialog", Icons.Filled.PictureAsPdf) { Reporting.printPdf(ctx, r) }
            ExportRow("Animated GIF", "A short looping clip", Icons.Filled.Gif) {
                val start = (times.minOrNull()?.minus(1.0) ?: 0.0).coerceAtLeast(0.0)
                exportGif(ctx, r.source, start, start + 3.0)
            }
        }
    }
}

@Composable
private fun ExportRow(label: String, subtitle: String, icon: ImageVector, onClick: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp)).clickable { onClick() }.padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            Modifier.size(40.dp).clip(CircleShape).background(MaterialTheme.colorScheme.primary.copy(alpha = 0.14f)),
            contentAlignment = Alignment.Center,
        ) {
            Icon(icon, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(20.dp))
        }
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            Text(label, style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.SemiBold)
            Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Icon(
            Icons.AutoMirrored.Filled.KeyboardArrowRight,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.size(20.dp),
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun AskSheet(
    answers: List<Pair<String, String>>,
    asking: Boolean,
    onAsk: (String) -> Unit,
    onDismiss: () -> Unit,
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    var q by remember { mutableStateOf("") }
    val listState = rememberLazyListState()
    LaunchedEffect(answers.size, asking) {
        val target = answers.size + if (asking) 1 else 0
        if (target > 0) listState.animateScrollToItem(target - 1)
    }

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        containerColor = MaterialTheme.colorScheme.surface,
    ) {
        Column(Modifier.fillMaxWidth().padding(horizontal = 20.dp).padding(bottom = 20.dp).imePadding()) {
            Text("Ask the coach", style = MaterialTheme.typography.titleLarge)
            Spacer(Modifier.height(2.dp))
            Text(
                "Anything about this report — the coach answers and reads it aloud.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(14.dp))

            if (answers.isEmpty() && !asking) {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf(
                        "How do I fix my split-step?",
                        "What should I focus on next session?",
                        "Why is my footwork late?",
                    ).forEach { s ->
                        SuggestionChip(s) { q = s }
                    }
                }
            } else {
                LazyColumn(
                    Modifier.fillMaxWidth().heightIn(max = 420.dp),
                    state = listState,
                    verticalArrangement = Arrangement.spacedBy(14.dp),
                ) {
                    items(answers) { (question, answer) -> QA(question, answer) }
                    if (asking) item { ThinkingBubble() }
                }
            }

            Spacer(Modifier.height(14.dp))
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                OutlinedTextField(
                    value = q,
                    onValueChange = { q = it },
                    modifier = Modifier.weight(1f),
                    placeholder = { Text("Ask a question…") },
                    shape = RoundedCornerShape(24.dp),
                    singleLine = true,
                    maxLines = 1,
                )
                MicButton { q = it }
                FilledIconButton(
                    onClick = { if (q.isNotBlank() && !asking) { onAsk(q); q = "" } },
                    enabled = q.isNotBlank() && !asking,
                    colors = IconButtonDefaults.filledIconButtonColors(
                        containerColor = MaterialTheme.colorScheme.primary,
                        contentColor = Color.White,
                        disabledContainerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.3f),
                        disabledContentColor = Color.White.copy(alpha = 0.6f),
                    ),
                ) {
                    Icon(Icons.AutoMirrored.Filled.Send, contentDescription = "Send")
                }
            }
        }
    }
}

/** A question/answer pair as chat bubbles (you on the right, coach on the left). */
@Composable
private fun QA(question: String, answer: String) {
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
            Box(
                Modifier
                    .widthIn(max = 300.dp)
                    .clip(RoundedCornerShape(16.dp, 16.dp, 4.dp, 16.dp))
                    .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.15f))
                    .padding(12.dp),
            ) {
                Text(question, style = MaterialTheme.typography.bodyMedium)
            }
        }
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.Top) {
            Box(
                Modifier
                    .weight(1f, fill = false)
                    .clip(RoundedCornerShape(16.dp, 16.dp, 16.dp, 4.dp))
                    .background(MaterialTheme.colorScheme.surfaceVariant)
                    .padding(12.dp),
            ) {
                Text(answer, style = MaterialTheme.typography.bodyMedium)
            }
            Spacer(Modifier.width(4.dp))
            SpeakButton(answer)
        }
    }
}

@Composable
private fun ThinkingBubble() {
    Row(Modifier.fillMaxWidth()) {
        Box(
            Modifier
                .clip(RoundedCornerShape(16.dp, 16.dp, 16.dp, 4.dp))
                .background(MaterialTheme.colorScheme.surfaceVariant)
                .padding(horizontal = 14.dp, vertical = 10.dp),
        ) {
            Text("Coach is thinking…", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun SuggestionChip(text: String, onClick: () -> Unit) {
    Box(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(MaterialTheme.colorScheme.surfaceVariant)
            .clickable { onClick() }
            .padding(horizontal = 14.dp, vertical = 12.dp),
    ) {
        Text(text, style = MaterialTheme.typography.bodyMedium)
    }
}

// ---------------------------------------------------------------------------
// Diagnostics
// ---------------------------------------------------------------------------

@Composable
fun DiagnosticsTab(r: Report) {
    val totalTokens = r.usage["total_tokens"]?.toString() ?: "0"
    val timelineStages = r.timeline.mapNotNull { it as? JsonObject }
    val maxSec = timelineStages.mapNotNull { it["seconds"]?.toString()?.toDoubleOrNull() }.maxOrNull() ?: 1.0
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            TspCard(modifier = Modifier.weight(1f), horizontalAlignment = Alignment.CenterHorizontally) {
                Text("${r.calls.size}", style = MaterialTheme.typography.headlineMedium, fontFamily = FontFamily.Monospace)
                Text("MODEL CALLS", style = MaterialTheme.typography.labelSmall, letterSpacing = 1.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            TspCard(modifier = Modifier.weight(1f), horizontalAlignment = Alignment.CenterHorizontally) {
                Text(totalTokens, style = MaterialTheme.typography.headlineMedium, fontFamily = FontFamily.Monospace)
                Text("TOKENS", style = MaterialTheme.typography.labelSmall, letterSpacing = 1.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
        if (timelineStages.isNotEmpty()) {
            TspCard(modifier = Modifier.fillMaxWidth()) {
                SectionLabel("Stage timeline")
                Spacer(Modifier.height(10.dp))
                timelineStages.forEach { o ->
                    val stage = o["stage"]?.toString()?.trim('"').orEmpty()
                    val secs = o["seconds"]?.toString()?.toDoubleOrNull() ?: 0.0
                    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(vertical = 4.dp)) {
                        Text(stage, Modifier.width(130.dp), style = MaterialTheme.typography.bodySmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Box(Modifier.weight(1f).height(10.dp).clip(RoundedCornerShape(5.dp)).background(MaterialTheme.colorScheme.surfaceVariant)) {
                            Box(Modifier.fillMaxWidth((secs / maxSec).toFloat().coerceIn(0f, 1f)).fillMaxHeight().background(MaterialTheme.colorScheme.primary))
                        }
                        Text("${"%.1f".format(secs)}s", Modifier.width(52.dp).padding(start = 8.dp), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        }
        if (r.calls.isNotEmpty()) {
            TspCard(modifier = Modifier.fillMaxWidth()) {
                SectionLabel("Model calls")
                Spacer(Modifier.height(10.dp))
                r.calls.forEach { el ->
                    val o = el as? JsonObject ?: return@forEach
                    Text(
                        "${o["stage"]?.toString()?.trim('"')} · ${o["model"]?.toString()?.trim('"')}",
                        style = MaterialTheme.typography.bodyMedium,
                        fontFamily = FontFamily.Monospace,
                    )
                    Text(
                        "${o["prompt_tokens"]} in / ${o["completion_tokens"]} out · ${o["seconds"]}s",
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = FontFamily.Monospace,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    Spacer(Modifier.height(8.dp))
                }
            }
        }
        if (r.tools.isNotEmpty()) {
            TspCard(modifier = Modifier.fillMaxWidth()) {
                SectionLabel("Tools")
                Spacer(Modifier.height(10.dp))
                r.tools.forEach { el ->
                    val o = el as? JsonObject ?: return@forEach
                    Row {
                        Text("${o["name"]?.toString()?.trim('"')}", Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium, fontFamily = FontFamily.Monospace)
                        Text("${o["seconds"]}s", style = MaterialTheme.typography.bodySmall, fontFamily = FontFamily.Monospace, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        }
    }
}


// ---------------------------------------------------------------------------
// Charts (Compose Canvas)
// ---------------------------------------------------------------------------

private fun fmtTime(s: Double): String {
    if (s <= 0) return "0.0s"
    val minutes = (s / 60).toInt()
    val seconds = s - minutes * 60
    return if (minutes > 0) "%d:%04.1fs".format(minutes, seconds) else "%.1fs".format(seconds)
}

/** Side-to-side legs position over time (the shaded concept is the travel band). */
@Composable
private fun FootworkChart(series: JsonArray) {
    val pts = series.mapNotNull {
        val o = it as? JsonObject ?: return@mapNotNull null
        val t = o["t"]?.toString()?.toDoubleOrNull() ?: return@mapNotNull null
        val x = o["x"]?.toString()?.toDoubleOrNull() ?: return@mapNotNull null
        t to x
    }
    if (pts.size < 2) return
    val t0 = pts.first().first; val t1 = pts.last().first
    val lo = pts.minOf { it.second }; val hi = pts.maxOf { it.second }
    val span = maxOf(0.08, hi - lo)
    val dlo = lo - span * 0.4; val dhi = hi + span * 0.4
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Left–right position", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text("range %.2f–%.2f".format(lo, hi), style = MaterialTheme.typography.labelSmall, fontFamily = FontFamily.Monospace, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        val primaryColor = MaterialTheme.colorScheme.primary
        androidx.compose.foundation.Canvas(Modifier.fillMaxWidth().height(150.dp)) {
            val w = size.width; val h = size.height
            fun xOf(t: Double) = (((t - t0) / (if (t1 - t0 == 0.0) 1.0 else t1 - t0)) * w).toFloat()
            fun yOf(x: Double) = ((dhi - x) / (dhi - dlo) * h).toFloat()
            val path = androidx.compose.ui.graphics.Path()
            pts.forEachIndexed { i, (t, x) ->
                val px = xOf(t); val py = yOf(x)
                if (i == 0) path.moveTo(px, py) else path.lineTo(px, py)
            }
            drawPath(path, color = primaryColor, style = androidx.compose.ui.graphics.drawscope.Stroke(width = 4f))
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("0s", style = MaterialTheme.typography.labelSmall, fontFamily = FontFamily.Monospace, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text("time (s)", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text("%.1fs".format(t1), style = MaterialTheme.typography.labelSmall, fontFamily = FontFamily.Monospace, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun PoseAngleChart(series: JsonArray) {
    val rows = series.mapNotNull { it as? JsonObject }.mapNotNull { o ->
        val t = o["t"]?.toString()?.toDoubleOrNull() ?: return@mapNotNull null
        doubleArrayOf(
            t,
            o["l_knee"]?.toString()?.toDoubleOrNull() ?: Double.NaN,
            o["r_knee"]?.toString()?.toDoubleOrNull() ?: Double.NaN,
            o["l_elbow"]?.toString()?.toDoubleOrNull() ?: Double.NaN,
            o["r_elbow"]?.toString()?.toDoubleOrNull() ?: Double.NaN,
        )
    }
    if (rows.size < 2) return
    val t0 = rows.first()[0]; val t1 = rows.last()[0]
    val primaryColor = MaterialTheme.colorScheme.primary
    val secondaryColor = MaterialTheme.colorScheme.secondary
    val colors = listOf(primaryColor, secondaryColor, Good, Warn)
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Joint angle (°)", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text("0–180°", style = MaterialTheme.typography.labelSmall, fontFamily = FontFamily.Monospace, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        androidx.compose.foundation.Canvas(Modifier.fillMaxWidth().height(150.dp)) {
            val w = size.width; val h = size.height
            fun xOf(t: Double) = (((t - t0) / (if (t1 - t0 == 0.0) 1.0 else t1 - t0)) * w).toFloat()
            fun yOf(v: Double) = (h - (v / 180.0 * h)).toFloat()
            for (k in 1..4) {
                val path = androidx.compose.ui.graphics.Path()
                var started = false
                rows.forEach { row ->
                    val v = row[k]
                    if (!v.isNaN()) {
                        val x = xOf(row[0]); val y = yOf(v)
                        if (!started) { path.moveTo(x, y); started = true } else path.lineTo(x, y)
                    }
                }
                drawPath(path, colors[k - 1], style = androidx.compose.ui.graphics.drawscope.Stroke(width = 3f))
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("0s", style = MaterialTheme.typography.labelSmall, fontFamily = FontFamily.Monospace, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text("time (s)", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text("%.1fs".format(t1), style = MaterialTheme.typography.labelSmall, fontFamily = FontFamily.Monospace, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            listOf("L knee" to primaryColor, "R knee" to secondaryColor, "L elbow" to Good, "R elbow" to Warn).forEach { (label, c) ->
                Row(verticalAlignment = Alignment.CenterVertically) {
                    androidx.compose.foundation.Canvas(Modifier.height(6.dp).width(14.dp)) { drawRect(color = c) }
                    Text(" $label", style = MaterialTheme.typography.bodySmall)
                }
            }
        }
    }
}

@Composable
fun EnergyChart(activity: JsonArray, playhead: Double? = null, onSeek: ((Double) -> Unit)? = null) {
    val pts = activity.mapNotNull {
        val o = it as? JsonObject ?: return@mapNotNull null
        val t = o["t"]?.toString()?.toDoubleOrNull() ?: return@mapNotNull null
        val e = o["energy"]?.toString()?.toDoubleOrNull() ?: return@mapNotNull null
        t to e
    }
    if (pts.size < 2) return
    val t0 = pts.first().first; val t1 = pts.last().first
    val span = if (t1 - t0 == 0.0) 1.0 else t1 - t0
    val maxE = maxOf(1e-3, pts.maxOf { it.second })
    val mod = Modifier.fillMaxWidth().height(130.dp).let { base ->
        if (onSeek != null) base.pointerInput(Unit) {
            detectTapGestures { pos -> onSeek((t0 + (pos.x / size.width) * span).coerceIn(t0, t1)) }
        } else base
    }
    val primaryColor = MaterialTheme.colorScheme.primary
    val secondaryColor = MaterialTheme.colorScheme.secondary
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text(
                "Movement energy",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(
                "peak %.2f".format(maxE),
                style = MaterialTheme.typography.labelSmall,
                fontFamily = FontFamily.Monospace,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        androidx.compose.foundation.Canvas(mod) {
            val w = size.width; val h = size.height
            fun xOf(t: Double) = (((t - t0) / span) * w).toFloat()
            fun yOf(e: Double) = (h - (e / maxE * h)).toFloat()
            val line = androidx.compose.ui.graphics.Path()
            val area = androidx.compose.ui.graphics.Path()
            pts.forEachIndexed { i, (t, e) ->
                val px = xOf(t); val py = yOf(e)
                if (i == 0) { line.moveTo(px, py); area.moveTo(px, h); area.lineTo(px, py) } else { line.lineTo(px, py); area.lineTo(px, py) }
            }
            area.lineTo(xOf(t1), h); area.close()
            drawPath(area, color = primaryColor.copy(alpha = 0.18f))
            drawPath(line, color = primaryColor, style = androidx.compose.ui.graphics.drawscope.Stroke(width = 3f))
            playhead?.let { ph ->
                val px = xOf(ph.coerceIn(t0, t1))
                drawLine(secondaryColor, androidx.compose.ui.geometry.Offset(px, 0f), androidx.compose.ui.geometry.Offset(px, h), strokeWidth = 2f)
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("0s", style = MaterialTheme.typography.labelSmall, fontFamily = FontFamily.Monospace, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text("time (s)", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text("%.1fs".format(t1), style = MaterialTheme.typography.labelSmall, fontFamily = FontFamily.Monospace, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

/** A timeline bar of active spans. */
@Composable
fun SegmentsBar(segments: JsonArray, duration: Double, playhead: Double? = null, onSeek: ((Double) -> Unit)? = null) {
    val spans = segments.mapNotNull {
        val o = it as? JsonObject ?: return@mapNotNull null
        val s = o["start"]?.toString()?.toDoubleOrNull() ?: return@mapNotNull null
        val e = o["end"]?.toString()?.toDoubleOrNull() ?: return@mapNotNull null
        s to e
    }
    if (spans.isEmpty() || duration <= 0) return
    val mod = Modifier.fillMaxWidth().height(30.dp).let { base ->
        if (onSeek != null) base.pointerInput(Unit) {
            detectTapGestures { pos -> onSeek(((pos.x / size.width) * duration).toDouble().coerceIn(0.0, duration)) }
        } else base
    }
    val primaryColor = MaterialTheme.colorScheme.primary
    val secondaryColor = MaterialTheme.colorScheme.secondary
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        androidx.compose.foundation.Canvas(mod) {
            val w = size.width; val h = size.height
            drawRect(color = primaryColor.copy(alpha = 0.15f), size = androidx.compose.ui.geometry.Size(w, h))
            spans.forEach { (s, e) ->
                val x = (s / duration * w).toFloat()
                val ww = ((e - s) / duration * w).toFloat()
                drawRect(
                    color = secondaryColor,
                    topLeft = androidx.compose.ui.geometry.Offset(x, 0f),
                    size = androidx.compose.ui.geometry.Size(ww.coerceAtLeast(2f), h),
                )
            }
            playhead?.let { ph ->
                val px = ((ph / duration) * w).toFloat().coerceIn(0f, w)
                drawLine(secondaryColor, androidx.compose.ui.geometry.Offset(px, 0f), androidx.compose.ui.geometry.Offset(px, h), strokeWidth = 2f)
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("0s", style = MaterialTheme.typography.labelSmall, fontFamily = FontFamily.Monospace, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text("time (s)", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text("%.1fs".format(duration), style = MaterialTheme.typography.labelSmall, fontFamily = FontFamily.Monospace, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

fun lastT(activity: JsonArray): Double =
    activity.mapNotNull { (it as? JsonObject)?.get("t")?.toString()?.toDoubleOrNull() }.maxOrNull() ?: 10.0
