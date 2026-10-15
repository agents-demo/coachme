package com.topspinreview.android.ui.newanalysis

import android.content.Context
import android.graphics.Bitmap
import android.net.Uri
import android.provider.Settings
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.FiniteAnimationSpec
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.horizontalScroll
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
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Movie
import androidx.compose.material.icons.filled.PhotoCamera
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Restore
import androidx.compose.material.icons.filled.Videocam
import androidx.compose.material.icons.filled.WarningAmber
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.ProgressBarRangeInfo
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.progressBarRangeInfo
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import coil.compose.AsyncImage
import com.topspinreview.android.pipeline.PendingRun
import com.topspinreview.android.pipeline.Pipeline
import com.topspinreview.android.pipeline.Sampler
import com.topspinreview.android.pipeline.Stages
import com.topspinreview.android.ui.components.EyebrowPill
import com.topspinreview.android.ui.components.GhostButton
import com.topspinreview.android.ui.components.MetaChip
import com.topspinreview.android.ui.components.PrimaryButton
import com.topspinreview.android.ui.components.SectionLabel
import com.topspinreview.android.ui.components.TspCard
import com.topspinreview.android.ui.components.TspTopBar
import com.topspinreview.android.ui.components.heroBrush
import com.topspinreview.android.ui.theme.Accent
import com.topspinreview.android.ui.theme.Accent2
import com.topspinreview.android.ui.theme.Bad
import com.topspinreview.android.ui.theme.Good
import com.topspinreview.android.ui.theme.Warn
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import javax.inject.Inject
import kotlin.math.roundToInt

@HiltViewModel
class NewAnalysisViewModel @Inject constructor(
    private val pipeline: Pipeline,
    private val sampler: Sampler,
    @ApplicationContext private val context: Context,
) : ViewModel() {
    /** A reviewed-but-not-yet-analyzed source, with the pre-flight facts shown on the confirm card. */
    data class Selection(
        val path: String,
        val name: String,
        val isImage: Boolean,
        val durationSec: Double,
        val width: Int,
        val height: Int,
        val fps: Double,
        val posterPath: String?,
        val warnings: List<String>,
    )

    data class State(
        val running: Boolean = false,
        val loading: Boolean = false,
        val stage: String = "Preparing",
        val stageIndex: Int = -1,
        val stageCount: Int = 0,
        val progress: Float = 0f,
        val nextStage: String? = null,
        val startedAtMs: Long = 0L,
        val stages: List<String> = emptyList(),
        val stepSeconds: Map<String, Double> = emptyMap(),
        val warnings: List<String> = emptyList(),
        val error: String? = null,
        val failedStage: String? = null,
        val canResume: Boolean = false,
        val selection: Selection? = null,
        val pendingRun: PendingRun? = null,
        val useRegion: Boolean = false,
        val region: List<Float> = listOf(0.2f, 0.1f, 0.8f, 0.95f),
        /** Set on a clean success; the screen navigates automatically. */
        val stem: String? = null,
        /** Set on a success that carried warnings; the screen asks the user to continue. */
        val finishedStem: String? = null,
    )

    private val _state = MutableStateFlow(State())
    val state = _state.asStateFlow()
    private var job: Job? = null
    private var lastPath: String? = null
    private var lastRegion: FloatArray? = null
    private var lastIsImage = false
    private var lastStageName: String? = null
    private var lastStageAt = 0L

    init { refreshPending() }

    /** Re-scan disk for an interrupted run (shown as a resume banner). */
    private fun refreshPending() {
        viewModelScope.launch {
            val run = withContext(Dispatchers.IO) { pipeline.pendingRun() }
            _state.value = _state.value.copy(pendingRun = run)
        }
    }

    fun select(uri: Uri) {
        val isImage = context.contentResolver.getType(uri)?.startsWith("image") == true
        val name = queryDisplayName(uri).ifBlank { "Selected clip" }
        loadSelection(name, isImage) { copyToCache(uri) }
    }

    /** Use the clip bundled in assets (like the desktop "use the sample clip"). */
    fun selectSample() = loadSelection("Bundled sample", isImage = false) { copySample() }

    private fun loadSelection(name: String, isImage: Boolean, make: suspend () -> File) {
        job?.cancel()
        job = viewModelScope.launch {
            _state.value = State(loading = true)
            try {
                val file = withContext(Dispatchers.IO) { make() }
                lastPath = file.absolutePath
                lastIsImage = isImage
                val inspection = withContext(Dispatchers.IO) { sampler.inspect(file.absolutePath) }
                val posterPath = withContext(Dispatchers.IO) { savePoster(file.nameWithoutExtension, inspection.poster) }
                _state.value = State(
                    selection = Selection(
                        path = file.absolutePath,
                        name = name,
                        isImage = isImage,
                        durationSec = inspection.durationSec,
                        width = inspection.width,
                        height = inspection.height,
                        fps = inspection.fps,
                        posterPath = posterPath,
                        warnings = inspection.warnings,
                    ),
                )
            } catch (e: CancellationException) {
                _state.value = State()
            } catch (e: Exception) {
                _state.value = State(error = e.message ?: "Could not open that file.")
            }
        }
    }

    fun setUseRegion(value: Boolean) { _state.value = _state.value.copy(useRegion = value) }

    fun setRegionEdge(index: Int, value: Float) {
        val r = _state.value.region.toMutableList()
        if (index in r.indices) {
            r[index] = value.coerceIn(0f, 1f)
            _state.value = _state.value.copy(region = r)
        }
    }

    fun start() {
        val sel = _state.value.selection ?: return
        val box = if (_state.value.useRegion) _state.value.region.toFloatArray() else null
        lastRegion = box
        launchRun(box, sel.isImage, resume = false) { File(sel.path) }
    }

    fun retry() {
        val path = lastPath ?: return
        launchRun(lastRegion, lastIsImage, resume = false) { File(path) }
    }

    /** Continue the just-failed run from its checkpoint. */
    fun resume() {
        val path = lastPath ?: return
        launchRun(lastRegion, lastIsImage, resume = true) { File(path) }
    }

    /** Continue an interrupted run by stem (used when the Sessions screen hands one over). */
    fun resumeStem(stem: String) {
        val run = pipeline.pendingRunFor(stem) ?: return
        resumeRun(run)
    }

    /** Continue an interrupted run discovered on disk (restoring its crop region too). */
    fun resumeRun(run: PendingRun) {
        val region = run.region.takeIf { it.size == 4 }
        lastPath = run.videoPath
        lastIsImage = run.isImage
        lastRegion = region?.toFloatArray()
        if (region != null) _state.value = _state.value.copy(useRegion = true, region = region)
        launchRun(region?.toFloatArray(), run.isImage, resume = true) { File(run.videoPath) }
    }

    fun discard() {
        job?.cancel()
        _state.value = State()
        refreshPending()
    }

    fun discardRun(stem: String) {
        viewModelScope.launch {
            withContext(Dispatchers.IO) { pipeline.discardRun(stem) }
            refreshPending()
        }
    }

    fun cancel() {
        job?.cancel()
        _state.value = State()
        refreshPending()
    }

    private fun launchRun(regionBox: FloatArray?, isImage: Boolean, resume: Boolean = false, prepare: suspend () -> File) {
        job = viewModelScope.launch {
            val plan = Stages.plan(isImage)
            _state.value = _state.value.copy(
                running = true,
                loading = false,
                stage = "Preparing",
                stageIndex = -1,
                stageCount = plan.size,
                progress = 0f,
                nextStage = plan.firstOrNull(),
                startedAtMs = System.currentTimeMillis(),
                stages = plan,
                stepSeconds = emptyMap(),
                warnings = emptyList(),
                error = null,
                failedStage = null,
                canResume = false,
                pendingRun = null,
                stem = null,
                finishedStem = null,
            )
            val warnings = mutableListOf<String>()
            lastStageName = "Prepare clip"
            lastStageAt = System.currentTimeMillis()
            try {
                val file = prepare()
                lastPath = file.absolutePath
                val report = withContext(Dispatchers.Default) {
                    pipeline.analyze(
                        videoPath = file.absolutePath,
                        regionBox = regionBox,
                        resume = resume,
                        onStage = { s ->
                            val now = System.currentTimeMillis()
                            val prev = lastStageName
                            val times = if (prev != null && lastStageAt > 0) {
                                _state.value.stepSeconds + (prev to (now - lastStageAt) / 1000.0)
                            } else _state.value.stepSeconds
                            lastStageName = s.name
                            lastStageAt = now
                            _state.value = _state.value.copy(
                                stage = s.name,
                                stageIndex = s.index,
                                stageCount = s.total,
                                progress = s.progress,
                                nextStage = s.next,
                                stepSeconds = times,
                            )
                        },
                        onWarning = { w ->
                            if (w !in warnings) {
                                warnings += w
                                _state.value = _state.value.copy(warnings = warnings.toList())
                            }
                        },
                    )
                }
                val stem = report.stem.ifBlank { file.nameWithoutExtension }
                _state.value = if (warnings.isEmpty()) {
                    State(stem = stem)
                } else {
                    State(finishedStem = stem, warnings = warnings.toList())
                }
            } catch (e: CancellationException) {
                _state.value = _state.value.copy(running = false)
            } catch (e: Exception) {
                _state.value = _state.value.copy(
                    running = false,
                    error = e.message ?: "Analysis failed",
                    failedStage = _state.value.stage,
                    warnings = warnings.toList(),
                    canResume = lastPath?.let { pipeline.hasCheckpoint(it) } ?: false,
                )
            }
        }
    }

    private fun savePoster(stem: String, bitmap: Bitmap?): String? {
        if (bitmap == null) return null
        return runCatching {
            val dir = File(context.filesDir, "media").apply { mkdirs() }
            val f = File(dir, "${sanitize(stem)}_poster.jpg")
            f.outputStream().use { bitmap.compress(Bitmap.CompressFormat.JPEG, 85, it) }
            f.absolutePath
        }.getOrNull()
    }

    private suspend fun copySample(): File = withContext(Dispatchers.IO) {
        val dir = File(context.filesDir, "media").apply { mkdirs() }
        val out = File(dir, "sample.mp4")
        context.assets.open("sample.mp4").use { input -> out.outputStream().use { input.copyTo(it) } }
        out
    }

    private suspend fun copyToCache(uri: Uri): File = withContext(Dispatchers.IO) {
        val raw = queryDisplayName(uri)
        val mime = context.contentResolver.getType(uri).orEmpty()
        val fallbackExt = if (mime.startsWith("image")) "jpg" else "mp4"
        val base = raw.substringBeforeLast('.', raw).ifBlank { "input_${System.currentTimeMillis()}" }
        val ext = raw.substringAfterLast('.', "").lowercase().ifBlank { fallbackExt }
        val dir = File(context.filesDir, "media").apply { mkdirs() }
        val out = File(dir, "${sanitize(base)}.$ext")
        context.contentResolver.openInputStream(uri)?.use { input -> out.outputStream().use { input.copyTo(it) } }
        out
    }

    /** The human-readable file name behind a content:// URI (e.g. "Michael-Osher.mp4"). */
    private fun queryDisplayName(uri: Uri): String {
        val projection = arrayOf(android.provider.OpenableColumns.DISPLAY_NAME)
        context.contentResolver.query(uri, projection, null, null, null)?.use { c ->
            if (c.moveToFirst()) {
                val idx = c.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
                if (idx >= 0) c.getString(idx)?.takeIf { it.isNotBlank() }?.let { return it }
            }
        }
        return ""
    }

    private fun sanitize(name: String): String =
        name.replace(Regex("[^A-Za-z0-9._-]"), "_").trim('_').trim('.').ifBlank { "clip" }
}

@Composable
fun NewAnalysisScreen(
    onDone: (String) -> Unit,
    onBack: () -> Unit,
    resumeStem: String? = null,
    vm: NewAnalysisViewModel = hiltViewModel(),
) {
    val state by vm.state.collectAsStateWithLifecycle()

    val useRegion = state.useRegion
    val region = state.region

    val picker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) vm.select(uri)
    }

    LaunchedEffect(state.stem) { state.stem?.let(onDone) }

    LaunchedEffect(resumeStem) { if (resumeStem != null) vm.resumeStem(resumeStem) }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = { TspTopBar(onBack = onBack) },
    ) { pad ->
        Column(
            Modifier.fillMaxSize().padding(pad).verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Stagger(0) { AnalyzeHeader() }

            val sel = state.selection
            val finishedStem = state.finishedStem
            when {
                state.running -> Stagger(1) { RunningPanel(state = state, onCancel = vm::cancel) }

                finishedStem != null -> Stagger(1) {
                    CompletionPanel(warnings = state.warnings, onView = { onDone(finishedStem) })
                }

                state.loading -> Stagger(1) { LoadingPanel() }

                sel != null -> Stagger(1) {
                    PreviewPanel(
                        selection = sel,
                        useRegion = useRegion,
                        onToggle = vm::setUseRegion,
                        left = region[0], top = region[1], right = region[2], bottom = region[3],
                        onLeft = { vm.setRegionEdge(0, it) }, onTop = { vm.setRegionEdge(1, it) },
                        onRight = { vm.setRegionEdge(2, it) }, onBottom = { vm.setRegionEdge(3, it) },
                        onStart = vm::start,
                        onDiscard = { vm.discard() },
                    )
                }

                else -> {
                    Stagger(1) {
                        CapturePanel(
                            onVideo = { picker.launch("video/*") },
                            onPhoto = { picker.launch("image/*") },
                            onSample = { vm.selectSample() },
                        )
                    }
                    state.pendingRun?.let { run ->
                        Stagger(2) {
                            ResumeBanner(
                                run = run,
                                onResume = { vm.resumeRun(run) },
                                onDiscard = { vm.discardRun(run.stem) },
                            )
                        }
                    }
                }
            }

            state.error?.let { err ->
                Stagger(3) {
                    ErrorPanel(
                        message = err,
                        failedStage = state.failedStage,
                        warnings = state.warnings,
                        canResume = state.canResume,
                        onResume = vm::resume,
                        onRetry = vm::retry,
                    )
                }
            }
        }
    }
}

@Composable
private fun rememberReducedMotion(): Boolean {
    val context = LocalContext.current
    return remember {
        Settings.Global.getFloat(context.contentResolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f) == 0f
    }
}

@Composable
private fun Stagger(index: Int, content: @Composable () -> Unit) {
    val reduced = rememberReducedMotion()
    var shown by remember { mutableStateOf(reduced) }
    LaunchedEffect(Unit) {
        if (!reduced) {
            delay(index * 55L)
            shown = true
        }
    }
    val spec: FiniteAnimationSpec<Float> = if (reduced) tween(0) else tween(340, easing = FastOutSlowInEasing)
    val alpha by animateFloatAsState(if (shown) 1f else 0f, spec, label = "staggerA")
    val ty by animateFloatAsState(if (shown) 0f else 16f, spec, label = "staggerY")
    Box(Modifier.graphicsLayer { this.alpha = alpha; translationY = ty }) { content() }
}

@Composable
private fun AnalyzeHeader() {
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        EyebrowPill("Topspin Review")
        Text(
            "Analyze a clip",
            style = MaterialTheme.typography.displaySmall.copy(brush = heroBrush()),
        )
        Text(
            "Frames are measured on your phone. Only the sampled frames and metrics ever reach the model.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Row(
            Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            MetaChip("Pose")
            MetaChip("Ball")
            MetaChip("Footwork")
            MetaChip("Private", color = Good, border = Good.copy(alpha = 0.45f))
        }
    }
}

@Composable
private fun CapturePanel(
    onVideo: () -> Unit,
    onPhoto: () -> Unit,
    onSample: () -> Unit,
) {
    TspCard(modifier = Modifier.fillMaxWidth(), padding = PaddingValues(0.dp)) {
        Box(
            Modifier
                .fillMaxWidth()
                .background(
                    Brush.verticalGradient(
                        listOf(Accent.copy(alpha = 0.16f), Color.Transparent, Accent2.copy(alpha = 0.10f)),
                    ),
                ),
        ) {
            Column(
                Modifier.fillMaxWidth().padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        Modifier.size(54.dp).clip(RoundedCornerShape(17.dp)).background(heroBrush()),
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(Icons.Filled.Videocam, contentDescription = null, tint = Color.White, modifier = Modifier.size(28.dp))
                    }
                    Spacer(Modifier.width(14.dp))
                    Column(Modifier.weight(1f)) {
                        Text("Add footage", style = MaterialTheme.typography.titleLarge)
                        Text(
                            "A full clip or a single still — analyzed end to end",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }

                PrimaryButton(
                    "Choose a video",
                    onVideo,
                    Modifier.fillMaxWidth(),
                    icon = { Icon(Icons.Filled.PlayArrow, contentDescription = null, modifier = Modifier.size(18.dp)) },
                )

                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    ActionButton("Photo", Icons.Filled.PhotoCamera, onPhoto, Modifier.weight(1f))
                    ActionButton("Sample clip", Icons.Filled.Movie, onSample, Modifier.weight(1f))
                }
            }
        }
    }
}

@Composable
private fun ActionButton(label: String, icon: ImageVector, onClick: () -> Unit, modifier: Modifier = Modifier) {
    OutlinedButton(
        onClick = onClick,
        modifier = modifier.height(48.dp),
        shape = RoundedCornerShape(10.dp),
        border = BorderStroke(2.dp, MaterialTheme.colorScheme.outline),
        colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.onSurface),
    ) {
        Icon(icon, contentDescription = null, modifier = Modifier.size(18.dp))
        Spacer(Modifier.width(8.dp))
        Text(label, style = MaterialTheme.typography.labelLarge, maxLines = 1)
    }
}

@Composable
private fun LoadingPanel() {
    TspCard(modifier = Modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            CircularProgressIndicator(color = Accent, strokeWidth = 2.dp, modifier = Modifier.size(20.dp))
            Spacer(Modifier.width(12.dp))
            Text("Preparing clip…", style = MaterialTheme.typography.titleMedium)
        }
        Spacer(Modifier.height(6.dp))
        Text(
            "Reading the file and grabbing a preview frame.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun ResumeBanner(run: PendingRun, onResume: () -> Unit, onDiscard: () -> Unit) {
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
        PrimaryButton(
            "Resume",
            onResume,
            Modifier.fillMaxWidth(),
            icon = { Icon(Icons.Filled.PlayArrow, contentDescription = null, modifier = Modifier.size(18.dp)) },
        )
        Spacer(Modifier.height(2.dp))
        TextButton(
            onClick = onDiscard,
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
            colors = ButtonDefaults.textButtonColors(contentColor = MaterialTheme.colorScheme.onSurfaceVariant),
        ) {
            Text("Discard this run", style = MaterialTheme.typography.labelLarge)
        }
    }
}

@Composable
private fun PreviewPanel(
    selection: NewAnalysisViewModel.Selection,
    useRegion: Boolean,
    onToggle: (Boolean) -> Unit,
    left: Float, top: Float, right: Float, bottom: Float,
    onLeft: (Float) -> Unit, onTop: (Float) -> Unit, onRight: (Float) -> Unit, onBottom: (Float) -> Unit,
    onStart: () -> Unit,
    onDiscard: () -> Unit,
) {
    val aspect = if (selection.width > 0 && selection.height > 0) {
        (selection.width.toFloat() / selection.height).coerceIn(0.5f, 2.2f)
    } else 16f / 9f
    val facts = buildList {
        formatDuration(selection.durationSec)?.let { add(it) }
        if (selection.width > 0) add("${selection.width}×${selection.height}")
        if (selection.fps > 0.1) add("${selection.fps.roundToInt()} fps")
    }

    TspCard(modifier = Modifier.fillMaxWidth()) {
        SectionLabel("Ready to analyze")
        Spacer(Modifier.height(12.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                Modifier.size(64.dp).clip(RoundedCornerShape(14.dp))
                    .background(Brush.linearGradient(listOf(Accent.copy(alpha = 0.35f), Accent2.copy(alpha = 0.35f)))),
                contentAlignment = Alignment.Center,
            ) {
                if (selection.posterPath != null) {
                    AsyncImage(
                        model = File(selection.posterPath),
                        contentDescription = null,
                        contentScale = ContentScale.Crop,
                        modifier = Modifier.fillMaxSize(),
                    )
                } else {
                    Icon(
                        if (selection.isImage) Icons.Filled.PhotoCamera else Icons.Filled.Movie,
                        contentDescription = null, tint = Color.White, modifier = Modifier.size(28.dp),
                    )
                }
            }
            Spacer(Modifier.width(14.dp))
            Column(Modifier.weight(1f)) {
                Text(selection.name, style = MaterialTheme.typography.titleMedium, maxLines = 1)
                Text(
                    if (selection.isImage) "Single photo · posture analysis"
                    else facts.ifEmpty { listOf("Video · full breakdown") }.joinToString(" · "),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1,
                )
            }
        }

        if (selection.warnings.isNotEmpty()) {
            Spacer(Modifier.height(10.dp))
            selection.warnings.forEach { WarningRow(it) }
        }

        Spacer(Modifier.height(16.dp))
        CropSection(
            useRegion = useRegion, onToggle = onToggle,
            left = left, top = top, right = right, bottom = bottom,
            onLeft = onLeft, onTop = onTop, onRight = onRight, onBottom = onBottom,
            enabled = true, aspect = aspect, posterPath = selection.posterPath,
        )

        Spacer(Modifier.height(18.dp))
        PrimaryButton(
            "Start analysis",
            onStart,
            Modifier.fillMaxWidth(),
            icon = { Icon(Icons.Filled.PlayArrow, contentDescription = null, modifier = Modifier.size(18.dp)) },
        )
        Spacer(Modifier.height(2.dp))
        TextButton(
            onClick = onDiscard,
            modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp),
            colors = ButtonDefaults.textButtonColors(contentColor = MaterialTheme.colorScheme.onSurfaceVariant),
        ) {
            Text("Choose a different clip", style = MaterialTheme.typography.labelLarge)
        }
    }
}

@Composable
private fun RunningPanel(state: NewAnalysisViewModel.State, onCancel: () -> Unit) {
    val reduced = rememberReducedMotion()
    val progress by animateFloatAsState(state.progress, tween(if (reduced) 0 else 450, easing = FastOutSlowInEasing), label = "progress")
    val index = state.stageIndex

    var nowMs by remember { mutableStateOf(System.currentTimeMillis()) }
    LaunchedEffect(Unit) {
        while (true) {
            nowMs = System.currentTimeMillis()
            delay(1000)
        }
    }
    val elapsedSec = if (state.startedAtMs > 0) (nowMs - state.startedAtMs) / 1000 else 0L

    TspCard(modifier = Modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            PulsingDot()
            Spacer(Modifier.width(10.dp))
            Text("Analyzing", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.width(8.dp))
            Text(
                formatDuration(elapsedSec.toDouble()) ?: "0:00",
                style = MaterialTheme.typography.bodySmall,
                fontFamily = FontFamily.Monospace,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.weight(1f))
            Text("${(progress * 100).toInt()}%", style = MaterialTheme.typography.titleMedium, color = Accent)
        }
        Spacer(Modifier.height(12.dp))
        LiveProgress(progress)
        if (state.stages.isNotEmpty()) {
            Spacer(Modifier.height(14.dp))
            val steps = buildList {
                add("Prepare clip" to -1)
                state.stages.forEachIndexed { i, name -> add(name to i) }
            }
            STAGE_GROUP_ORDER.forEach { group ->
                val items = steps.filter { stageGroupOf(it.first) == group }
                if (items.isNotEmpty()) {
                    Spacer(Modifier.height(9.dp))
                    Text(
                        group.uppercase(),
                        style = MaterialTheme.typography.labelSmall,
                        letterSpacing = 1.sp,
                        color = Accent,
                    )
                    Spacer(Modifier.height(2.dp))
                    items.forEach { (name, planIndex) ->
                        val phase = when {
                            planIndex < 0 -> if (index < 0) 1 else 0
                            index >= 0 && planIndex < index -> 0
                            planIndex == index -> 1
                            else -> 2
                        }
                        StageRow(
                            label = name,
                            phase = phase,
                            seconds = if (phase == 0) state.stepSeconds[name] else null,
                        )
                    }
                }
            }
        } else {
            Spacer(Modifier.height(12.dp))
            Text(state.stage.ifBlank { "Working" }, style = MaterialTheme.typography.titleSmall)
        }
        if (state.warnings.isNotEmpty()) {
            Spacer(Modifier.height(10.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Filled.WarningAmber, contentDescription = null, tint = Warn, modifier = Modifier.size(16.dp))
                Spacer(Modifier.width(8.dp))
                Text(
                    "${state.warnings.size} caveat${if (state.warnings.size == 1) "" else "s"} so far",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
        Spacer(Modifier.height(18.dp))
        GhostButton("Cancel", onCancel, Modifier.fillMaxWidth())
    }
}

@Composable
private fun StageRow(label: String, phase: Int, seconds: Double? = null) {
    val done = phase == 0
    val active = phase == 1
    Row(
        Modifier
            .fillMaxWidth()
            .padding(vertical = 3.dp)
            .clearAndSetSemantics {
                val state = when {
                    done -> "done"
                    active -> "in progress"
                    else -> "pending"
                }
                contentDescription = "$label, $state" + (seconds?.let { ", took ${"%.1f".format(it)} seconds" } ?: "")
            },
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(Modifier.size(18.dp), contentAlignment = Alignment.Center) {
            when {
                done -> Icon(Icons.Filled.Check, contentDescription = null, tint = Good, modifier = Modifier.size(16.dp))
                active -> PulsingDot(size = 10.dp, color = Accent)
                else -> Box(Modifier.size(7.dp).clip(CircleShape).background(MaterialTheme.colorScheme.outline))
            }
        }
        Spacer(Modifier.width(10.dp))
        Text(
            label,
            Modifier.weight(1f),
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = if (active) FontWeight.SemiBold else FontWeight.Normal,
            color = when {
                active -> MaterialTheme.colorScheme.onSurface
                done -> MaterialTheme.colorScheme.onSurfaceVariant
                else -> MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.55f)
            },
        )
        if (seconds != null && done) {
            Text(
                "%.1fs".format(seconds),
                style = MaterialTheme.typography.labelSmall,
                fontFamily = FontFamily.Monospace,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun CompletionPanel(warnings: List<String>, onView: () -> Unit) {
    TspCard(modifier = Modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Filled.WarningAmber, contentDescription = null, tint = Warn, modifier = Modifier.size(20.dp))
            Spacer(Modifier.width(10.dp))
            Text("Report ready — with caveats", style = MaterialTheme.typography.titleMedium)
        }
        Spacer(Modifier.height(6.dp))
        Text(
            "A few steps were skipped or the footage was limited, so some findings may be more general than usual.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        if (warnings.isNotEmpty()) {
            Spacer(Modifier.height(12.dp))
            warnings.forEach { WarningRow(it) }
        }
        Spacer(Modifier.height(18.dp))
        PrimaryButton("View report", onView, Modifier.fillMaxWidth())
    }
}

@Composable
private fun WarningRow(text: String) {
    Row(Modifier.fillMaxWidth().padding(vertical = 3.dp), verticalAlignment = Alignment.Top) {
        Box(Modifier.padding(top = 5.dp).size(6.dp).clip(CircleShape).background(Warn))
        Spacer(Modifier.width(8.dp))
        Text(
            text,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun CropSection(
    useRegion: Boolean,
    onToggle: (Boolean) -> Unit,
    left: Float, top: Float, right: Float, bottom: Float,
    onLeft: (Float) -> Unit, onTop: (Float) -> Unit, onRight: (Float) -> Unit, onBottom: (Float) -> Unit,
    enabled: Boolean,
    aspect: Float,
    posterPath: String?,
) {
    Column {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("Only look at me", style = MaterialTheme.typography.titleMedium)
                Text(
                    "Crop the frame to your body",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Switch(
                checked = useRegion,
                onCheckedChange = onToggle,
                enabled = enabled,
                colors = SwitchDefaults.colors(checkedTrackColor = Accent),
            )
        }
        AnimatedVisibility(
            visible = useRegion,
            enter = expandVertically() + fadeIn(),
            exit = shrinkVertically() + fadeOut(),
        ) {
            Column {
                Spacer(Modifier.height(12.dp))
                CropPreview(
                    left = left, top = top, right = right, bottom = bottom,
                    aspect = aspect, posterPath = posterPath,
                    onMove = { dx, dy ->
                        val w = right - left
                        val h = bottom - top
                        val nl = (left + dx).coerceIn(0f, 1f - w)
                        val nt = (top + dy).coerceIn(0f, 1f - h)
                        onLeft(nl); onTop(nt); onRight(nl + w); onBottom(nt + h)
                    },
                )
                Spacer(Modifier.height(6.dp))
                Text(
                    "Drag the box to reposition it, or fine-tune with the sliders.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Spacer(Modifier.height(4.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    TextButton(
                        onClick = { onLeft(0.28f); onTop(0.03f); onRight(0.72f); onBottom(0.98f) },
                        modifier = Modifier.heightIn(min = 48.dp),
                        colors = ButtonDefaults.textButtonColors(contentColor = Accent),
                    ) {
                        Icon(Icons.Filled.AutoAwesome, contentDescription = null, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(6.dp))
                        Text("Detect me", style = MaterialTheme.typography.labelLarge)
                    }
                    TextButton(
                        onClick = { onLeft(0f); onTop(0f); onRight(1f); onBottom(1f) },
                        modifier = Modifier.heightIn(min = 48.dp),
                        colors = ButtonDefaults.textButtonColors(contentColor = MaterialTheme.colorScheme.onSurfaceVariant),
                    ) {
                        Text("Full frame", style = MaterialTheme.typography.labelLarge)
                    }
                }
                RegionSlider("Left", left, onLeft, enabled)
                RegionSlider("Top", top, onTop, enabled)
                RegionSlider("Right", right, onRight, enabled)
                RegionSlider("Bottom", bottom, onBottom, enabled)
            }
        }
    }
}

@Composable
private fun CropPreview(
    left: Float, top: Float, right: Float, bottom: Float,
    aspect: Float,
    posterPath: String?,
    modifier: Modifier = Modifier,
    onMove: ((Float, Float) -> Unit)? = null,
) {
    var boxSize by remember { mutableStateOf(IntSize.Zero) }
    val move = rememberUpdatedState(onMove)

    Box(
        modifier
            .fillMaxWidth()
            .aspectRatio(aspect)
            .clip(RoundedCornerShape(14.dp))
            .background(MaterialTheme.colorScheme.surfaceVariant)
            .onSizeChanged { boxSize = it }
            .semantics { contentDescription = "Crop region — drag to move the area that is analyzed" }
            .pointerInput(Unit) {
                detectDragGestures { change, drag ->
                    change.consume()
                    if (boxSize.width > 0 && boxSize.height > 0) {
                        move.value?.invoke(drag.x / boxSize.width, drag.y / boxSize.height)
                    }
                }
            },
    ) {
        if (posterPath != null) {
            AsyncImage(
                model = File(posterPath),
                contentDescription = null,
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize(),
            )
        } else {
            Icon(
                Icons.Filled.Videocam,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.22f),
                modifier = Modifier.align(Alignment.Center).size(40.dp),
            )
        }
        Canvas(Modifier.fillMaxSize()) {
            val l = size.width * left
            val t = size.height * top
            val r = size.width * right
            val b = size.height * bottom
            val w = r - l
            val h = b - t
            val dim = Color.Black.copy(alpha = 0.5f)

            drawRect(dim, Offset(0f, 0f), Size(size.width, t))
            drawRect(dim, Offset(0f, b), Size(size.width, size.height - b))
            drawRect(dim, Offset(0f, t), Size(l, h))
            drawRect(dim, Offset(r, t), Size(size.width - r, h))

            val grid = Color.White.copy(alpha = 0.16f)
            for (i in 1..2) {
                val gx = l + w * i / 3f
                val gy = t + h * i / 3f
                drawLine(grid, Offset(gx, t), Offset(gx, b), 1f)
                drawLine(grid, Offset(l, gy), Offset(r, gy), 1f)
            }

            drawRect(Accent, Offset(l, t), Size(w, h), style = Stroke(2f))

            val len = (minOf(w, h) * 0.16f).coerceAtMost(w * 0.35f).coerceAtLeast(8f)
            val brackets = listOf(
                floatArrayOf(l, t, 1f, 1f),
                floatArrayOf(r, t, -1f, 1f),
                floatArrayOf(l, b, 1f, -1f),
                floatArrayOf(r, b, -1f, -1f),
            )
            for (c in brackets) {
                val cx = c[0]; val cy = c[1]; val sx = c[2]; val sy = c[3]
                drawLine(Accent, Offset(cx, cy), Offset(cx + sx * len, cy), 3f)
                drawLine(Accent, Offset(cx, cy), Offset(cx, cy + sy * len), 3f)
            }
        }
    }
}

@Composable
private fun RegionSlider(label: String, value: Float, onChange: (Float) -> Unit, enabled: Boolean) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text(
            label,
            Modifier.width(58.dp),
            style = MaterialTheme.typography.bodySmall,
            fontWeight = FontWeight.Medium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Slider(
            value = value,
            onValueChange = onChange,
            enabled = enabled,
            valueRange = 0f..1f,
            modifier = Modifier.weight(1f),
            colors = SliderDefaults.colors(
                thumbColor = Accent,
                activeTrackColor = Accent,
                inactiveTrackColor = MaterialTheme.colorScheme.surfaceVariant,
            ),
        )
    }
}

@Composable
private fun ErrorPanel(
    message: String,
    failedStage: String?,
    warnings: List<String>,
    canResume: Boolean,
    onResume: () -> Unit,
    onRetry: () -> Unit,
) {
    val context = LocalContext.current
    val clipboard = LocalClipboardManager.current
    val friendly = friendlyError(message)

    TspCard(modifier = Modifier.fillMaxWidth()) {
        SectionLabel("Analysis failed", color = Bad)
        if (failedStage != null) {
            Spacer(Modifier.height(6.dp))
            Text(
                "Stopped at: $failedStage",
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.Medium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Spacer(Modifier.height(6.dp))
        Text(friendly, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        if (friendly != message) {
            TextButton(
                onClick = {
                    clipboard.setText(AnnotatedString(message))
                    Toast.makeText(context, "Details copied", Toast.LENGTH_SHORT).show()
                },
                modifier = Modifier.heightIn(min = 48.dp),
                colors = ButtonDefaults.textButtonColors(contentColor = MaterialTheme.colorScheme.onSurfaceVariant),
            ) {
                Text("Copy details", style = MaterialTheme.typography.labelLarge)
            }
        }
        if (warnings.isNotEmpty()) {
            Spacer(Modifier.height(10.dp))
            warnings.forEach { WarningRow(it) }
        }
        Spacer(Modifier.height(14.dp))
        if (canResume) {
            PrimaryButton("Resume", onResume, Modifier.fillMaxWidth())
            Spacer(Modifier.height(8.dp))
            GhostButton("Start over", onRetry, Modifier.fillMaxWidth())
            Spacer(Modifier.height(6.dp))
            Text(
                "Resume continues from where it stopped — finished steps aren't repeated. Start over runs everything again.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        } else {
            PrimaryButton("Start over", onRetry, Modifier.fillMaxWidth())
            Spacer(Modifier.height(6.dp))
            Text(
                "Runs the full pipeline again from the start.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun LiveProgress(fraction: Float, modifier: Modifier = Modifier) {
    val reduced = rememberReducedMotion()
    val inf = rememberInfiniteTransition(label = "live")
    val animated by inf.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(1400, easing = LinearEasing)),
        label = "phase",
    )
    val phase = if (reduced) 0f else animated
    Box(
        modifier
            .fillMaxWidth()
            .height(10.dp)
            .clip(CircleShape)
            .background(MaterialTheme.colorScheme.surfaceVariant)
            .semantics { progressBarRangeInfo = ProgressBarRangeInfo(fraction.coerceIn(0f, 1f), 0f..1f) },
    ) {
        Box(
            Modifier
                .fillMaxWidth(fraction.coerceIn(0f, 1f))
                .height(10.dp)
                .clip(CircleShape)
                .background(
                    Brush.linearGradient(
                        colors = listOf(Accent, Accent2, Color.White.copy(alpha = 0.55f), Accent2, Accent),
                        start = Offset(-400f + phase * 900f, 0f),
                        end = Offset(phase * 900f, 240f),
                    ),
                ),
        )
    }
}

@Composable
private fun PulsingDot(size: Dp = 10.dp, color: Color = Good) {
    val reduced = rememberReducedMotion()
    val inf = rememberInfiniteTransition(label = "pulse")
    val animated by inf.animateFloat(
        initialValue = 0.35f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            tween(850, easing = FastOutSlowInEasing),
            RepeatMode.Reverse,
        ),
        label = "alpha",
    )
    val a = if (reduced) 1f else animated
    Box(Modifier.size(size).clip(CircleShape).background(color.copy(alpha = a)))
}

/** The coarse pipeline stages each step belongs to (mirrors gui2's STEP_GROUP/GROUP_ORDER). */
private val STAGE_GROUP_ORDER = listOf("Setup", "Measure", "Vision (observe)", "Report (coach)")

private fun stageGroupOf(step: String): String = when (step) {
    "Prepare clip" -> "Setup"
    "Pick frames", "Measure movement", "Estimate pose", "Track ball", "Render images" -> "Measure"
    "First look", "Review image", "Detailed findings" -> "Vision (observe)"
    else -> "Report (coach)"
}

private fun formatDuration(seconds: Double): String? {
    if (seconds <= 0.1) return null
    val total = seconds.roundToInt()
    return "%d:%02d".format(total / 60, total % 60)
}

private fun friendlyError(raw: String): String {
    val lower = raw.lowercase()
    return when {
        "network" in lower || "unreachable" in lower || "failed to connect" in lower || "host" in lower ->
            "We couldn't reach the model service. Check the phone's internet connection (or Private DNS) and try again."
        lower.startsWith("http 401") || lower.startsWith("http 403") ->
            "The model service rejected the request. Check the API key in Settings."
        lower.startsWith("http 429") ->
            "The model service is rate-limiting right now. Wait a moment and try again."
        lower.startsWith("http 5") ->
            "The model service had a temporary problem. Try again in a moment."
        lower.startsWith("http 4") ->
            "The model service returned an error. Check your account and API settings."
        "no frames" in lower ->
            "We couldn't read any frames from that clip. Try a different file."
        "could not read the image" in lower ->
            "We couldn't open that photo. Try a different file."
        else -> raw
    }
}
