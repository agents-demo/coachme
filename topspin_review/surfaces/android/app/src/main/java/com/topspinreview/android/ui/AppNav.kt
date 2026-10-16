package com.topspinreview.android.ui

import androidx.compose.animation.ExperimentalSharedTransitionApi
import androidx.compose.animation.SharedTransitionLayout
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.topspinreview.android.ui.compare.CompareScreen
import com.topspinreview.android.ui.newanalysis.NewAnalysisScreen
import com.topspinreview.android.ui.result.DiagnosticsScreen
import com.topspinreview.android.ui.result.ResultScreen
import com.topspinreview.android.ui.sessions.SessionsScreen
import com.topspinreview.android.ui.settings.SettingsScreen

private const val SLIDE_DURATION = 380

/** Navigation graph (Appendix H): sessions → new / result / settings. */
@OptIn(ExperimentalSharedTransitionApi::class)
@Composable
fun AppNav() {
    val nav = rememberNavController()
    SharedTransitionLayout {
        NavHost(
            navController = nav,
            startDestination = "sessions",
            enterTransition = {
                slideInHorizontally(tween(SLIDE_DURATION)) { it } + fadeIn(tween(SLIDE_DURATION))
            },
            exitTransition = {
                slideOutHorizontally(tween(SLIDE_DURATION)) { -it / 3 } + fadeOut(tween(SLIDE_DURATION))
            },
            popEnterTransition = {
                slideInHorizontally(tween(SLIDE_DURATION)) { -it / 3 } + fadeIn(tween(SLIDE_DURATION))
            },
            popExitTransition = {
                slideOutHorizontally(tween(SLIDE_DURATION)) { it } + fadeOut(tween(SLIDE_DURATION))
            },
        ) {
            composable("sessions") {
                SessionsScreen(
                    sharedTransitionScope = this@SharedTransitionLayout,
                    animatedVisibilityScope = this@composable,
                    onOpen = { stem -> nav.navigate("result/$stem") },
                    onNew = { nav.navigate("new") },
                    onSettings = { nav.navigate("settings") },
                    onCompare = { nav.navigate("compare") },
                    onResume = { stem -> nav.navigate("new?resume=$stem") },
                )
            }
            composable(
                "new?resume={resume}",
                arguments = listOf(navArgument("resume") {
                    type = NavType.StringType
                    nullable = true
                    defaultValue = null
                }),
            ) { entry ->
                NewAnalysisScreen(
                    resumeStem = entry.arguments?.getString("resume"),
                    onDone = { stem -> nav.navigate("result/$stem") { popUpTo("sessions") } },
                    onBack = { nav.popBackStack() },
                )
            }
            composable(
                "result/{stem}",
                arguments = listOf(navArgument("stem") { type = NavType.StringType }),
            ) { entry ->
                ResultScreen(
                    stem = entry.arguments?.getString("stem").orEmpty(),
                    sharedTransitionScope = this@SharedTransitionLayout,
                    animatedVisibilityScope = this@composable,
                    onBack = { nav.popBackStack() },
                    onOpenDiagnostics = { s -> nav.navigate("diagnostics/$s") },
                    onRetryAnalysis = { s -> nav.navigate("new?resume=$s") },
                )
            }
            composable(
                "diagnostics/{stem}",
                arguments = listOf(navArgument("stem") { type = NavType.StringType }),
            ) { entry ->
                DiagnosticsScreen(
                    stem = entry.arguments?.getString("stem").orEmpty(),
                    onBack = { nav.popBackStack() },
                )
            }
            composable("settings") { SettingsScreen(onBack = { nav.popBackStack() }) }
            composable("compare") { CompareScreen(onBack = { nav.popBackStack() }) }
        }
    }
}
