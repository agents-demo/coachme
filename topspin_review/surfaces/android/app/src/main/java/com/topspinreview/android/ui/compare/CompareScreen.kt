package com.topspinreview.android.ui.compare

import android.net.Uri
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import com.topspinreview.android.data.Report
import com.topspinreview.android.data.ReportStore
import com.topspinreview.android.domain.Compare
import com.topspinreview.android.ui.components.GhostButton
import com.topspinreview.android.ui.components.HeroCard
import com.topspinreview.android.ui.components.PrimaryButton
import com.topspinreview.android.ui.components.SectionLabel
import com.topspinreview.android.ui.components.TspCard
import com.topspinreview.android.ui.components.TspTopBar
import com.topspinreview.android.ui.theme.Accent2
import com.topspinreview.android.ui.theme.Bad
import com.topspinreview.android.ui.theme.Good
import com.topspinreview.android.ui.theme.Warn
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

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = { TspTopBar(title = "Compare", onBack = onBack) },
    ) { pad ->
        Column(
            Modifier.fillMaxSize().padding(pad).verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            HeroCard(
                eyebrow = "Progress",
                title = { Text("Compare two sessions", style = MaterialTheme.typography.headlineLarge) },
                subtitle = "Pick an earlier and a later session to see what improved, what regressed, and what's still open.",
            )

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
                TspCard(modifier = Modifier.fillMaxWidth()) {
                    SectionLabel("Clips")
                    Spacer(Modifier.height(10.dp))
                    ComparePlayers(ra.source, rb.source)
                }
            }

            diff?.let { d ->
                TspCard(modifier = Modifier.fillMaxWidth()) {
                    SectionLabel("What changed")
                    Spacer(Modifier.height(8.dp))
                    Text(
                        d.text.ifBlank { "No comparable change." },
                        style = MaterialTheme.typography.bodyLarge,
                    )
                }
                if (d.metricDeltas.isNotEmpty()) {
                    TspCard(modifier = Modifier.fillMaxWidth()) {
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

@Composable
private fun ComparePlayers(sourceA: String, sourceB: String) {
    val ctx = androidx.compose.ui.platform.LocalContext.current
    fun uriOf(s: String): Uri =
        if (s.startsWith("content:") || s.startsWith("http")) Uri.parse(s) else Uri.fromFile(java.io.File(s))
    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text("Earlier", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        PlayerBox(ctx, uriOf(sourceA))
        Text("Later", style = MaterialTheme.typography.labelMedium, color = Accent2)
        PlayerBox(ctx, uriOf(sourceB))
    }
}

@Composable
private fun PlayerBox(ctx: android.content.Context, uri: Uri) {
    val exo = remember {
        androidx.media3.exoplayer.ExoPlayer.Builder(ctx).build().apply {
            setMediaItem(androidx.media3.common.MediaItem.fromUri(uri)); prepare(); playWhenReady = false
        }
    }
    androidx.compose.runtime.DisposableEffect(Unit) { onDispose { exo.release() } }
    Box(Modifier.fillMaxWidth().height(200.dp).clip(RoundedCornerShape(14.dp))) {
        androidx.compose.ui.viewinterop.AndroidView(
            factory = { androidx.media3.ui.PlayerView(it).apply { player = exo; useController = true } },
            modifier = Modifier.fillMaxSize(),
        )
    }
}

@Composable
private fun PickerCard(label: String, reports: List<Report>, selected: Report?, onPick: (Report) -> Unit) {
    var open by remember { mutableStateOf(false) }
    TspCard(modifier = Modifier.fillMaxWidth()) {
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
