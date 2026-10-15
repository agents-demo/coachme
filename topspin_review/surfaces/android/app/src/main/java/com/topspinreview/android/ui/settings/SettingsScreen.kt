package com.topspinreview.android.ui.settings

import android.content.Context
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.topspinreview.android.data.AppSettings
import com.topspinreview.android.data.SettingsStore
import com.topspinreview.android.llm.DeepSeekClient
import com.topspinreview.android.ui.components.GhostButton
import com.topspinreview.android.ui.components.HeroCard
import com.topspinreview.android.ui.components.PrimaryButton
import com.topspinreview.android.ui.components.SectionLabel
import com.topspinreview.android.ui.components.TspCard
import com.topspinreview.android.ui.components.TspTopBar
import com.topspinreview.android.ui.theme.Accent
import com.topspinreview.android.ui.theme.Bad
import com.topspinreview.android.ui.theme.Good
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val store: SettingsStore,
    private val client: DeepSeekClient,
    @dagger.hilt.android.qualifiers.ApplicationContext private val context: Context,
) : ViewModel() {
    var state by mutableStateOf(AppSettings())
        private set
    var status by mutableStateOf("")
        private set

    fun assetExists(name: String): Boolean = runCatching { context.assets.open(name).close(); true }.getOrDefault(false)

    init { viewModelScope.launch { state = store.flow.first() } }
    fun update(transform: (AppSettings) -> AppSettings) { state = transform(state) }
    fun save() = viewModelScope.launch { store.save(state); status = "Saved" }

    fun testConnection() = viewModelScope.launch {
        status = "Testing…"
        status = runCatching { client.text("You are a health check.", "Reply with the word ok.") }
            .fold({ "OK: ${it.take(60)}" }, { "Failed: ${it.message}" })
    }
}

@Composable
fun SettingsScreen(onBack: () -> Unit, vm: SettingsViewModel = hiltViewModel()) {
    val s = vm.state
    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = { TspTopBar(title = "Settings", onBack = onBack) },
    ) { pad ->
        Column(
            Modifier.fillMaxSize().padding(pad).verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            HeroCard(
                eyebrow = "Configuration",
                title = { Text("Settings", style = MaterialTheme.typography.headlineLarge) },
                subtitle = "The model endpoint and your player profile feed the prompts and the rubric.",
            )

            TspCard(modifier = Modifier.fillMaxWidth()) {
                SectionLabel("Model API")
                Spacer(Modifier.height(10.dp))
                Field("API base", s.apiBase) { v -> vm.update { it.copy(apiBase = v) } }
                Field("API key", s.apiKey) { v -> vm.update { it.copy(apiKey = v) } }
                Field("Text model", s.textModel) { v -> vm.update { it.copy(textModel = v) } }
                Field("Vision model", s.visionModel) { v -> vm.update { it.copy(visionModel = v) } }
            }

            TspCard(modifier = Modifier.fillMaxWidth()) {
                SectionLabel("Player profile")
                Spacer(Modifier.height(10.dp))
                Field("Sport", s.sport) { v -> vm.update { it.copy(sport = v) } }
                Field("Level", s.level) { v -> vm.update { it.copy(level = v) } }
                Field("Dominant hand", s.hand) { v -> vm.update { it.copy(hand = v) } }
                Field("Goal", s.goal) { v -> vm.update { it.copy(goal = v) } }
            }

            TspCard(modifier = Modifier.fillMaxWidth()) {
                SectionLabel("Appearance")
                Spacer(Modifier.height(10.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf("system", "light", "dark").forEach { t ->
                        ChoiceChip(t.replaceFirstChar { it.uppercase() }, selected = s.theme == t) {
                            vm.update { it.copy(theme = t) }
                        }
                    }
                }
            }

            TspCard(modifier = Modifier.fillMaxWidth()) {
                SectionLabel("Readiness")
                Spacer(Modifier.height(10.dp))
                ReadyRow("API key set", s.apiKey.isNotBlank())
                ReadyRow("Text model set", s.textModel.isNotBlank())
                ReadyRow("Vision model set", s.visionModel.isNotBlank())
                ReadyRow("Pose model bundled", vm.assetExists("pose_landmarker_lite.task"))
                ReadyRow("Ball model bundled", vm.assetExists("ball.onnx"))
                ReadyRow("Sample clip bundled", vm.assetExists("sample.mp4"))
            }

            PrimaryButton("Save", vm::save, Modifier.fillMaxWidth())
            GhostButton("Test connection", vm::testConnection, Modifier.fillMaxWidth())

            if (vm.status.isNotBlank()) {
                val ok = vm.status.startsWith("OK") || vm.status == "Saved"
                TspCard(modifier = Modifier.fillMaxWidth()) {
                    Text(
                        vm.status,
                        style = MaterialTheme.typography.bodyMedium,
                        color = if (ok) Good else MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
    }
}

@Composable
private fun Field(label: String, value: String, onChange: (String) -> Unit) {
    OutlinedTextField(
        value = value,
        onValueChange = onChange,
        label = { Text(label) },
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
        shape = RoundedCornerShape(14.dp),
        singleLine = true,
    )
}

@Composable
private fun ChoiceChip(label: String, selected: Boolean, onClick: () -> Unit) {
    Box(
        Modifier
            .clip(RoundedCornerShape(50))
            .background(if (selected) Accent.copy(alpha = 0.18f) else Color.Transparent)
            .border(2.dp, if (selected) Accent else MaterialTheme.colorScheme.outline, RoundedCornerShape(50))
            .clickable { onClick() }
            .padding(horizontal = 16.dp, vertical = 8.dp),
    ) {
        Text(
            label,
            style = MaterialTheme.typography.labelLarge,
            color = if (selected) Accent else MaterialTheme.colorScheme.onSurface,
            fontWeight = FontWeight.SemiBold,
        )
    }
}

@Composable
private fun ReadyRow(label: String, ok: Boolean) {
    Row(Modifier.padding(vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
        Box(
            Modifier.size(10.dp).clip(CircleShape).background(if (ok) Good else Bad),
        )
        Spacer(Modifier.size(10.dp))
        Text(label, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurface)
    }
}
