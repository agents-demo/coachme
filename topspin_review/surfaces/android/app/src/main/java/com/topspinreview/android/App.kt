package com.topspinreview.android

import android.app.Application
import com.topspinreview.android.data.Youtube
import dagger.hilt.android.HiltAndroidApp

/** Application root. Hilt provides the object graph (settings, client, store, pipeline). */
@HiltAndroidApp
class App : Application() {
    override fun onCreate() {
        super.onCreate()
        // Prepare the yt-dlp environment in the background so the first YouTube link is quick.
        Youtube.warmUp(this)
    }
}
