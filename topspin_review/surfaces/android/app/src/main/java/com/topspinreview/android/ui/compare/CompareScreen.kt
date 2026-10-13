package com.topspinreview.android.ui.compare

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import com.topspinreview.android.data.Report
import com.topspinreview.android.data.ReportStore
import com.topspinreview.android.domain.Compare
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

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CompareScreen(onBack: () -> Unit, vm: CompareViewModel = hiltViewModel()) {
    val reports by vm.reports.collectAsStateWithLifecycle()
    val diff by vm.diff.collectAsStateWithLifecycle()
    var a by remember { mutableStateOf<Report?>(null) }
    var b by remember { mutableStateOf<Report?>(null) }

    Scaffold(topBar = { TopAppBar(title = { Text("Compare two sessions") }) }) { pad ->
        Column(Modifier.fillMaxSize().padding(pad).padding(16.dp).verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Picker("Earlier", reports, a) { a = it }
            Picker("Later", reports, b) { b = it }
            Button(
                onClick = { val x = a; val y = b; if (x != null && y != null) vm.compare(x, y) },
                enabled = a != null && b != null,
                modifier = Modifier.fillMaxWidth(),
            ) { Text("Compare") }
            diff?.let { d ->
                Text(d.text.ifBlank { "no comparable change." }, fontWeight = FontWeight.SemiBold)
                if (d.metricDeltas.isNotEmpty()) {
                    Text("Metric deltas (later − earlier):", fontWeight = FontWeight.Bold)
                    d.metricDeltas.forEach { (k, v) -> Text("$k: ${if (v > 0) "+" else ""}${"%.3f".format(v)}") }
                }
            }
        }
    }
}

@Composable
private fun Picker(label: String, reports: List<Report>, selected: Report?, onPick: (Report) -> Unit) {
    var open by remember { mutableStateOf(false) }
    Column {
        Text("$label: ${selected?.stem ?: "—"}", style = MaterialTheme.typography.bodyMedium)
        Button(onClick = { open = true }) { Text("Choose") }
        DropdownMenu(expanded = open, onDismissRequest = { open = false }) {
            reports.forEach { r ->
                DropdownMenuItem(text = { Text(r.stem.ifBlank { r.source }) }, onClick = { onPick(r); open = false })
            }
        }
    }
}
