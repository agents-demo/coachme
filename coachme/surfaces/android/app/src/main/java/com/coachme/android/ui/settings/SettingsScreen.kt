package com.coachme.android.ui.settings

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.text.format.DateUtils
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material.icons.outlined.Bolt
import androidx.compose.material.icons.outlined.Cloud
import androidx.compose.material.icons.outlined.Palette
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Switch
import com.coachme.android.ui.components.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.coachme.android.BuildConfig
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.coachme.android.data.AppSettings
import com.coachme.android.data.SettingsStore
import com.coachme.android.llm.DeepSeekClient
import com.coachme.android.ui.components.DividerLine
import com.coachme.android.ui.components.GhostButton
import com.coachme.android.ui.components.PrimaryButton
import com.coachme.android.ui.components.SectionLabel
import com.coachme.android.ui.components.CoachCard
import com.coachme.android.ui.components.CoachSegmented
import com.coachme.android.ui.components.CoachTopBar
import com.coachme.android.ui.i18n.tr
import com.coachme.android.ui.theme.Accent
import com.coachme.android.ui.theme.Accent2
import com.coachme.android.ui.theme.Bad
import com.coachme.android.ui.theme.Good
import com.coachme.android.ui.theme.SportAccent
import com.coachme.android.ui.theme.SportAccent2
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.put
import kotlin.math.roundToInt
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
    var testing by mutableStateOf(false)
        private set
    var saveTick by mutableIntStateOf(0)
        private set
    var importStatus by mutableStateOf("")
        private set

    fun assetExists(name: String): Boolean = runCatching { context.assets.open(name).close(); true }.getOrDefault(false)

    fun hasPermission(permission: String): Boolean =
        ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED

    fun assetSize(name: String): Long {
        val fdSize = runCatching { context.assets.openFd(name).use { it.length } }.getOrDefault(0L)
        if (fdSize > 0L) return fdSize
        return runCatching { context.assets.open(name).use { it.available().toLong() } }.getOrDefault(0L)
    }

    private var saveJob: Job? = null
    private var loaded = false
    private var dirty = false

    init {
        viewModelScope.launch {
            state = store.flow.first()
            loaded = true
        }
    }

    private fun apply(next: AppSettings) {
        if (
            next.apiBase != state.apiBase ||
            next.apiKey != state.apiKey ||
            next.textModel != state.textModel ||
            next.visionModel != state.visionModel
        ) {
            status = ""
        }
        state = if (next.apiKey != state.apiKey) next.copy(apiKeyFromBuild = false) else next
    }

    fun update(transform: (AppSettings) -> AppSettings) {
        apply(transform(state))
        dirty = true
        saveJob?.cancel()
        saveJob = viewModelScope.launch {
            delay(350)
            store.save(state)
            dirty = false
            saveTick++
        }
    }

    fun updateNow(transform: (AppSettings) -> AppSettings) {
        apply(transform(state))
        dirty = true
        saveJob?.cancel()
        saveJob = viewModelScope.launch {
            store.save(state)
            dirty = false
            saveTick++
        }
    }

    fun clearApiKey() {
        updateNow { it.copy(apiKey = "") }
    }

    fun resetAll() {
        val d = AppSettings()
        importStatus = ""
        updateNow {
            it.copy(
                apiBase = d.apiBase,
                textModel = d.textModel,
                visionModel = d.visionModel,
                sport = d.sport,
                level = d.level,
                hand = d.hand,
                goal = d.goal,
                theme = d.theme,
                appStyle = d.appStyle,
                agentic = d.agentic,
                maxFrames = d.maxFrames,
                showDemo = d.showDemo,
                lastTestAt = 0L,
            )
        }
    }

    fun importSettings(uri: Uri) = viewModelScope.launch {
        importStatus = ""
        val text = withContext(Dispatchers.IO) {
            context.contentResolver.openInputStream(uri)?.bufferedReader()?.use { it.readText() }
        }
        if (text.isNullOrBlank()) {
            importStatus = "Import failed: empty file"
            return@launch
        }
        val obj = runCatching { Json.parseToJsonElement(text).jsonObject }.getOrElse {
            importStatus = "Import failed: ${it.message}"
            return@launch
        }
        fun str(key: String, fallback: String) =
            (obj[key] as? JsonPrimitive)?.contentOrNull ?: fallback
        fun bool(key: String, fallback: Boolean) =
            (obj[key] as? JsonPrimitive)?.booleanOrNull ?: fallback
        fun num(key: String, fallback: Int) =
            (obj[key] as? JsonPrimitive)?.intOrNull ?: fallback

        val theme = str("theme", state.theme)
            .takeIf { it in setOf("system", "light", "dark") } ?: state.theme
        val style = str("appStyle", state.appStyle)
            .takeIf { it in setOf("sport", "dynamic", "indigo") } ?: state.appStyle
        updateNow { current ->
            current.copy(
                apiBase = str("apiBase", current.apiBase).trim(),
                textModel = str("textModel", current.textModel).trim(),
                visionModel = str("visionModel", current.visionModel).trim(),
                sport = str("sport", current.sport).trim(),
                level = str("level", current.level),
                hand = str("hand", current.hand),
                goal = str("goal", current.goal),
                theme = theme,
                appStyle = style,
                agentic = bool("agentic", current.agentic),
                maxFrames = num("maxFrames", current.maxFrames).coerceIn(4, 24),
                showDemo = bool("showDemo", current.showDemo),
                lastTestAt = 0L,
            )
        }
        importStatus = "Imported settings"
    }

    fun resetApiDefaults() {
        val defaults = AppSettings()
        updateNow {
            it.copy(
                apiBase = defaults.apiBase,
                textModel = defaults.textModel,
                visionModel = defaults.visionModel,
            )
        }
    }

    fun testConnection() = viewModelScope.launch {
        if (testing) return@launch
        saveJob?.cancel()
        store.save(state)
        dirty = false
        testing = true
        status = "Testing…"
        val started = System.currentTimeMillis()
        status = try {
            val reply = client.text("You are a health check.", "Reply with the word ok.")
            val ms = (System.currentTimeMillis() - started).coerceAtLeast(1)
            state = state.copy(lastTestAt = System.currentTimeMillis())
            store.save(state)
            "OK: ${reply.take(40)} · ${ms}ms · ${state.textModel.trim()}"
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            friendlyError(e)
        } finally {
            testing = false
        }
    }

    private fun friendlyError(e: Exception): String {
        val m = e.message.orEmpty()
        return when {
            m.contains("HTTP 401") -> "Failed: invalid API key (401)"
            m.contains("HTTP 403") -> "Failed: access denied (403)"
            m.contains("HTTP 404") -> "Failed: endpoint or model not found (404)"
            m.contains("HTTP 429") -> "Failed: rate limited (429), try again shortly"
            m.contains("HTTP 5") -> "Failed: provider server error — try again later"
            m.contains("timeout", ignoreCase = true) -> "Failed: timed out — check the connection"
            m.contains("Network error") -> "Failed: can't reach the endpoint — check internet/DNS"
            else -> "Failed: ${m.take(140).ifBlank { "unknown error" }}"
        }
    }

    override fun onCleared() {
        saveJob?.cancel()
        if (loaded && dirty) runBlocking(Dispatchers.IO) { store.save(state) }
        super.onCleared()
    }
}

private data class SettingsTab(val label: String, val icon: ImageVector)

@Composable
fun SettingsScreen(onBack: () -> Unit, vm: SettingsViewModel = hiltViewModel()) {
    val s = vm.state
    var tab by rememberSaveable { mutableIntStateOf(0) }
    var showReadiness by rememberSaveable { mutableStateOf(false) }
    val tabs = listOf(
        SettingsTab("API", Icons.Outlined.Cloud),
        SettingsTab("Profile", Icons.Outlined.Person),
        SettingsTab("Analysis", Icons.Outlined.Tune),
        SettingsTab("Appearance", Icons.Outlined.Palette),
    )
    val snackbar = remember { SnackbarHostState() }
    val haptics = LocalHapticFeedback.current
    val assets = remember {
        listOf(
            "pose_landmarker_lite.task" to vm.assetSize("pose_landmarker_lite.task"),
            "ball.onnx" to vm.assetSize("ball.onnx"),
            "sample.mp4" to vm.assetSize("sample.mp4"),
        )
    }
    val mediaPermission = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        Manifest.permission.READ_MEDIA_VIDEO
    } else {
        Manifest.permission.READ_EXTERNAL_STORAGE
    }
    val checks = listOf(
        "API key set" to s.apiKey.isNotBlank(),
        "Text model set" to s.textModel.isNotBlank(),
        "Vision model set" to s.visionModel.isNotBlank(),
        "Pose model bundled" to (assets[0].second > 0),
        "Ball model bundled" to (assets[1].second > 0),
        "Sample clip bundled" to (assets[2].second > 0),
        "Media permission" to vm.hasPermission(mediaPermission),
        "Microphone permission" to vm.hasPermission(Manifest.permission.RECORD_AUDIO),
        "Camera permission" to vm.hasPermission(Manifest.permission.CAMERA),
    )
    val missing = checks.count { !it.second }

    LaunchedEffect(vm.saveTick) {
        if (vm.saveTick > 0) snackbar.showSnackbar(tr("Saved"))
    }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        snackbarHost = { SnackbarHost(snackbar) },
        topBar = {
            CoachTopBar(title = "Settings", onBack = onBack) {
                Row(
                    Modifier
                        .padding(end = 12.dp)
                        .clip(CircleShape)
                        .background(MaterialTheme.colorScheme.surfaceVariant)
                        .clickable(
                            role = Role.Button,
                            onClickLabel = "Open readiness",
                            onClick = { showReadiness = true },
                        )
                        .padding(horizontal = 12.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Box(
                        Modifier.size(8.dp).clip(CircleShape)
                            .background(if (missing == 0) Good else Bad),
                    )
                    Spacer(Modifier.width(6.dp))
                    Text(
                        if (missing == 0) "Ready" else "$missing issue${if (missing == 1) "" else "s"}",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSurface,
                    )
                }
            }
        },
        bottomBar = {
            Column {
                DividerLine()
                NavigationBar(containerColor = MaterialTheme.colorScheme.background) {
                    tabs.forEachIndexed { i, item ->
                        NavigationBarItem(
                            selected = tab == i,
                            onClick = {
                                tab = i
                                haptics.performHapticFeedback(HapticFeedbackType.TextHandleMove)
                            },
                            icon = { Icon(item.icon, contentDescription = null) },
                            label = {
                                Text(
                                    item.label,
                                    style = MaterialTheme.typography.labelSmall,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                )
                            },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = MaterialTheme.colorScheme.primary,
                                selectedTextColor = MaterialTheme.colorScheme.primary,
                                indicatorColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.16f),
                                unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant,
                            ),
                        )
                    }
                }
            }
        },
    ) { pad ->
        Column(
            Modifier.fillMaxSize().padding(pad).verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp, vertical = 14.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            when (tab) {
                0 -> ApiTab(s, vm)
                1 -> ProfileTab(s, vm)
                2 -> AnalysisTab(s, vm)
                else -> StyleTab(s, vm)
            }
        }
    }

    if (showReadiness) {
        ReadinessSheet(checks, assets, s.lastTestAt) { showReadiness = false }
    }
}

@Composable
private fun ApiTab(s: AppSettings, vm: SettingsViewModel) {
    val base = s.apiBase.trim()
    val baseError = when {
        base.isBlank() -> null
        !base.startsWith("http://") && !base.startsWith("https://") ->
            "Must start with http:// or https://"
        else -> null
    }
    CoachCard(modifier = Modifier.fillMaxWidth()) {
        SectionLabel("Model API")
        Text(
            "DeepSeek endpoint used for the observe and coach passes.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 4.dp, bottom = 8.dp),
        )
        Field("API base", s.apiBase, KeyboardType.Uri, error = baseError) { v ->
            vm.update { it.copy(apiBase = v) }
        }
        SecretField("API key", s.apiKey) { v -> vm.update { it.copy(apiKey = v) } }
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                when {
                    s.apiKeyFromBuild -> "Using build default key"
                    s.apiKey.isBlank() -> "No API key set"
                    else -> "Custom key saved"
                },
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            if (s.apiKey.isNotBlank()) {
                TextButton(onClick = { vm.clearApiKey() }) { Text("Clear") }
            }
        }
        ModelField(
            "Text model",
            s.textModel,
            listOf(BuildConfig.DEFAULT_TEXT_MODEL.ifBlank { "deepseek-v4-pro" }),
        ) { v -> vm.update { it.copy(textModel = v) } }
        ModelField(
            "Vision model",
            s.visionModel,
            listOf(BuildConfig.DEFAULT_VISION_MODEL.ifBlank { "deepseek-v4-flash-vision-exp" }),
            imeAction = ImeAction.Done,
        ) { v -> vm.update { it.copy(visionModel = v) } }
        PrimaryButton(
            text = if (vm.testing) "Testing…" else "Test connection",
            onClick = { vm.testConnection() },
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
            enabled = !vm.testing && s.apiKey.trim().isNotEmpty() && baseError == null,
            icon = {
                if (vm.testing) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(18.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onPrimary,
                    )
                } else {
                    Icon(Icons.Outlined.Bolt, contentDescription = null, modifier = Modifier.size(18.dp))
                }
            },
        )
        TextButton(
            onClick = { vm.resetApiDefaults() },
            modifier = Modifier.align(Alignment.CenterHorizontally),
        ) { Text("Reset defaults") }
        if (vm.status.isNotBlank()) {
            val tone = when {
                vm.status.startsWith("OK") -> Good
                vm.status.startsWith("Failed") -> Bad
                else -> MaterialTheme.colorScheme.onSurfaceVariant
            }
            Text(
                vm.status,
                style = MaterialTheme.typography.bodySmall,
                color = tone,
                modifier = Modifier.padding(top = 2.dp),
            )
        }
    }
}

@Composable
private fun ProfileTab(s: AppSettings, vm: SettingsViewModel) {
    CoachCard(modifier = Modifier.fillMaxWidth()) {
        SectionLabel("Player profile")
        Text(
            "Feeds the prompts and the scoring rubric.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 4.dp, bottom = 8.dp),
        )
        ModelField(
            "Sport",
            s.sport,
            listOf("table tennis", "tennis", "badminton", "squash", "padel"),
            imeAction = ImeAction.Done,
        ) { v -> vm.update { it.copy(sport = v) } }
        ChipRow("Level", listOf("beginner", "intermediate", "advanced"), s.level) { v ->
            vm.updateNow { it.copy(level = v) }
        }
        ChipRow("Dominant hand", listOf("right", "left"), s.hand) { v ->
            vm.updateNow { it.copy(hand = v) }
        }
        ChipRow("Goal", listOf("improve", "consistency", "power", "footwork", "match play"), s.goal) { v ->
            vm.updateNow { it.copy(goal = v) }
        }
    }
}

@Composable
private fun StyleTab(s: AppSettings, vm: SettingsViewModel) {
    CoachCard(modifier = Modifier.fillMaxWidth()) {
        SectionLabel("Language")
        Spacer(Modifier.height(10.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("system" to "System", "en" to "English", "zh" to "中文").forEach { (value, label) ->
                ChoiceChip(label, selected = s.language == value) {
                    vm.updateNow { it.copy(language = value) }
                }
            }
        }
        Text(
            "Phone language is used by default; English is the fallback.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 10.dp),
        )
    }

    CoachCard(modifier = Modifier.fillMaxWidth()) {
        SectionLabel("Theme")
        Spacer(Modifier.height(10.dp))
        val themeValues = listOf("system", "light", "dark")
        CoachSegmented(
            options = listOf("System", "Light", "Dark"),
            selectedIndex = themeValues.indexOf(s.theme).coerceAtLeast(0),
            onSelect = { i -> vm.updateNow { it.copy(theme = themeValues[i]) } },
        )
        Text(
            "System follows your device's light or dark setting.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 10.dp),
        )
    }

    CoachCard(modifier = Modifier.fillMaxWidth()) {
        SectionLabel("Palette")
        Spacer(Modifier.height(10.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            val styles = buildList {
                add(Triple("sport", "Sport", listOf(SportAccent, SportAccent2)))
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    add(
                        Triple(
                            "dynamic",
                            "Dynamic",
                            listOf(Color(0xFF6750A4), Color(0xFF7D5260), Color(0xFF386A20)),
                        ),
                    )
                }
                add(Triple("indigo", "Indigo", listOf(Accent, Accent2)))
            }
            styles.forEach { (value, label, colors) ->
                val selected = s.appStyle == value
                Column(
                    Modifier
                        .weight(1f)
                        .clip(RoundedCornerShape(14.dp))
                        .background(
                            if (selected) MaterialTheme.colorScheme.primary.copy(alpha = 0.10f)
                            else Color.Transparent,
                        )
                        .border(
                            width = if (selected) 2.dp else 1.dp,
                            color = if (selected) MaterialTheme.colorScheme.primary
                            else MaterialTheme.colorScheme.outline,
                            shape = RoundedCornerShape(14.dp),
                        )
                        .selectable(
                            selected = selected,
                            role = Role.RadioButton,
                            onClick = { vm.updateNow { it.copy(appStyle = value) } },
                        )
                        .padding(6.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Box(
                        Modifier.fillMaxWidth().height(44.dp).clip(RoundedCornerShape(10.dp))
                            .background(Brush.linearGradient(colors)),
                    )
                    Spacer(Modifier.height(6.dp))
                    Text(
                        label,
                        style = MaterialTheme.typography.labelLarge,
                        color = if (selected) MaterialTheme.colorScheme.primary
                        else MaterialTheme.colorScheme.onSurface,
                        maxLines = 1,
                    )
                }
            }
        }
        Text(
            when (s.appStyle) {
                "sport" -> "Athletic orange with image-forward session cards."
                "dynamic" -> "Wallpaper-matched Material You colors."
                else -> "Classic indigo brand palette."
            },
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 10.dp),
        )
    }

    CoachCard(modifier = Modifier.fillMaxWidth()) {
        SwitchRow(
            title = "Show demo session with my sessions",
            subtitle = "When off, the demo is hidden as soon as you have at least one real session.",
            checked = s.showDemo,
            onCheckedChange = { checked -> vm.updateNow { it.copy(showDemo = checked) } },
        )
    }
}

@Composable
private fun AnalysisTab(s: AppSettings, vm: SettingsViewModel) {
    val context = LocalContext.current
    var showReset by rememberSaveable { mutableStateOf(false) }
    val importLauncher = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) vm.importSettings(uri)
    }

    CoachCard(modifier = Modifier.fillMaxWidth()) {
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            SectionLabel("Frame sampling")
            Text(
                "${s.maxFrames} frames",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
            )
        }
        Text(
            "Maximum stills sampled from the clip for the observe pass.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 4.dp),
        )
        Slider(
            value = s.maxFrames.toFloat(),
            onValueChange = { v -> vm.update { it.copy(maxFrames = v.roundToInt().coerceIn(4, 24)) } },
            valueRange = 4f..24f,
            steps = 19,
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
        )
    }

    CoachCard(modifier = Modifier.fillMaxWidth()) {
        SwitchRow(
            title = "Agentic report pass",
            subtitle = "Let the model inspect tools and revise the coaching report.",
            checked = s.agentic,
            onCheckedChange = { checked -> vm.updateNow { it.copy(agentic = checked) } },
        )
    }

    CoachCard(modifier = Modifier.fillMaxWidth()) {
        SectionLabel("Backup")
        Text(
            "Export or import the non-secret settings as JSON.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 4.dp, bottom = 8.dp),
        )
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            GhostButton("Export", { exportSettings(context, s) }, Modifier.weight(1f))
            GhostButton(
                "Import",
                { importLauncher.launch(arrayOf("application/json")) },
                Modifier.weight(1f),
            )
        }
        if (vm.importStatus.isNotBlank()) {
            Text(
                vm.importStatus,
                style = MaterialTheme.typography.bodySmall,
                color = if (vm.importStatus.startsWith("Imported")) Good else Bad,
                modifier = Modifier.padding(top = 8.dp),
            )
        }
    }

    CoachCard(modifier = Modifier.fillMaxWidth()) {
        GhostButton("Reset all settings", { showReset = true }, Modifier.fillMaxWidth())
    }

    if (showReset) {
        AlertDialog(
            onDismissRequest = { showReset = false },
            title = { Text("Reset all settings?") },
            text = {
                Text(
                    "Restores the API endpoint, models, profile, appearance and analysis " +
                        "settings. Your API key is kept.",
                )
            },
            confirmButton = {
                TextButton(onClick = { vm.resetAll(); showReset = false }) { Text("Reset") }
            },
            dismissButton = {
                TextButton(onClick = { showReset = false }) { Text("Cancel") }
            },
        )
    }
}

@Composable
private fun SwitchRow(
    title: String,
    subtitle: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(
        Modifier.fillMaxWidth().padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.bodyMedium)
            Text(
                subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Spacer(Modifier.width(12.dp))
        Switch(checked = checked, onCheckedChange = onCheckedChange)
    }
}

private fun exportSettings(context: Context, s: AppSettings) {
    val json = buildJsonObject {
        put("version", 1)
        put("apiBase", s.apiBase)
        put("textModel", s.textModel)
        put("visionModel", s.visionModel)
        put("sport", s.sport)
        put("level", s.level)
        put("hand", s.hand)
        put("goal", s.goal)
        put("theme", s.theme)
        put("appStyle", s.appStyle)
        put("agentic", s.agentic)
        put("maxFrames", s.maxFrames)
        put("showDemo", s.showDemo)
    }.toString()
    val intent = Intent(Intent.ACTION_SEND).apply {
        type = "application/json"
        putExtra(Intent.EXTRA_TEXT, json)
    }
    context.startActivity(Intent.createChooser(intent, tr("Export settings")))
}

@Composable
private fun InfoRow(label: String, value: String) {
    Row(
        Modifier.fillMaxWidth().padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(label, style = MaterialTheme.typography.bodyMedium)
        Text(
            value,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ReadinessSheet(
    checks: List<Pair<String, Boolean>>,
    assets: List<Pair<String, Long>>,
    lastTestAt: Long,
    onDismiss: () -> Unit,
) {
    val ready = checks.count { it.second }
    val lastTest = if (lastTestAt <= 0L) {
        "Never tested"
    } else {
        DateUtils.getRelativeTimeSpanString(
            lastTestAt,
            System.currentTimeMillis(),
            DateUtils.MINUTE_IN_MILLIS,
        ).toString()
    }

    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(Modifier.fillMaxWidth().padding(start = 20.dp, end = 20.dp, bottom = 28.dp)) {
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("Readiness", style = MaterialTheme.typography.titleLarge)
                Text(
                    "$ready / ${checks.size}",
                    style = MaterialTheme.typography.labelLarge,
                    color = if (ready == checks.size) Good else MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Text(
                "Last API test: $lastTest",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 4.dp),
            )
            Text(
                "Read-only checks for the API setup and bundled models.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 2.dp, bottom = 10.dp),
            )
            checks.forEach { (label, ok) -> ReadyRow(label, ok) }
            Spacer(Modifier.height(14.dp))
            Text("Bundled assets", style = MaterialTheme.typography.labelLarge)
            Spacer(Modifier.height(4.dp))
            assets.forEach { (name, size) ->
                Row(
                    Modifier.fillMaxWidth().padding(vertical = 4.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(name, style = MaterialTheme.typography.bodyMedium)
                    Text(
                        formatSize(size),
                        style = MaterialTheme.typography.bodySmall,
                        color = if (size > 0) MaterialTheme.colorScheme.onSurfaceVariant else Bad,
                    )
                }
            }
            Spacer(Modifier.height(14.dp))
            Text("App", style = MaterialTheme.typography.labelLarge)
            Spacer(Modifier.height(4.dp))
            InfoRow(
                "Version",
                "${BuildConfig.VERSION_NAME} · ${if (BuildConfig.DEBUG) "debug" else "release"}",
            )
            InfoRow("Android", "${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})")
        }
    }
}

private fun formatSize(bytes: Long): String = when {
    bytes >= 1_048_576 -> "%.1f MB".format(bytes / 1_048_576.0)
    bytes >= 1024 -> "%.0f KB".format(bytes / 1024.0)
    else -> "$bytes B"
}

@Composable
private fun Field(
    label: String,
    value: String,
    keyboardType: KeyboardType = KeyboardType.Text,
    imeAction: ImeAction = ImeAction.Next,
    error: String? = null,
    onChange: (String) -> Unit,
) {
    OutlinedTextField(
        value = value,
        onValueChange = onChange,
        label = { Text(label) },
        keyboardOptions = KeyboardOptions(keyboardType = keyboardType, imeAction = imeAction),
        isError = error != null,
        supportingText = if (error != null) {
            { Text(error) }
        } else {
            null
        },
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
        shape = RoundedCornerShape(14.dp),
        singleLine = true,
    )
}

@Composable
private fun SecretField(label: String, value: String, onChange: (String) -> Unit) {
    var revealed by rememberSaveable { mutableStateOf(false) }
    OutlinedTextField(
        value = value,
        onValueChange = onChange,
        label = { Text(label) },
        singleLine = true,
        visualTransformation = if (revealed) VisualTransformation.None else PasswordVisualTransformation(),
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password, imeAction = ImeAction.Next),
        trailingIcon = {
            IconButton(onClick = { revealed = !revealed }) {
                Icon(
                    if (revealed) Icons.Filled.VisibilityOff else Icons.Filled.Visibility,
                    contentDescription = if (revealed) "Hide API key" else "Show API key",
                )
            }
        },
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
        shape = RoundedCornerShape(14.dp),
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ModelField(
    label: String,
    value: String,
    presets: List<String>,
    imeAction: ImeAction = ImeAction.Next,
    onChange: (String) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    val options = (listOf(value) + presets).distinct()
    ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }) {
        OutlinedTextField(
            value = value,
            onValueChange = onChange,
            label = { Text(label) },
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Text, imeAction = imeAction),
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
            modifier = Modifier.menuAnchor().fillMaxWidth().padding(vertical = 4.dp),
            shape = RoundedCornerShape(14.dp),
        )
        ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            options.forEach { option ->
                DropdownMenuItem(
                    text = { Text(option) },
                    onClick = {
                        onChange(option)
                        expanded = false
                    },
                )
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun ChipRow(label: String, options: List<String>, selected: String, onSelect: (String) -> Unit) {
    Text(
        label,
        style = MaterialTheme.typography.bodyMedium,
        modifier = Modifier.padding(top = 10.dp),
    )
    FlowRow(
        Modifier.fillMaxWidth().padding(top = 6.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        val all = if (selected in options) options else options + selected
        all.forEach { option ->
            ChoiceChip(option.replaceFirstChar { it.uppercase() }, selected == option) { onSelect(option) }
        }
    }
}

@Composable
private fun ChoiceChip(
    label: String,
    selected: Boolean,
    swatch: Color? = null,
    onClick: () -> Unit,
) {
    Box(
        Modifier
            .clip(RoundedCornerShape(50))
            .background(if (selected) MaterialTheme.colorScheme.primary.copy(alpha = 0.18f) else Color.Transparent)
            .border(2.dp, if (selected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outline, RoundedCornerShape(50))
            .selectable(selected = selected, role = Role.RadioButton, onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 8.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            if (swatch != null) {
                Box(Modifier.size(10.dp).clip(CircleShape).background(swatch))
                Spacer(Modifier.width(6.dp))
            }
            Text(
                label,
                style = MaterialTheme.typography.labelLarge,
                color = if (selected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface,
                fontWeight = FontWeight.SemiBold,
            )
        }
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
