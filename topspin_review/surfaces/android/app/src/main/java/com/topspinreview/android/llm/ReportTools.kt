package com.topspinreview.android.llm

import com.topspinreview.android.data.ReportStore
import com.topspinreview.android.data.SettingsStore
import kotlinx.coroutines.flow.first
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/** The agent's tools (ported from `core/stages/coach/report_tools.py`). */
class ReportTools(
    private val settings: SettingsStore,
    private val store: ReportStore,
    private val json: Json,
) {
    /** Stem of the last report saved this run (read by the pipeline). */
    var lastSavedStem: String? = null
        private set
    /** Name + JSON-schema for each tool, for the `tools` field of the request. */
    fun schemas(): JsonArray = buildJsonArray {
        add(fn("get_profile", "Return the player profile as JSON."))
        add(
            fn(
                "recent_reports", "Return the most recent saved reports as a JSON array.",
                buildJsonObject {
                    put("type", "object")
                    put("properties", buildJsonObject {
                        put("n", buildJsonObject { put("type", "integer") })
                    })
                },
            )
        )
        add(
            fn(
                "save_report", "Save the coaching report.",
                buildJsonObject {
                    put("type", "object")
                    put("properties", buildJsonObject {
                        put("report_json", buildJsonObject { put("type", "string") })
                    })
                    put("required", buildJsonArray { add(kotlinx.serialization.json.JsonPrimitive("report_json")) })
                },
            )
        )
    }

    private fun fn(name: String, description: String, params: JsonObject = buildJsonObject {
        put("type", "object"); put("properties", buildJsonObject {})
    }) = buildJsonObject {
        put("type", "function")
        put("function", buildJsonObject {
            put("name", name); put("description", description); put("parameters", params)
        })
    }

    /** Run a tool by name; returns its text result. */
    suspend fun execute(name: String, argumentsJson: String): String = when (name) {
        "get_profile" -> json.encodeToString(JsonObject.serializer(), profileJson())
        "recent_reports" -> {
            val n = runCatching {
                json.parseToJsonElement(argumentsJson).jsonObject["n"]?.jsonPrimitive?.intOrNull
            }.getOrNull() ?: 5
            store.recentJson(n)
        }
        "save_report" -> saveReport(argumentsJson)
        else -> "unknown tool: $name"
    }

    private suspend fun profileJson(): JsonObject {
        val s = settings.flow.first()
        return buildJsonObject {
            put("sport", s.sport); put("level", s.level)
            put("dominant_hand", s.hand); put("goal", s.goal)
        }
    }

    private fun saveReport(argumentsJson: String): String {
        return try {
            val args = json.parseToJsonElement(argumentsJson).jsonObject
            val raw = args["report_json"]?.jsonPrimitive?.content ?: return "report must be a JSON object"
            var obj = json.parseToJsonElement(raw).jsonObject
            if (obj["date"]?.jsonPrimitive?.content.isNullOrBlank()) {
                val today = SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date())
                obj = JsonObject(obj + ("date" to kotlinx.serialization.json.JsonPrimitive(today)))
            }
            val stem = obj["source"]?.jsonPrimitive?.content?.substringAfterLast('/')?.substringBeforeLast('.')
                ?: "session_" + System.currentTimeMillis()
            store.saveRaw(stem, json.encodeToString(JsonObject.serializer(), obj))
            lastSavedStem = stem
            "report saved"
        } catch (e: Exception) {
            "report save failed: ${e.message}"
        }
    }
}
