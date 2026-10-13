package com.topspinreview.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.topspinreview.android.ui.AppNav
import com.topspinreview.android.ui.theme.TopspinTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            TopspinTheme {
                AppNav()
            }
        }
    }
}
