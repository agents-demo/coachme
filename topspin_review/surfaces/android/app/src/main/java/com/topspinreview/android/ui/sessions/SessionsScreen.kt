package com.topspinreview.android.ui.sessions

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.CompareArrows
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import coil.compose.AsyncImage
import com.topspinreview.android.data.Report
import com.topspinreview.android.data.ReportStore
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File
import javax.inject.Inject

@HiltViewModel
class SessionsViewModel @Inject constructor(private val store: ReportStore) : ViewModel() {
    private val _reports = MutableStateFlow<List<Report>>(emptyList())
    val reports: StateFlow<List<Report>> = _reports.asStateFlow()

    init { refresh() }
    fun refresh() = viewModelScope.launch { _reports.value = store.list() }
    fun delete(stem: String) = viewModelScope.launch { store.delete(stem); refresh() }
}

/** Best available thumbnail for a session (pose → motion → frames → source photo). */
private fun thumbOf(r: Report): String? =
    r.artifacts["pose"] ?: r.artifacts["motion"] ?: r.artifacts["frames"]
        ?: if (r.source.matches(Regex(".*\\.(png|jpe?g|bmp|webp|gif)$", RegexOption.IGNORE_CASE))) r.source else null

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SessionsScreen(
    onOpen: (String) -> Unit,
    onNew: () -> Unit,
    onSettings: () -> Unit,
    onCompare: () -> Unit,
    vm: SessionsViewModel = hiltViewModel(),
) {
    val reports by vm.reports.collectAsStateWithLifecycle()
    val totalIssues = reports.sumOf { it.issues.size }
    var pendingDelete by androidx.compose.runtime.remember { androidx.compose.runtime.mutableStateOf<Report?>(null) }
    pendingDelete?.let { victim ->
        androidx.compose.material3.AlertDialog(
            onDismissRequest = { pendingDelete = null },
            title = { Text("Delete session?") },
            text = { Text("This removes \"${victim.stem.ifBlank { victim.source }}\" and its analysis.") },
            confirmButton = {
                androidx.compose.material3.TextButton(onClick = { vm.delete(victim.stem); pendingDelete = null }) { Text("Delete") }
            },
            dismissButton = {
                androidx.compose.material3.TextButton(onClick = { pendingDelete = null }) { Text("Cancel") }
            },
        )
    }
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Topspin Review") },
                actions = {
                    IconButton(onClick = onCompare) { Icon(Icons.Filled.CompareArrows, "Compare sessions") }
                    IconButton(onClick = onSettings) { Icon(Icons.Filled.Settings, "Settings") }
                },
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = onNew) { Icon(Icons.Filled.Add, "New analysis") }
        },
    ) { pad ->
        Column(Modifier.fillMaxSize().padding(pad)) {
            if (reports.isNotEmpty()) {
                Row(Modifier.fillMaxWidth().padding(16.dp), horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                    Stat("${reports.size}", "Sessions")
                    Stat("$totalIssues", "Open issues")
                }
            }
            if (reports.isEmpty()) {
                Text("No sessions yet. Tap + to analyze a clip from your phone.", Modifier.padding(24.dp))
                return@Column
            }
            LazyColumn(
                Modifier.fillMaxSize(),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                items(reports, key = { it.stem.ifEmpty { it.source } }) { r ->
                    Card(Modifier.fillMaxWidth().clickable { onOpen(r.stem) }) {
                        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                            val thumb = thumbOf(r)
                            if (thumb != null) {
                                AsyncImage(
                                    model = File(thumb),
                                    contentDescription = null,
                                    modifier = Modifier.width(96.dp).height(64.dp),
                                )
                            }
                            Column(Modifier.weight(1f).padding(start = 12.dp)) {
                                Text(r.stem.ifEmpty { r.source }, fontWeight = FontWeight.Bold)
                                Text("${r.sport} · ${r.date}", style = MaterialTheme.typography.bodySmall)
                                if (r.focus.isNotBlank()) Text("Focus: ${r.focus}", style = MaterialTheme.typography.bodySmall)
                                Text("${r.issues.size} issue(s)", style = MaterialTheme.typography.bodySmall)
                            }
                            IconButton(onClick = { pendingDelete = r }) { Icon(Icons.Filled.Delete, "Delete") }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun Stat(value: String, label: String) {
    Column {
        Text(value, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        Text(label, style = MaterialTheme.typography.bodySmall)
    }
}
