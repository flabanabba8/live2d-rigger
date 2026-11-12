package org.umamo.cli

import java.io.File
import javax.imageio.ImageIO
import kotlin.math.sin
import kotlin.math.cos
import kotlin.math.PI
import kotlinx.serialization.json.*
import org.umamo.runtime.model.*
import org.umamo.format.moc3.moc.MocVersion
import org.umamo.interop.moc3.Moc3Sidecars
import org.umamo.interop.describeExportNotice

// Experimental head-roll prototype. No XY, expressions or physics are authored.
fun main(args: Array<String>) {
    val project = File(args[0]); val output = File(args[1]); output.mkdirs()
    val doc = Json.parseToJsonElement(File(project, "model-project.json").readText()).jsonObject
    val rows = doc.getValue("layers").jsonArray
    val canvas = doc["canvas"]?.jsonArray ?: rows.first { it.jsonObject["offset"] is JsonNull }.jsonObject.getValue("dimensions").jsonArray
    val width = canvas[0].jsonPrimitive.float; val height = canvas[1].jsonPrimitive.float
    fun box(item: JsonObject): FloatArray {
        val img=ImageIO.read(File(project,item.getValue("path").jsonPrimitive.content))
        var minX=img.width;var minY=img.height;var maxX=-1;var maxY=-1
        for (y in 0 until img.height) for (x in 0 until img.width) if ((img.getRGB(x,y) ushr 24)>0) {
            minX=minOf(minX,x);minY=minOf(minY,y);maxX=maxOf(maxX,x);maxY=maxOf(maxY,y)
        }
        check(maxX>=0) { "Empty face art" }
        val o=item["offset"];val p=item["placement"]?.jsonObject
        val ox=p?.get("x")?.jsonPrimitive?.float ?: if(o==null || o is JsonNull) 0f else o.jsonArray[0].jsonPrimitive.float
        val oy=p?.get("y")?.jsonPrimitive?.float ?: if(o==null || o is JsonNull) 0f else o.jsonArray[1].jsonPrimitive.float
        val scale=p?.get("scale")?.jsonPrimitive?.float ?: 1f
        val sx=p?.get("scale_x")?.jsonPrimitive?.float ?: scale;val sy=p?.get("scale_y")?.jsonPrimitive?.float ?: scale
        return floatArrayOf(ox+(minX+maxX+1)*sx/2,oy+(minY+maxY+1)*sy/2,oy+(maxY+1)*sy,(maxX-minX+1)*sx,(maxY-minY+1)*sy)
    }
    val face=rows.firstOrNull { val o=it.jsonObject;(o.getValue("name").jsonPrimitive.content+" "+o.getValue("role").jsonPrimitive.content).lowercase().contains("face") }
        ?: error("A named face layer is required for the prototype head pivot")
    val pivot=box(face.jsonObject)
    val angle=Parameter(ParameterId("ParamAngleZ"),"Experimental head roll",-10f,10f,0f)
    fun label(row:JsonElement):String { val o=row.jsonObject;return (o.getValue("name").jsonPrimitive.content+" "+o.getValue("role").jsonPrimitive.content).lowercase() }
    val body=rows.firstOrNull { row -> listOf("body","torso","dress").any { it in label(row) } }
    val bodyPivot=body?.let { box(it.jsonObject) }
    val bodyAngle=Parameter(ParameterId("ParamBodyAngleZ"),"Experimental body sway",-5f,5f,0f)
    val breath=Parameter(ParameterId("ParamBreath"),"Experimental breathing",0f,1f,0f)
    fun side(name:String):String? = when {
        "left" in name || "_l_" in name || name.endsWith("_l") -> "L"
        "right" in name || "_r_" in name || name.endsWith("_r") -> "R"
        else -> null
    }
    val whites=rows.mapIndexedNotNull { i,row ->
        val t=label(row);val side=side(t)
        if(side!=null && ("eye_white" in t || "eye white" in t || "eye-white" in t || "eye_combined" in t)) side to i else null
    }.toMap()
    val eyePivots=whites.mapValues { (_,index) -> box(rows[index].jsonObject) }
    fun colouredRegion(item:JsonObject):FloatArray? {
        val img=ImageIO.read(File(project,item.getValue("path").jsonPrimitive.content))
        var minX=img.width;var minY=img.height;var maxX=-1;var maxY=-1;var count=0
        for(yy in 0 until img.height) for(xx in 0 until img.width) {
            val p=img.getRGB(xx,yy);if((p ushr 24)<128)continue
            val r=(p shr 16) and 255;val g=(p shr 8) and 255;val b=p and 255
            val hi=maxOf(r,g,b);val lo=minOf(r,g,b)
            if(hi>40 && hi-lo>45 && (hi-lo).toFloat()/hi>.3f) {minX=minOf(minX,xx);maxX=maxOf(maxX,xx);minY=minOf(minY,yy);maxY=maxOf(maxY,yy);count++}
        }
        if(count<30 || maxX<minX || maxY<minY)return null
        val o=item["offset"];val p=item["placement"]?.jsonObject
        val ox=p?.get("x")?.jsonPrimitive?.float ?: if(o==null || o is JsonNull) 0f else o.jsonArray[0].jsonPrimitive.float
        val oy=p?.get("y")?.jsonPrimitive?.float ?: if(o==null || o is JsonNull) 0f else o.jsonArray[1].jsonPrimitive.float
        val scale=p?.get("scale")?.jsonPrimitive?.float ?: 1f
        val sx=p?.get("scale_x")?.jsonPrimitive?.float ?: scale;val sy=p?.get("scale_y")?.jsonPrimitive?.float ?: scale
        return floatArrayOf(ox+(minX+maxX+1)*sx/2,oy+(minY+maxY+1)*sy/2,(maxX-minX+1)*sx,(maxY-minY+1)*sy)
    }
    val combinedRegions=whites.mapNotNull { (side,index) ->
        val item=rows[index].jsonObject;val kind=item.getValue("name").jsonPrimitive.content.lowercase()
        if("eye_combined" in kind) colouredRegion(item)?.let { side to it } else null
    }.toMap()
    val leftOpen=Parameter(ParameterId("ParamEyeLOpen"),"Experimental left blink",0f,1f,1f)
    val rightOpen=Parameter(ParameterId("ParamEyeROpen"),"Experimental right blink",0f,1f,1f)
    val gazeX=Parameter(ParameterId("ParamEyeBallX"),"Experimental eye look X",-1f,1f,0f)
    val gazeY=Parameter(ParameterId("ParamEyeBallY"),"Experimental eye look Y",-1f,1f,0f)
    val hasIris=combinedRegions.isNotEmpty() || rows.any { val n=it.jsonObject.getValue("name").jsonPrimitive.content.lowercase(); "iris" in n && side(n) in whites.keys }
    val mouthIndex=rows.indexOfFirst { row -> val n=row.jsonObject.getValue("name").jsonPrimitive.content.lowercase(); "mouth_inside" in n || "mouth_cavity" in n }
    val mouthPivot=if(mouthIndex>=0) box(rows[mouthIndex].jsonObject) else null
    val mouthOpen=Parameter(ParameterId("ParamMouthOpenY"),"Experimental mouth open",0f,1f,0f)
    val hairIndex=rows.indexOfFirst { row -> "hair" in row.jsonObject.getValue("name").jsonPrimitive.content.lowercase() }
    val hairPivot=if(hairIndex>=0) box(rows[hairIndex].jsonObject) else null
    val hairSway=Parameter(ParameterId("ParamHairBack"),"Experimental back hair sway",-1f,1f,0f)
    val draws = rows.mapIndexed { i, row ->
        val item = row.jsonObject; val dimensions = item.getValue("dimensions").jsonArray
        val offset = item["offset"]
        val placement = item["placement"]?.jsonObject
        val x = placement?.get("x")?.jsonPrimitive?.float ?: if (offset == null || offset is JsonNull) 0f else offset.jsonArray[0].jsonPrimitive.float
        val y = placement?.get("y")?.jsonPrimitive?.float ?: if (offset == null || offset is JsonNull) 0f else offset.jsonArray[1].jsonPrimitive.float
        val scale = placement?.get("scale")?.jsonPrimitive?.float ?: 1f
        val sx=placement?.get("scale_x")?.jsonPrimitive?.float ?: scale;val sy=placement?.get("scale_y")?.jsonPrimitive?.float ?: scale
        val w = dimensions[0].jsonPrimitive.float * sx; val h = dimensions[1].jsonPrimitive.float * sy
        val mesh = if(i==hairIndex && hairPivot!=null) {
            val top=hairPivot[2]-hairPivot[4]
            val ys=listOf(y,top,top+hairPivot[4]*.35f,hairPivot[2],y+h).map { it.coerceIn(y,y+h) }.distinct().sorted()
            val positions=ys.flatMap { rowY -> listOf(x,rowY,x+w,rowY) }.toFloatArray()
            val uv=ys.flatMap { rowY -> val v=(rowY-y)/h;listOf(0f,v,1f,v) }.toFloatArray()
            val triangles=mutableListOf<Int>();for(j in 0 until ys.size-1) {val a=j*2;triangles.addAll(listOf(a,a+1,a+3,a,a+3,a+2))}
            DrawableMesh.withLocalEqualToCanvas(positions,uv,triangles.toIntArray())
        } else if("eye_combined" in item.getValue("name").jsonPrimitive.content.lowercase()) {
            val ext=box(item);val left=ext[0]-ext[3]/2;val top=ext[1]-ext[4]/2;val cols=12;val lines=12
            val positions=mutableListOf<Float>();val uv=mutableListOf<Float>();val triangles=mutableListOf<Int>()
            for(j in 0..lines) for(k in 0..cols) {val px=left+ext[3]*k/cols;val py=top+ext[4]*j/lines;positions.addAll(listOf(px,py));uv.addAll(listOf((px-x)/w,(py-y)/h))}
            for(j in 0 until lines) for(k in 0 until cols) {val a=j*(cols+1)+k;triangles.addAll(listOf(a,a+1,a+cols+2,a,a+cols+2,a+cols+1))}
            DrawableMesh.withLocalEqualToCanvas(positions.toFloatArray(),uv.toFloatArray(),triangles.toIntArray())
        } else DrawableMesh.withLocalEqualToCanvas(floatArrayOf(x,y,x+w,y,x+w,y+h,x,y+h), floatArrayOf(0f,0f,1f,0f,1f,1f,0f,1f), intArrayOf(0,1,2,0,2,3))
        val id = "Part" + i
        val role=(item.getValue("name").jsonPrimitive.content+" "+item.getValue("role").jsonPrimitive.content).lowercase()
        val head=listOf("head","face","hair","fringe","bang","eye","iris","brow","nose","mouth","ear").any { it in role }
        val torso=listOf("body","torso","dress","apron").any { it in role }
        val kind=item.getValue("name").jsonPrimitive.content.lowercase()
        val eyeSide=side(kind);val eye=eyeSide?.let { eyePivots[it] }
        val iris="iris" in kind
        val combined="eye_combined" in kind
        val irisRegion=eyeSide?.let { combinedRegions[it] }
        val upperLid="lid_upper" in kind || "upper_lid" in kind
        val eyePart=eye!=null && (iris || upperLid || "eye_white" in kind || "eye-white" in kind || "eye_combined" in kind)
        val mouthPart=mouthPivot!=null && ("mouth_inside" in kind || "mouth_cavity" in kind || "mouth_upper" in kind || "mouth_lower" in kind)
        val axes=mutableListOf<KeyformAxis>()
        if(head) axes.add(KeyformAxis(angle.id,floatArrayOf(-10f,0f,10f)))
        if(bodyPivot!=null) axes.add(KeyformAxis(bodyAngle.id,floatArrayOf(-5f,0f,5f)))
        if(bodyPivot!=null && torso) axes.add(KeyformAxis(breath.id,floatArrayOf(0f,1f)))
        if(eyePart) axes.add(KeyformAxis(if(eyeSide=="L") leftOpen.id else rightOpen.id,floatArrayOf(0f,1f)))
        if(eyePart && (iris || (combined && irisRegion!=null))) {axes.add(KeyformAxis(gazeX.id,floatArrayOf(-1f,0f,1f)));axes.add(KeyformAxis(gazeY.id,floatArrayOf(-1f,0f,1f)))}
        if(mouthPart) axes.add(KeyformAxis(mouthOpen.id,floatArrayOf(0f,1f)))
        if(i==hairIndex) axes.add(KeyformAxis(hairSway.id,floatArrayOf(-1f,0f,1f)))
        val forms=if(axes.isEmpty()) null else {
            val count=axes.fold(1) { n,ax -> n*ax.keys.size }
            KeyformGrid(axes,List(count) { index ->
                var n=index;val coordinate=IntArray(axes.size) { j -> (n%axes[j].keys.size).also { n/=axes[j].keys.size } }
                val values=axes.indices.associate { j -> axes[j].parameterId.raw to axes[j].keys[coordinate[j]] }
                val z=(values["ParamAngleZ"]?:0f)*PI.toFloat()/180f
                val sway=(values["ParamBodyAngleZ"]?:0f)*PI.toFloat()/180f
                val breathe=values["ParamBreath"]?:0f
                val delta=FloatArray(mesh.positions.size)
                for(k in 0 until mesh.positions.size step 2) {
                    var px=mesh.positions[k];var py=mesh.positions[k+1]
                    if(eyePart && eye!=null) {
                        if(iris) {px+=eye[3]*0.15f*(values["ParamEyeBallX"]?:0f);py-=eye[4]*0.12f*(values["ParamEyeBallY"]?:0f)}
                        if(combined && irisRegion!=null) {
                            val dx=(px-irisRegion[0])/(irisRegion[2]*.65f).coerceAtLeast(1f);val dy=(py-irisRegion[1])/(irisRegion[3]*.65f).coerceAtLeast(1f)
                            val weight=(1f-(dx*dx+dy*dy)).coerceIn(0f,1f)
                            px+=eye[3]*.08f*(values["ParamEyeBallX"]?:0f)*weight;py-=eye[4]*.08f*(values["ParamEyeBallY"]?:0f)*weight
                        }
                        val open=values[if(eyeSide=="L") "ParamEyeLOpen" else "ParamEyeROpen"]?:1f
                        if(upperLid) py+=eye[4]*0.5f*(1f-open) else py=eye[1]+(py-eye[1])*open
                    }
                    if(mouthPart && mouthPivot!=null) {
                        val opened=values["ParamMouthOpenY"]?:0f
                        if("mouth_inside" in kind || "mouth_cavity" in kind) py=mouthPivot[1]+(py-mouthPivot[1])*(0.2f+0.8f*opened)
                        else if("mouth_upper" in kind) py-=mouthPivot[4]*0.15f*opened
                        else if("mouth_lower" in kind) py+=mouthPivot[4]*0.15f*opened
                    }
                    if(i==hairIndex && hairPivot!=null) {
                        val hx=hairPivot[0];val hy=hairPivot[2]-hairPivot[4];val dx=px-hx;val dy=py-hy
                        val influence=((py-hy-hairPivot[4]*.35f)/(hairPivot[4]*.65f)).coerceIn(0f,1f)
                        val a=(values["ParamHairBack"]?:0f)*6f*influence*PI.toFloat()/180f
                        px=hx+dx*cos(a)-dy*sin(a);py=hy+dx*sin(a)+dy*cos(a)
                    }
                    if(head) {val dx=px-pivot[0];val dy=py-pivot[1];px=pivot[0]+dx*cos(z)-dy*sin(z);py=pivot[1]+dx*sin(z)+dy*cos(z)}
                    if(torso && bodyPivot!=null) {px=bodyPivot[0]+(px-bodyPivot[0])*(1f+0.01f*breathe);py=bodyPivot[2]+(py-bodyPivot[2])*(1f+0.01f*breathe)}
                    if(bodyPivot!=null) {val dx=px-bodyPivot[0];val dy=py-bodyPivot[2];px=bodyPivot[0]+dx*cos(sway)-dy*sin(sway);py=bodyPivot[2]+dx*sin(sway)+dy*cos(sway)}
                    delta[k]=px-mesh.positions[k];delta[k+1]=py-mesh.positions[k+1]
                }
                KeyformCell(coordinate,MeshDeltaForm(delta))
            })
        }
        val masks=if(iris && eyeSide!=null && eyeSide in whites) listOf(DrawableId("Part"+whites.getValue(eyeSide))) else emptyList()
        val pairedLids="lids_both" in kind && "L" in whites && "R" in whites
        val channels=if(pairedLids) {
            val la=KeyformAxis(leftOpen.id,floatArrayOf(0f,.5f,1f));val ra=KeyformAxis(rightOpen.id,floatArrayOf(0f,.5f,1f))
            val cells=mutableListOf<KeyformCell<ChannelValue>>()
            for(j in 0..2) for(k in 0..2) cells.add(KeyformCell(intArrayOf(k,j),ChannelValue.Scalar(1f-maxOf(la.keys[k],ra.keys[j]))))
            ChannelGrids(mapOf(FormChannel.OPACITY to KeyformGrid(listOf(la,ra),cells)))
        } else if(upperLid && eyePart) {
            val axis=KeyformAxis(if(eyeSide=="L") leftOpen.id else rightOpen.id,floatArrayOf(0f,.5f,1f))
            val cells:List<KeyformCell<ChannelValue>> = listOf(1f,1f,0f).mapIndexed { j,value -> KeyformCell(intArrayOf(j),ChannelValue.Scalar(value)) }
            ChannelGrids(mapOf(FormChannel.OPACITY to KeyformGrid(listOf(axis),cells)))
        } else ChannelGrids.Empty
        Drawable(DrawableId(id), item.getValue("name").jsonPrimitive.content, null, BlendMode.Normal, masks, mesh, forms, channels, drawOrder=i.toFloat(), texturePage=i)
    }
    val parameters=mutableListOf(angle)
    if(bodyPivot!=null)parameters.addAll(listOf(bodyAngle,breath))
    if("L" in whites)parameters.add(leftOpen)
    if("R" in whites)parameters.add(rightOpen)
    if(hasIris)parameters.addAll(listOf(gazeX,gazeY))
    if(mouthPivot!=null)parameters.add(mouthOpen)
    if(hairPivot!=null)parameters.add(hairSway)
    val model = PuppetModel(parameters, emptyList(), emptyList(), draws, draws.map { OrgChild.Drawable(it.id) }, null,
        canvasWidth=width, canvasHeight=height, worldOriginX=width/2, worldOriginZ=-height/2, pixelsPerUnit=1000f).withDerivedRenderRoot()
    val pages = rows.mapIndexed { i, row ->
        val path = row.jsonObject.getValue("path").jsonPrimitive.content
        Moc3Sidecars.AtlasPage("textures/part${i}.png", File(project, path).readBytes())
    }
    val bundle = Moc3Sidecars.bundle(model, "Model", version=MocVersion.V40, pages=pages)
    bundle.report.notices.forEach { println(describeExportNotice(it)) }
    check(bundle.report.notices.isEmpty()) { "Export reported notices" }
    bundle.files.forEach { f -> File(output, f.name).apply { parentFile.mkdirs(); writeBytes(f.bytes) } }
    File(output,"prototype-has-hair.txt").writeText((hairPivot!=null).toString())
    println("Experimental prototype; appearance and physics must be checked in Core")
}
