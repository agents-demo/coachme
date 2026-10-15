package com.topspinreview.android.ui

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

/** Navigation graph (Appendix H): sessions → new / result / settings. */
@Composable
fun AppNav() {
    val nav = rememberNavController()
    NavHost(navController = nav, startDestination = "sessions") {
        composable("sessions") {
            SessionsScreen(
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
                onBack = { nav.popBackStack() },
                onOpenDiagnostics = { s -> nav.navigate("diagnostics/$s") },
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
