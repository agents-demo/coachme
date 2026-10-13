package com.topspinreview.android.ui.newanalysis

import android.content.Context
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import com.topspinreview.android.pipeline.Pipeline
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import javax.inject.Inject

@HiltViewModel
class NewAnalysisViewModel @Inject constructor(
    private val pipeline: Pipeline,
    @ApplicationContext private val context: Context,
) : ViewModel() {
    data class State(
        val running: Boolean = false, val stage: String = "",
        val stem: String? = null, val error: String? = null,
    )

    private val _state = MutableStateFlow(State())
    val state = _state.asStateFlow()
    private var job: Job? = null
    private var lastUri: Uri? = null
    private var lastRegion: FloatArray? = null

    fun analyze(uri: Uri, regionBox: FloatArray?) {
        lastUri = uri; lastRegion = regionBox
        job = viewModelScope.launch {
            _state.value = State(running = true, stage = "Preparing")
            try {
                val file = copyToCache(uri)
                val report = pipeline.analyze(file.absolutePath, regionBox) { stage ->
                    _state.value = _state.value.copy(stage = stage)
                }
                _state.value = State(stem = report.stem.ifBlank { file.nameWithoutExtension })
            } catch (e: CancellationException) {
                _state.value = State()
            } catch (e: Exception) {
                _state.value = State(error = e.message ?: "Analysis failed")
            }
        }
    }

    fun cancel() { job?.cancel(); _state.value = State() }

    fun retry() { lastUri?.let { analyze(it, lastRegion) } }

    /** Analyze the clip bundled in assets (like the desktop "use the sample clip"). */
    fun analyzeSample(regionBox: FloatArray?) {
        job = viewModelScope.launch {
            _state.value = State(running = true, stage = "Preparing")
            try {
                val file = withContext(Dispatchers.IO) {
                    val out = File(context.cacheDir, "sample.mp4")
                    context.assets.open("sample.mp4").use { input -> out.outputStream().use { input.copyTo(it) } }
                    out
                }
                val report = pipeline.analyze(file.absolutePath, regionBox) { stage ->
                    _state.value = _state.value.copy(stage = stage)
                }
                _state.value = State(stem = report.stem.ifBlank { file.nameWithoutExtension })
            } catch (e: CancellationException) {
                _state.value = State()
            } catch (e: Exception) {
                _state.value = State(error = e.message ?: "Analysis failed")
            }
        }
    }

    private suspend fun copyToCache(uri: Uri): File = withContext(Dispatchers.IO) {
        val mime = context.contentResolver.getType(uri).orEmpty()
        val ext = if (mime.startsWith("image")) "jpg" else "mp4"
        val out = File(context.cacheDir, "input_${System.currentTimeMillis()}.$ext")
        context.contentResolver.openInputStream(uri)?.use { input -> out.outputStream().use { input.copyTo(it) } }
        out
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NewAnalysisScreen(onDone: (String) -> Unit, onBack: () -> Unit, vm: NewAnalysisViewModel = hiltViewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()

    var useRegion by remember { mutableStateOf(false) }
    var left by remember { mutableStateOf(0.2f) }
    var top by remember { mutableStateOf(0.1f) }
    var right by remember { mutableStateOf(0.8f) }
    var bottom by remember { mutableStateOf(0.95f) }

    fun regionBox(): FloatArray? = if (useRegion) floatArrayOf(left, top, right, bottom) else null

    val picker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) vm.analyze(uri, regionBox())
    }

    LaunchedEffect(state.stem) { state.stem?.let(onDone) }

    Scaffold(topBar = { TopAppBar(title = { Text("New analysis") }) }) { pad ->
        Column(Modifier.fillMaxSize().padding(pad).padding(24.dp).verticalScroll(rememberScrollState())) {
            Text("Pick a video (or photo) from your phone, then analyze it on-device.",
                style = MaterialTheme.typography.bodyMedium)
            Spacer(Modifier.height(24.dp))
            Button(onClick = { picker.launch("video/*") }, enabled = !state.running, modifier = Modifier.fillMaxWidth()) {
                Text("Pick video & analyze")
            }
            Spacer(Modifier.height(8.dp))
            Button(onClick = { picker.launch("image/*") }, enabled = !state.running, modifier = Modifier.fillMaxWidth()) {
                Text("Pick photo (posture only)")
            }
            Spacer(Modifier.height(8.dp))
            androidx.compose.material3.OutlinedButton(
                onClick = { vm.analyzeSample(regionBox()) },
                enabled = !state.running,
                modifier = Modifier.fillMaxWidth(),
            ) { Text("Use the bundled sample clip") }

            Spacer(Modifier.height(16.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Only look at me (region box)")
                Switch(checked = useRegion, onCheckedChange = { useRegion = it })
            }
            if (useRegion) {
                RegionSlider("left", left) { left = it }
                RegionSlider("top", top) { top = it }
                RegionSlider("right", right) { right = it }
                RegionSlider("bottom", bottom) { bottom = it }
            }

            Spacer(Modifier.height(16.dp))
            if (state.running) {
                CircularProgressIndicator()
                Spacer(Modifier.height(12.dp))
                Text(state.stage, style = MaterialTheme.typography.bodyMedium)
                Spacer(Modifier.height(8.dp))
                Button(onClick = vm::cancel, modifier = Modifier.fillMaxWidth()) { Text("Cancel") }
            }
            state.error?.let {
                Text(it, color = MaterialTheme.colorScheme.error)
                Spacer(Modifier.height(8.dp))
                Button(onClick = vm::retry, modifier = Modifier.fillMaxWidth()) { Text("Retry") }
            }
            Spacer(Modifier.height(8.dp))
            TextButton(onClick = onBack) { Text("Back") }
        }
    }
}

@Composable
private fun RegionSlider(label: String, value: Float, onChange: (Float) -> Unit) {
    Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
        Text(label, Modifier.padding(end = 8.dp), style = MaterialTheme.typography.bodySmall)
        Slider(value = value, onValueChange = onChange, valueRange = 0f..1f, modifier = Modifier.weight(1f))
    }
}
