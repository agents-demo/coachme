package com.topspinreview.android

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

/** Application root. Hilt provides the object graph (settings, client, store, pipeline). */
@HiltAndroidApp
class App : Application()
