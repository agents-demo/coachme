package com.topspinreview.android.ui.result

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.ScrollableTabRow
import androidx.compose.material3.Tab
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
import com.topspinreview.android.llm.DeepSeekClient
import com.topspinreview.android.llm.Prompts
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import javax.inject.Inject

@HiltViewModel
class ResultViewModel @Inject constructor(
    private val store: ReportStore,
    private val client: DeepSeekClient,
    private val json: Json,
) : ViewModel() {
    private val _report = MutableStateFlow<Report?>(null)
    val report = _report.asStateFlow()
    private val _answers = MutableStateFlow<List<Pair<String, String>>>(emptyList())
    val answers = _answers.asStateFlow()

    fun load(stem: String) { _report.value = store.load(stem) }

    fun ask(question: String) = viewModelScope.launch {
        val r = _report.value ?: return@launch
        val context = buildJsonObject {
            put("summary", r.summary); put("focus", r.focus)
            put("issues", buildJsonArray {
                r.issues.forEach { i ->
                    add(buildJsonObject {
                        put("issue", i.issue); put("confidence", i.confidence)
                        put("evidence_times", buildJsonArray { i.evidence_times.forEach { add(kotlinx.serialization.json.JsonPrimitive(it)) } })
                    })
                }
            })
            put("drills", buildJsonArray { r.drills.forEach { add(kotlinx.serialization.json.JsonPrimitive(it)) } })
            put("metrics", r.metrics)
        }
        val answer = runCatching {
            client.text(Prompts.QA_SYSTEM, "Report:\n$context\n\nQuestion: $question")
        }.getOrElse { "Could not answer: ${it.message}" }
        _answers.value = _answers.value + (question to answer)
    }
}

private val TABS = listOf("Video", "Analysis", "Observations", "Coaching", "Diagnostics")

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ResultScreen(stem: String, onBack: () -> Unit, vm: ResultViewModel = hiltViewModel()) {
    val report by vm.report.collectAsStateWithLifecycle()
    var tab by remember { mutableStateOf(2) } // Observations
    val answers by vm.answers.collectAsStateWithLifecycle()

    androidx.compose.runtime.LaunchedEffect(stem) { vm.load(stem) }

    Scaffold(
        topBar = {
            TopAppBar(title = {
                Text(report?.stem?.ifBlank { stem } ?: stem)
            })
        },
    ) { pad ->
        val r = report
        Column(Modifier.fillMaxSize().padding(pad)) {
            if (r == null) { Text("Report not found.", Modifier.padding(16.dp)); return@Scaffold }
            ScrollableTabRow(selectedTabIndex = tab) {
                TABS.forEachIndexed { i, t -> Tab(selected = tab == i, onClick = { tab = i }, text = { Text(t) }) }
            }
            when (tab) {
                0 -> Placeholder("Video: player, frame-step, slow-mo, draw/angle tool, trim & export (P5)")
                1 -> Placeholder("Analysis: heat maps · movement · pose · tracked object (P2–P4)")
                2 -> Observations(r)
                3 -> Coaching(r, answers, onAsk = vm::ask)
                else -> Diagnostics(r)
            }
        }
    }
}

@Composable
private fun Placeholder(text: String) {
    Text(text, Modifier.padding(24.dp), style = MaterialTheme.typography.bodyMedium)
}

@Composable
private fun Observations(r: Report) {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)) {
        if (r.tt_reading != null) {
            item {
                Text("Table-tennis reading", fontWeight = FontWeight.Bold)
                Text(r.tt_reading.toString(), style = MaterialTheme.typography.bodySmall)
            }
        }
        item { Text("Key moments", fontWeight = FontWeight.Bold) }
        items(r.issues) { issue ->
            Column {
                Text(issue.issue, fontWeight = FontWeight.SemiBold)
                Text(
                    "t=${issue.evidence_times.joinToString(", ")} · confidence ${issue.confidence}",
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }
    }
}

@Composable
private fun Coaching(r: Report, answers: List<Pair<String, String>>, onAsk: (String) -> Unit) {
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)) {
        if (r.focus.isNotBlank()) item { Text("Focus next session", fontWeight = FontWeight.Bold); Text(r.focus) }
        if (r.summary.isNotBlank()) item { Text("Summary", fontWeight = FontWeight.Bold); Text(r.summary) }
        if (r.strengths.isNotEmpty()) item {
            Text("What's working", fontWeight = FontWeight.Bold)
            r.strengths.forEach { Text("• $it") }
        }
        if (r.issues.isNotEmpty()) item {
            Text("What to improve", fontWeight = FontWeight.Bold)
            r.issues.forEach { Text("• ${it.issue}") }
        }
        if (r.drills.isNotEmpty()) item {
            Text("Practice", fontWeight = FontWeight.Bold)
            r.drills.forEach { Text("• $it") }
        }
        if (r.limitations.isNotEmpty()) item {
            Text("Limits", fontWeight = FontWeight.Bold)
            r.limitations.forEach { Text("• $it") }
        }
        item {
            Text("Ask", fontWeight = FontWeight.Bold)
            var q by remember { mutableStateOf("") }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(q, { q = it }, Modifier.weight(1f), label = { Text("Question") })
                Button(onClick = { if (q.isNotBlank()) { onAsk(q); q = "" } }) { Text("Ask") }
            }
        }
        items(answers) { (q, a) ->
            Column {
                Text("You: $q", style = MaterialTheme.typography.bodySmall)
                Text("Coach: $a")
            }
        }
    }
}

@Composable
private fun Diagnostics(r: Report) {
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("Usage", fontWeight = FontWeight.Bold)
        Text(r.usage.toString(), style = MaterialTheme.typography.bodySmall)
        Spacer(Modifier.height(12.dp))
        Text("Model calls / tools / timeline come from the run's observability (P6).",
            style = MaterialTheme.typography.bodySmall)
    }
}
