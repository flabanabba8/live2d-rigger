package org.umamo.cli

import java.io.File
import kotlinx.serialization.json.*
import org.umamo.runtime.model.*
import org.umamo.format.moc3.moc.MocVersion
import org.umamo.interop.moc3.Moc3Sidecars
import org.umamo.interop.describeExportNotice
import org.umamo.render.canvasToParentSpaceFor

// Generic separate-layer transport. This exports a static model, not a rig.
fun main(args: Array<String>) {
    val project = File(args[0]); val output = File(args[1]); output.mkdirs()
    val doc = Json.parseToJsonElement(File(project, "model-project.json").readText()).jsonObject
    val rows = doc.getValue("layers").jsonArray
    val canvas = doc["canvas"]?.jsonArray ?: rows.first { it.jsonObject["offset"] is JsonNull }.jsonObject.getValue("dimensions").jsonArray
    val width = canvas[0].jsonPrimitive.float; val height = canvas[1].jsonPrimitive.float
    val draws = rows.mapIndexed { i, row ->
        val item = row.jsonObject; val dimensions = item.getValue("dimensions").jsonArray
        val offset = item["offset"]
        val placement = item["placement"]?.jsonObject
        val x = placement?.get("x")?.jsonPrimitive?.float ?: if (offset == null || offset is JsonNull) 0f else offset.jsonArray[0].jsonPrimitive.float
        val y = placement?.get("y")?.jsonPrimitive?.float ?: if (offset == null || offset is JsonNull) 0f else offset.jsonArray[1].jsonPrimitive.float
        val scale = placement?.get("scale")?.jsonPrimitive?.float ?: 1f
        val sx=placement?.get("scale_x")?.jsonPrimitive?.float ?: scale;val sy=placement?.get("scale_y")?.jsonPrimitive?.float ?: scale
        val w = dimensions[0].jsonPrimitive.float * sx; val h = dimensions[1].jsonPrimitive.float * sy
        val mesh = DrawableMesh(floatArrayOf(x,y,x+w,y,x+w,y+h,x,y+h), floatArrayOf(0f,0f,1f,0f,1f,1f,0f,1f), intArrayOf(0,1,2,0,2,3))
        val id = "Part" + i
        Drawable(DrawableId(id), item.getValue("name").jsonPrimitive.content, null, BlendMode.Normal, emptyList(), mesh, null, drawOrder=i.toFloat(), texturePage=i)
    }
    val model = PuppetModel(emptyList(), emptyList(), emptyList(), draws, draws.map { OrgChild.Drawable(it.id) }, null,
        canvasWidth=width, canvasHeight=height, worldOriginX=width/2, worldOriginZ=-height/2, pixelsPerUnit=1000f).withDerivedRenderRoot()
    val pages = rows.mapIndexed { i, row ->
        val path = row.jsonObject.getValue("path").jsonPrimitive.content
        Moc3Sidecars.AtlasPage("textures/part${i}.png", File(project, path).readBytes())
    }
    val bundle = Moc3Sidecars.bundle(model, "Model", version=MocVersion.V40, pages=pages, canvasToParentSpace=canvasToParentSpaceFor(model))
    bundle.report.notices.forEach { println(describeExportNotice(it)) }
    check(bundle.report.notices.isEmpty()) { "Export reported notices" }
    bundle.files.forEach { f -> File(output, f.name).apply { parentFile.mkdirs(); writeBytes(f.bytes) } }
    println("Static layer transport only: no controls, physics or animated rig")
}
