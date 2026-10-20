package com.coachme.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.coachme.android.data.AppSettings
import com.coachme.android.data.SettingsStore
import com.coachme.android.ui.AppNav
import com.coachme.android.ui.i18n.AppLanguage
import com.coachme.android.ui.theme.CoachMeTheme
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
            LaunchedEffect(s.language) { AppLanguage.apply(s.language) }
            val dark = when (s.theme) {
                "light" -> false
                "dark" -> true
                else -> isSystemInDarkTheme()
            }
            CoachMeTheme(darkTheme = dark, style = s.appStyle) {
                AppNav()
            }
        }
    }
}
