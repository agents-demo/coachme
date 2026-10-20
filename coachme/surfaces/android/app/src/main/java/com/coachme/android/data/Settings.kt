package com.coachme.android.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKeys
import com.coachme.android.BuildConfig
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.onStart
import kotlinx.coroutines.flow.update

/** The API + analysis settings (same values as the desktop `.env`). */
data class AppSettings(
    val apiBase: String = BuildConfig.DEFAULT_API_BASE.ifBlank { "https://api.deepseek.com" },
    val apiKey: String = BuildConfig.DEFAULT_API_KEY,
    val textModel: String = BuildConfig.DEFAULT_TEXT_MODEL.ifBlank { "deepseek-v4-pro" },
    val visionModel: String = BuildConfig.DEFAULT_VISION_MODEL.ifBlank { "deepseek-v4-flash-vision-exp" },
    val agentic: Boolean = false,
    val maxFrames: Int = 12,
    val showDemo: Boolean = true,
    // player profile (feeds prompts + rubric)
    val sport: String = "table tennis",
    val level: String = "intermediate",
    val hand: String = "right",
    val goal: String = "improve",
    val theme: String = "system",
    val language: String = "system",
    val appStyle: String = "sport",
    val lastTestAt: Long = 0L,
    val apiKeyFromBuild: Boolean = BuildConfig.DEFAULT_API_KEY.isNotBlank(),
)

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore("coachme")

class SettingsStore(private val context: Context) {
    private object K {
        val apiBase = stringPreferencesKey("api_base")
        val apiKey = stringPreferencesKey("api_key")
        val textModel = stringPreferencesKey("text_model")
        val visionModel = stringPreferencesKey("vision_model")
        val agentic = booleanPreferencesKey("agentic")
        val maxFrames = intPreferencesKey("max_frames")
        val showDemo = booleanPreferencesKey("show_demo")
        val sport = stringPreferencesKey("sport")
        val level = stringPreferencesKey("level")
        val hand = stringPreferencesKey("hand")
        val goal = stringPreferencesKey("goal")
        val theme = stringPreferencesKey("theme")
        val language = stringPreferencesKey("language")
        val appStyle = stringPreferencesKey("app_style")
        val dynamicColor = booleanPreferencesKey("dynamic_color")
        val sportMode = booleanPreferencesKey("sport_mode")
        val lastTestAt = longPreferencesKey("last_test_at")
    }

    private companion object {
        const val SECRET_API_KEY = "api_key"
    }

    private val secretPrefs = run {
        val masterKeyAlias = MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC)
        EncryptedSharedPreferences.create(
            "coachme_secrets",
            masterKeyAlias,
            context,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }
    private val apiKey = MutableStateFlow(secretPrefs.getString(SECRET_API_KEY, "") ?: "")
    private val apiKeyStored = MutableStateFlow(secretPrefs.contains(SECRET_API_KEY))

    private suspend fun migrateLegacyKey() {
        val legacy = context.dataStore.data.first()[K.apiKey]?.takeIf { it.isNotBlank() } ?: return
        if (apiKey.value.isBlank()) {
            secretPrefs.edit().putString(SECRET_API_KEY, legacy).apply()
            apiKey.value = legacy
            apiKeyStored.value = true
        }
        context.dataStore.edit { it.remove(K.apiKey) }
    }

    val flow: Flow<AppSettings> = combine(context.dataStore.data, apiKey, apiKeyStored) { p, key, stored ->
        AppSettings(
            apiBase = p[K.apiBase] ?: AppSettings().apiBase,
            apiKey = if (stored) key else BuildConfig.DEFAULT_API_KEY,
            apiKeyFromBuild = !stored && BuildConfig.DEFAULT_API_KEY.isNotBlank(),
            textModel = p[K.textModel] ?: AppSettings().textModel,
            visionModel = p[K.visionModel] ?: AppSettings().visionModel,
            agentic = p[K.agentic] ?: false,
            maxFrames = p[K.maxFrames] ?: 12,
            showDemo = p[K.showDemo] ?: true,
            sport = p[K.sport] ?: "table tennis",
            level = p[K.level] ?: "intermediate",
            hand = p[K.hand] ?: "right",
            goal = p[K.goal] ?: "improve",
            theme = p[K.theme] ?: "system",
            language = p[K.language] ?: "system",
            appStyle = p[K.appStyle] ?: when {
                p[K.sportMode] == true -> "sport"
                p[K.dynamicColor] == true -> "dynamic"
                else -> "sport"
            },
            lastTestAt = p[K.lastTestAt] ?: 0L,
        )
    }.onStart { migrateLegacyKey() }

    suspend fun save(s: AppSettings) {
        val clean = s.copy(
            apiBase = s.apiBase.trim(),
            apiKey = s.apiKey.trim(),
            textModel = s.textModel.trim(),
            visionModel = s.visionModel.trim(),
            sport = s.sport.trim(),
        )
        secretPrefs.edit().putString(SECRET_API_KEY, clean.apiKey).apply()
        apiKey.update { clean.apiKey }
        apiKeyStored.update { true }
        context.dataStore.edit { p ->
            p[K.apiBase] = clean.apiBase
            p.remove(K.apiKey)
            p[K.textModel] = clean.textModel
            p[K.visionModel] = clean.visionModel
            p[K.agentic] = clean.agentic
            p[K.maxFrames] = clean.maxFrames
            p[K.showDemo] = clean.showDemo
            p[K.sport] = clean.sport
            p[K.level] = clean.level
            p[K.hand] = clean.hand
            p[K.goal] = clean.goal
            p[K.theme] = clean.theme
            p[K.language] = clean.language
            p[K.appStyle] = clean.appStyle
            p[K.lastTestAt] = clean.lastTestAt
        }
    }
}
