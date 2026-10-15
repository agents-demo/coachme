package com.topspinreview.android.ui.result

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.topspinreview.android.data.Report
import com.topspinreview.android.data.ReportStore
import com.topspinreview.android.ui.components.MutedNote
import com.topspinreview.android.ui.components.TspTopBar
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject

@HiltViewModel
class DiagnosticsViewModel @Inject constructor(private val store: ReportStore) : ViewModel() {
    private val _report = MutableStateFlow<Report?>(null)
    val report = _report.asStateFlow()
    fun load(stem: String) { _report.value = store.load(stem) }
}

/** Diagnostics as its own screen (opened from the result screen's overflow menu). */
@Composable
fun DiagnosticsScreen(stem: String, onBack: () -> Unit, vm: DiagnosticsViewModel = hiltViewModel()) {
    val report by vm.report.collectAsStateWithLifecycle()
    LaunchedEffect(stem) { vm.load(stem) }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = { TspTopBar(title = "Diagnostics", onBack = onBack) },
    ) { pad ->
        Column(Modifier.fillMaxSize().padding(pad)) {
            val r = report
            if (r == null) MutedNote("Report not found.", Modifier.padding(horizontal = 16.dp))
            else DiagnosticsTab(r)
        }
    }
}
