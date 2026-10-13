package com.topspinreview.android.data

import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import android.content.Context
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/** The API + analysis settings (same values as the desktop `.env`). */
data class AppSettings(
    val apiBase: String = "https://api.deepseek.com",
    val apiKey: String = "",
    val textModel: String = "deepseek-v4-pro",
    val visionModel: String = "deepseek-v4-flash-vision-exp",
    val agentic: Boolean = false,
    val maxFrames: Int = 12,
    // player profile (feeds prompts + rubric)
    val sport: String = "table tennis",
    val level: String = "intermediate",
    val hand: String = "right",
    val goal: String = "improve",
    val theme: String = "system",
)

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore("topspin")

class SettingsStore(private val context: Context) {
    private object K {
        val apiBase = stringPreferencesKey("api_base")
        val apiKey = stringPreferencesKey("api_key")
        val textModel = stringPreferencesKey("text_model")
        val visionModel = stringPreferencesKey("vision_model")
        val agentic = booleanPreferencesKey("agentic")
        val maxFrames = intPreferencesKey("max_frames")
        val sport = stringPreferencesKey("sport")
        val level = stringPreferencesKey("level")
        val hand = stringPreferencesKey("hand")
        val goal = stringPreferencesKey("goal")
        val theme = stringPreferencesKey("theme")
    }

    val flow: Flow<AppSettings> = context.dataStore.data.map { p ->
        AppSettings(
            apiBase = p[K.apiBase] ?: "https://api.deepseek.com",
            apiKey = p[K.apiKey] ?: "",
            textModel = p[K.textModel] ?: "deepseek-v4-pro",
            visionModel = p[K.visionModel] ?: "deepseek-v4-flash-vision-exp",
            agentic = p[K.agentic] ?: false,
            maxFrames = p[K.maxFrames] ?: 12,
            sport = p[K.sport] ?: "table tennis",
            level = p[K.level] ?: "intermediate",
            hand = p[K.hand] ?: "right",
            goal = p[K.goal] ?: "improve",
            theme = p[K.theme] ?: "system",
        )
    }

    suspend fun save(s: AppSettings) {
        context.dataStore.edit { p ->
            p[K.apiBase] = s.apiBase
            p[K.apiKey] = s.apiKey
            p[K.textModel] = s.textModel
            p[K.visionModel] = s.visionModel
            p[K.agentic] = s.agentic
            p[K.maxFrames] = s.maxFrames
            p[K.sport] = s.sport
            p[K.level] = s.level
            p[K.hand] = s.hand
            p[K.goal] = s.goal
            p[K.theme] = s.theme
        }
    }
}
