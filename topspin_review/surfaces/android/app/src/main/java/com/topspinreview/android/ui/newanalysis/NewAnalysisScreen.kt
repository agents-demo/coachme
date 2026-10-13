package com.topspinreview.android.ui.newanalysis

import android.content.Context
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import com.topspinreview.android.pipeline.Pipeline
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
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

    fun analyze(uri: Uri) = viewModelScope.launch {
        _state.value = State(running = true, stage = "Preparing")
        try {
            val file = copyToCache(uri)
            val report = pipeline.analyze(file.absolutePath) { stage ->
                _state.value = _state.value.copy(stage = stage)
            }
            _state.value = State(stem = report.stem.ifBlank { file.nameWithoutExtension })
        } catch (e: Exception) {
            _state.value = State(error = e.message ?: "Analysis failed")
        }
    }

    private suspend fun copyToCache(uri: Uri): File = withContext(Dispatchers.IO) {
        val out = File(context.cacheDir, "input_${System.currentTimeMillis()}.mp4")
        context.contentResolver.openInputStream(uri)?.use { input -> out.outputStream().use { input.copyTo(it) } }
        out
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NewAnalysisScreen(onDone: (String) -> Unit, onBack: () -> Unit, vm: NewAnalysisViewModel = hiltViewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()

    val picker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) vm.analyze(uri)
    }

    // Navigate once a report is ready.
    LaunchedEffect(state.stem) {
        state.stem?.let(onDone)
    }

    Scaffold(topBar = { TopAppBar(title = { Text("New analysis") }) }) { pad ->
        Column(Modifier.fillMaxSize().padding(pad).padding(24.dp)) {
            Text("Pick a video (or photo) from your phone, then analyze it on-device.",
                style = MaterialTheme.typography.bodyMedium)
            Spacer(Modifier.height(24.dp))
            Button(
                onClick = { picker.launch("video/*") },
                enabled = !state.running,
                modifier = Modifier.fillMaxWidth(),
            ) { Text("Pick video & analyze") }
            Spacer(Modifier.height(16.dp))
            if (state.running) {
                CircularProgressIndicator()
                Spacer(Modifier.height(12.dp))
                Text(state.stage, style = MaterialTheme.typography.bodyMedium)
            }
            state.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            Spacer(Modifier.height(8.dp))
            TextButton(onClick = onBack) { Text("Back") }
        }
    }
}
