package com.coachme.android.llm

import com.coachme.android.data.AppSettings
import com.coachme.android.data.SettingsStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.put
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody

data class ToolCall(val id: String, val name: String, val arguments: String)
data class ChatResponse(val content: String, val toolCalls: List<ToolCall>)

/** One recorded model call, for the Diagnostics tab. */
data class CallInfo(
    val stage: String, val model: String,
    val promptTokens: Int, val completionTokens: Int, val seconds: Double,
)

/**
 * Direct DeepSeek (OpenAI-compatible) client — the Android replacement for openjiuwen.
 * Text + vision + a small tool-call loop, using the API values from Settings.
 */
class DeepSeekClient(
    private val http: OkHttpClient,
    private val json: Json,
    private val settings: SettingsStore,
) {
    private val JSON_MEDIA = "application/json; charset=utf-8".toMediaType()

    /** Current stage label, set by the pipeline; recorded with each call. */
    var stage: String = ""
    val calls = mutableListOf<CallInfo>()

    /** Seed the call log when resuming a run (so usage/cost reflects the whole session). */
    fun restoreCalls(list: List<CallInfo>) {
        calls.clear()
        calls.addAll(list)
    }

    private suspend fun cfg(): AppSettings = settings.flow.first()

    suspend fun vision(system: String, promptText: String, imagesBase64Jpeg: List<String>): String {
        val content = buildJsonArray {
            add(buildJsonObject { put("type", "text"); put("text", promptText) })
            for (b64 in imagesBase64Jpeg) {
                add(
                    buildJsonObject {
                        put("type", "image_url")
                        put("image_url", buildJsonObject { put("url", "data:image/jpeg;base64,$b64") })
                    }
                )
            }
        }
        val messages = buildJsonArray {
            add(buildJsonObject { put("role", "system"); put("content", system) })
            add(buildJsonObject { put("role", "user"); put("content", content) })
        }
        val cfg = cfg()
        val body = buildJsonObject {
            put("model", cfg.visionModel)
            put("temperature", 0)
            put("messages", messages)
        }
        return post(cfg, body).content
    }

    /** Note: plain text (no tools). `toolChoice` is only used by the agent loop. */
    suspend fun text(system: String, user: String): String {
        val messages = buildJsonArray {
            add(buildJsonObject { put("role", "system"); put("content", system) })
            add(buildJsonObject { put("role", "user"); put("content", user) })
        }
        val cfg = cfg()
        val body = buildJsonObject {
            put("model", cfg.textModel)
            put("messages", messages)
        }
        return post(cfg, body).content
    }

    /** One chat turn with optional tools (used by ReportTools' agent loop). */
    suspend fun chat(messages: JsonArray, tools: JsonArray?): ChatResponse {
        val cfg = cfg()
        val body = buildJsonObject {
            put("model", cfg.textModel)
            put("messages", messages)
            if (tools != null) { put("tools", tools); put("tool_choice", "auto") }
        }
        return post(cfg, body)
    }

    private suspend fun post(cfg: AppSettings, body: JsonObject): ChatResponse {
        var last: Exception? = null
        for (attempt in 0 until 3) {
            try {
                return doPost(cfg, body)
            } catch (e: java.net.UnknownHostException) {
                last = e; kotlinx.coroutines.delay(700L * (attempt + 1))
            } catch (e: java.io.IOException) {
                last = e; kotlinx.coroutines.delay(700L * (attempt + 1))
            }
        }
        val host = cfg.apiBase.trimEnd('/')
        throw IllegalStateException("Network error reaching $host — check the phone's internet / Private DNS.", last)
    }

    private suspend fun doPost(cfg: AppSettings, body: JsonObject): ChatResponse = withContext(Dispatchers.IO) {
        val started = System.nanoTime()
        val req = Request.Builder()
            .url(cfg.apiBase.trimEnd('/') + "/chat/completions")
            .addHeader("Authorization", "Bearer ${cfg.apiKey}")
            .addHeader("Content-Type", "application/json")
            .post(body.toString().toRequestBody(JSON_MEDIA))
            .build()
        http.newCall(req).execute().use { resp ->
            val raw = resp.body?.string().orEmpty()
            if (!resp.isSuccessful) error("HTTP ${resp.code}: ${raw.take(400)}")
            val root = json.parseToJsonElement(raw).jsonObject
            val msg = root["choices"]!!.jsonArray[0].jsonObject["message"]!!.jsonObject
            val content = (msg["content"] as? JsonPrimitive)?.content.orEmpty()
            val calls = (msg["tool_calls"] as? JsonArray)?.mapNotNull { el ->
                val o = el.jsonObject
                val fn = o["function"]?.jsonObject ?: return@mapNotNull null
                ToolCall(
                    id = o["id"]?.jsonPrimitive?.content.orEmpty(),
                    name = fn["name"]?.jsonPrimitive?.content.orEmpty(),
                    arguments = fn["arguments"]?.jsonPrimitive?.content.orEmpty(),
                )
            } ?: emptyList()
            val usage = root["usage"] as? JsonObject
            val pt = usage?.get("prompt_tokens")?.jsonPrimitive?.intOrNull ?: 0
            val ct = usage?.get("completion_tokens")?.jsonPrimitive?.intOrNull ?: 0
            val model = body["model"]?.jsonPrimitive?.content.orEmpty()
            this@DeepSeekClient.calls.add(CallInfo(stage, model, pt, ct, (System.nanoTime() - started) / 1e9))
            ChatResponse(content, calls)
        }
    }
}
