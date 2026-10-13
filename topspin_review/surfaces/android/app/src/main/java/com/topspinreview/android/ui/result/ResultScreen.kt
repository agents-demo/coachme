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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
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
import coil.compose.AsyncImage
import com.topspinreview.android.data.Report
import com.topspinreview.android.data.ReportStore
import com.topspinreview.android.ui.theme.Accent
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
import java.io.File
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

    fun saveAnnotations(annotations: kotlinx.serialization.json.JsonArray) {
        val r = _report.value ?: return
        store.saveAnnotations(r.stem, annotations)
        _report.value = r.copy(annotations = annotations)
    }

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
                0 -> VideoTab(r, vm::saveAnnotations)
                1 -> Analysis(r)
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
private fun Analysis(r: Report) {
    val m = r.metrics
    val mech = m["mechanics"] as? kotlinx.serialization.json.JsonObject
    val foot = m["footwork_series"] as? kotlinx.serialization.json.JsonArray
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        r.artifacts["motion"]?.let {
            Text("Movement map", fontWeight = FontWeight.Bold)
            AsyncImage(model = File(it), contentDescription = "Movement map", modifier = Modifier.fillMaxWidth())
        }
        r.artifacts["heatmap"]?.let {
            Text("Position map", fontWeight = FontWeight.Bold)
            AsyncImage(model = File(it), contentDescription = "Position map", modifier = Modifier.fillMaxWidth())
        }
        if (foot != null && foot.size > 1) {
            Text("Side-to-side movement", fontWeight = FontWeight.Bold)
            val lateral = (mech?.get("lower_lateral_range")?.toString()?.toDoubleOrNull() ?: 0.0) * 100
            val changes = mech?.get("lower_direction_changes")?.toString() ?: "0"
            Row(horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                Stat("${lateral.toInt()}%", "Travel (band height)")
                Stat(changes, "Direction changes")
            }
            FootworkChart(foot)
        }
        r.artifacts["pose"]?.let {
            Text("Skeleton", fontWeight = FontWeight.Bold)
            AsyncImage(model = File(it), contentDescription = "Skeleton", modifier = Modifier.fillMaxWidth())
        }
        val poseSummary = m["pose_summary"] as? kotlinx.serialization.json.JsonObject
        if (poseSummary != null && poseSummary.isNotEmpty()) {
            Text("Body angles", fontWeight = FontWeight.Bold)
            Row(horizontalArrangement = Arrangement.spacedBy(20.dp)) {
                poseSummary["l_knee_mean"]?.let { Stat(it.toString(), "L knee") }
                poseSummary["r_knee_mean"]?.let { Stat(it.toString(), "R knee") }
                poseSummary["l_elbow_mean"]?.let { Stat(it.toString(), "L elbow") }
                poseSummary["r_elbow_mean"]?.let { Stat(it.toString(), "R elbow") }
            }
        }
        val strokes = m["strokes"] as? kotlinx.serialization.json.JsonArray
        if (strokes != null && strokes.isNotEmpty()) {
            Text("Fast-hand events", fontWeight = FontWeight.Bold)
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                strokes.forEach { s ->
                    val o = s as? kotlinx.serialization.json.JsonObject
                    val hand = o?.get("hand")?.toString()?.trim('"') ?: "?"
                    val t = o?.get("t")?.toString() ?: "?"
                    Text("$hand ${t}s", style = MaterialTheme.typography.bodySmall)
                }
            }
        }
        val ball = m["ball"] as? kotlinx.serialization.json.JsonObject
        r.artifacts["ball"]?.let {
            Text("Object path", fontWeight = FontWeight.Bold)
            AsyncImage(model = File(it), contentDescription = "Object path", modifier = Modifier.fillMaxWidth())
        }
        ball?.get("stats")?.let { st ->
            val o = st as? kotlinx.serialization.json.JsonObject
            if (o != null) {
                Text("Tracked object", fontWeight = FontWeight.Bold)
                Row(horizontalArrangement = Arrangement.spacedBy(20.dp)) {
                    o["visible_frames"]?.let { Stat(it.toString(), "Frames tracked") }
                    o["max_speed"]?.let { Stat(it.toString(), "Max speed") }
                    (ball["segments"] as? kotlinx.serialization.json.JsonArray)?.let { Stat(it.size.toString(), "Active spans") }
                }
            }
        }
        if (foot == null && r.artifacts["motion"] == null && r.artifacts["pose"] == null && r.artifacts["ball"] == null) {
            Text("No measurements available for this run.", style = MaterialTheme.typography.bodyMedium)
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

/** A small lower-body left–right position chart (Appendix L12 · Side-to-side movement). */
@Composable
private fun FootworkChart(series: kotlinx.serialization.json.JsonArray) {
    val pts = series.mapNotNull {
        val o = it as? kotlinx.serialization.json.JsonObject ?: return@mapNotNull null
        val t = o["t"]?.toString()?.toDoubleOrNull() ?: return@mapNotNull null
        val x = o["x"]?.toString()?.toDoubleOrNull() ?: return@mapNotNull null
        t to x
    }
    if (pts.size < 2) return
    val t0 = pts.first().first; val t1 = pts.last().first
    val lo = pts.minOf { it.second }; val hi = pts.maxOf { it.second }
    val span = maxOf(0.08, hi - lo)
    val dlo = lo - span * 0.4; val dhi = hi + span * 0.4
    androidx.compose.foundation.Canvas(Modifier.fillMaxWidth().height(140.dp)) {
        val w = size.width; val h = size.height
        fun X(t: Double) = (((t - t0) / (if (t1 - t0 == 0.0) 1.0 else t1 - t0)) * w).toFloat()
        fun Y(x: Double) = ((dhi - x) / (dhi - dlo) * h).toFloat()
        val path = androidx.compose.ui.graphics.Path()
        pts.forEachIndexed { i, (t, x) ->
            val px = X(t); val py = Y(x)
            if (i == 0) path.moveTo(px, py) else path.lineTo(px, py)
        }
        drawPath(path, color = Accent, style = androidx.compose.ui.graphics.drawscope.Stroke(width = 4f))
    }
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
                com.topspinreview.android.ui.MicButton { q = it }
                Button(onClick = { if (q.isNotBlank()) { onAsk(q); q = "" } }) { Text("Ask") }
            }
        }
        items(answers) { (q, a) ->
            Column {
                Text("You: $q", style = MaterialTheme.typography.bodySmall)
                Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                    Text("Coach: $a", Modifier.weight(1f))
                    com.topspinreview.android.ui.SpeakButton(a)
                }
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
