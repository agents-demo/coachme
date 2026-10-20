package com.coachme.android.ui.result

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import com.coachme.android.ui.components.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.dp
import com.coachme.android.ui.theme.Accent
import com.coachme.android.ui.theme.Accent2
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlin.math.cos
import kotlin.math.sin

private val SKELETON = listOf(
    11 to 12, 11 to 13, 13 to 15, 12 to 14, 14 to 16,
    11 to 23, 12 to 24, 23 to 24, 23 to 25, 25 to 27, 24 to 26, 26 to 28,
)

/** Orthographic projection of a 3D point with yaw/pitch rotation. */
private fun project(x: Double, y: Double, z: Double, yaw: Double, pitch: Double): Pair<Double, Double> {
    val cy = cos(yaw); val sy = sin(yaw)
    val x1 = x * cy + z * sy
    val z1 = -x * sy + z * cy
    val cp = cos(pitch); val sp = sin(pitch)
    val y1 = y * cp - z1 * sp
    return x1 to y1
}

/** Body 3D: a rotatable stick figure from the pose world landmarks. Ported from `pose.Pose3D`. */
@Composable
fun Pose3DView(pose3d: JsonArray) {
    val frame = remember(pose3d) {
        pose3d.mapNotNull { it as? JsonArray }.maxByOrNull { it.size } ?: JsonArray(emptyList())
    }
    val pts = remember(frame) {
        frame.mapNotNull { el ->
            val a = el as? JsonArray ?: return@mapNotNull null
            Triple(
                a.getOrNull(0)?.toString()?.toDoubleOrNull() ?: 0.0,
                a.getOrNull(1)?.toString()?.toDoubleOrNull() ?: 0.0,
                a.getOrNull(2)?.toString()?.toDoubleOrNull() ?: 0.0,
            )
        }
    }
    if (pts.size < 29) return
    var yaw by remember { mutableStateOf(0.0) }
    var pitch by remember { mutableStateOf(0.0) }

    Text("Drag to rotate", style = MaterialTheme.typography.bodySmall)
    Canvas(
        Modifier.fillMaxWidth().height(220.dp).pointerInput(Unit) {
            detectDragGestures { _, drag ->
                yaw += drag.x / 200.0
                pitch += drag.y / 200.0
            }
        },
    ) {
        val w = size.width; val h = size.height
        val hipX = (pts[23].first + pts[24].first) / 2
        val hipY = (pts[23].second + pts[24].second) / 2
        val scale = minOf(w, h) / 2.2
        fun screen(i: Int): Offset {
            val (x, y, z) = pts[i]
            val (px, py) = project(x - hipX, y - hipY, z, yaw, pitch)
            return Offset((w / 2 + px * scale).toFloat(), (h / 2 + py * scale).toFloat())
        }
        SKELETON.forEach { (a, b) ->
            if (a < pts.size && b < pts.size) drawLine(Accent2, screen(a), screen(b), strokeWidth = 5f)
        }
        pts.indices.forEach { drawCircle(Accent, radius = 4f, center = screen(it)) }
    }
}

/** Object trajectory in 3D (rotatable). */
@Composable
fun Trajectory3DView(traj: JsonArray) {
    val pts = remember(traj) {
        traj.mapNotNull { el ->
            val o = el as? JsonObject ?: return@mapNotNull null
            Triple(
                o["x"]?.toString()?.toDoubleOrNull() ?: return@mapNotNull null,
                o["y"]?.toString()?.toDoubleOrNull() ?: return@mapNotNull null,
                o["z"]?.toString()?.toDoubleOrNull() ?: 0.0,
            )
        }
    }
    if (pts.size < 3) return
    var yaw by remember { mutableStateOf(0.0) }
    var pitch by remember { mutableStateOf(0.0) }

    Text("Drag to rotate", style = MaterialTheme.typography.bodySmall)
    Canvas(
        Modifier.fillMaxWidth().height(220.dp).pointerInput(Unit) {
            detectDragGestures { _, drag ->
                yaw += drag.x / 200.0
                pitch += drag.y / 200.0
            }
        },
    ) {
        val w = size.width; val h = size.height
        val cx = pts.map { it.first }.average(); val cy = pts.map { it.second }.average()
        val scale = minOf(w, h) * 0.8
        val screen = pts.map { (x, y, z) ->
            val (px, py) = project(x - cx, y - cy, z, yaw, pitch)
            Offset((w / 2 + px * scale).toFloat(), (h / 2 + py * scale).toFloat())
        }
        for (i in 1 until screen.size) drawLine(Accent2, screen[i - 1], screen[i], strokeWidth = 4f)
        screen.forEach { drawCircle(Accent, radius = 3f, center = it) }
    }
}
