package com.coachme.android.ui

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.os.Bundle
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import java.util.Locale

/** Read-aloud + speech-to-text helpers (Appendix H · voice ask). */

@Composable
fun rememberTts(): TextToSpeech? {
    val ctx = LocalContext.current
    val tts = remember { mutableStateOf<TextToSpeech?>(null) }
    DisposableEffect(Unit) {
        val engine = TextToSpeech(ctx) { }
        engine.language = Locale.US
        tts.value = engine
        onDispose { engine.stop(); engine.shutdown() }
    }
    return tts.value
}

@Composable
fun SpeakButton(text: String) {
    val tts = rememberTts()
    val speaking = remember { mutableStateOf(false) }
    DisposableEffect(tts) {
        tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) { speaking.value = true }
            override fun onDone(utteranceId: String?) { speaking.value = false }
            @Deprecated("Deprecated in Java")
            override fun onError(utteranceId: String?) { speaking.value = false }
            override fun onStop(utteranceId: String?, interrupted: Boolean) { speaking.value = false }
        })
        onDispose { }
    }
    IconButton(onClick = {
        val engine = tts ?: return@IconButton
        if (speaking.value) {
            engine.stop()
            speaking.value = false
        } else {
            speaking.value = true
            engine.speak(text, TextToSpeech.QUEUE_FLUSH, null, "read-aloud")
        }
    }) {
        Icon(
            if (speaking.value) Icons.Filled.Stop else Icons.Filled.VolumeUp,
            contentDescription = if (speaking.value) "Stop reading" else "Read aloud",
        )
    }
}

@Composable
fun MicButton(onText: (String) -> Unit) {
    val ctx = LocalContext.current
    val recognizer = remember { SpeechRecognizer.createSpeechRecognizer(ctx) }
    val intent = remember {
        Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            .putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            .putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-US")
    }
    DisposableEffect(Unit) { onDispose { recognizer.destroy() } }

    recognizer.setRecognitionListener(object : RecognitionListener {
        override fun onResults(results: Bundle?) {
            val list = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
            list?.firstOrNull()?.let(onText)
        }
        override fun onError(error: Int) {}
        override fun onReadyForSpeech(params: Bundle?) {}
        override fun onBeginningOfSpeech() {}
        override fun onRmsChanged(rmsdB: Float) {}
        override fun onBufferReceived(buffer: ByteArray?) {}
        override fun onEndOfSpeech() {}
        override fun onPartialResults(partialResults: Bundle?) {}
        override fun onEvent(eventType: Int, params: Bundle?) {}
    })

    val permLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) recognizer.startListening(intent)
    }
    IconButton(onClick = {
        if (ctx.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
            recognizer.startListening(intent)
        } else {
            permLauncher.launch(Manifest.permission.RECORD_AUDIO)
        }
    }) {
        Icon(Icons.Filled.Mic, contentDescription = "Ask by voice")
    }
}
