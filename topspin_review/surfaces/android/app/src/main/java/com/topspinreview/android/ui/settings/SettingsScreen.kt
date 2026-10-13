package com.topspinreview.android.ui.settings

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
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
import androidx.lifecycle.viewModelScope
import com.topspinreview.android.data.AppSettings
import com.topspinreview.android.data.SettingsStore
import com.topspinreview.android.llm.DeepSeekClient
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val store: SettingsStore,
    private val client: DeepSeekClient,
) : ViewModel() {
    var state by mutableStateOf(AppSettings())
        private set
    var status by mutableStateOf("")
        private set

    init { viewModelScope.launch { state = store.flow.first() } }
    fun update(transform: (AppSettings) -> AppSettings) { state = transform(state) }
    fun save() = viewModelScope.launch { store.save(state); status = "Saved" }

    fun testConnection() = viewModelScope.launch {
        status = "Testing…"
        status = runCatching { client.text("You are a health check.", "Reply with the word ok.") }
            .fold({ "OK: ${it.take(60)}" }, { "Failed: ${it.message}" })
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(onBack: () -> Unit, vm: SettingsViewModel = hiltViewModel()) {
    val s = vm.state
    Scaffold(topBar = { TopAppBar(title = { Text("Settings") }) }) { pad ->
        Column(Modifier.fillMaxSize().padding(pad).padding(16.dp).verticalScroll(rememberScrollState())) {
            Field("API base", s.apiBase) { v -> vm.update { it.copy(apiBase = v) } }
            Field("API key", s.apiKey) { v -> vm.update { it.copy(apiKey = v) } }
            Field("Text model", s.textModel) { v -> vm.update { it.copy(textModel = v) } }
            Field("Vision model", s.visionModel) { v -> vm.update { it.copy(visionModel = v) } }

            Spacer(Modifier.height(8.dp))
            Text("Profile", style = MaterialTheme.typography.titleSmall)
            Field("Sport", s.sport) { v -> vm.update { it.copy(sport = v) } }
            Field("Level", s.level) { v -> vm.update { it.copy(level = v) } }
            Field("Dominant hand", s.hand) { v -> vm.update { it.copy(hand = v) } }
            Field("Goal", s.goal) { v -> vm.update { it.copy(goal = v) } }

            Spacer(Modifier.height(8.dp))
            Text("Agentic mode", style = MaterialTheme.typography.titleSmall)
            Switch(checked = s.agentic, onCheckedChange = { v -> vm.update { it.copy(agentic = v) } })

            Spacer(Modifier.height(16.dp))
            Button(onClick = vm::save, modifier = Modifier.fillMaxWidth()) { Text("Save") }
            Spacer(Modifier.height(8.dp))
            Button(onClick = vm::testConnection, modifier = Modifier.fillMaxWidth()) { Text("Test connection") }
            if (vm.status.isNotBlank()) { Spacer(Modifier.height(8.dp)); Text(vm.status) }
            Spacer(Modifier.height(16.dp))
            Button(onClick = onBack, modifier = Modifier.fillMaxWidth()) { Text("Back") }
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
        singleLine = true,
    )
}
