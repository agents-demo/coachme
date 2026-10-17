package com.topspinreview.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.topspinreview.android.data.AppSettings
import com.topspinreview.android.data.SettingsStore
import com.topspinreview.android.ui.AppNav
import com.topspinreview.android.ui.theme.TopspinTheme
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    @Inject lateinit var settings: SettingsStore

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            val s by settings.flow.collectAsStateWithLifecycle(initialValue = AppSettings())
            val dark = when (s.theme) {
                "light" -> false
                "dark" -> true
                else -> isSystemInDarkTheme()
            }
            TopspinTheme(darkTheme = dark, style = s.appStyle) {
                AppNav()
            }
        }
    }
}
