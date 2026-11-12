# Live2D Rigger

![Live2D Rigger: describe a character and Hermes creates and rigs her](assets/thumbnail.jpg)

Create and rig a Live2D character from a description with Hermes and your own authoring tools. Hermes can generate complete parts as same-canvas reference edits, remove a flat key-colour background, arrange and position the layers, compile a MOC3 with your installed Umamo/JDK toolchain, and render a motion preview through your own Cubism Core viewer. You can describe a visible issue and compare a rebuilt or adjusted result with the earlier clip.

The built-in rig is **experimental**: it supplies head roll, basic body sway and breathing, simple blink, approximate gaze, mouth opening and a roll-driven back-hair physics group when matching parts are present. It does not supply XY head turns, independent limb motion, polished eyes or a native editable Cubism document. Independently generated parts may drift; reference matching is confidence-gated and still requires visual review. A successful export is not visual acceptance.

**Setup:** `hermes plugins install flabanabba8/live2d-rigger`, then `hermes plugins enable live2d-rigger`. Use Hermes 0.22+, Pillow and NumPy, your own installed compatible Umamo and JDK 21 (configured by settings or environment), and, for motion review, your own Cubism SDK viewer, Playwright Python and ffmpeg. The plugin bundles no Cubism Core, SDK, viewer, sample model or character model layers or textures; its approved promotional thumbnail contains character artwork. It does not install an authoring toolchain or accept Live2D's licence for you.

Existing models are opened as copies for inspection, physics changes, motion writing and before/after rendering. Official free samples are optional structural references and are downloaded only after you accept their terms. Linux is the platform tested. Umamo is a separate project licensed GPL-3.0; see [Umamo](https://github.com/umamoorg/umamo). This plugin is GPL-3.0-or-later and was made with AI assistance; see [VERIFICATION.md](VERIFICATION.md) for the tested limits.

Read the [task guide](llmwiki/task-guide.md) and [skill](skills/live2d-rigger/SKILL.md) for resource configuration, part contracts and review.

## Characters you already have (0.4.0)

`live2d_open_model` copies an existing model (a `.model3.json` folder) into a project so the original is never touched. `live2d_inspect_model` explains how she is put together (controls, expressions, motions, physics, and with the renderer ready the separate parts and each control range). `live2d_adjust_physics` changes how hair or skirt swing, `live2d_write_motion` writes a new idle motion from plain curve descriptions, and `live2d_render_clip` renders a labelled clip through the official Cubism Core so before and after compare frame for frame. Rendering uses your own Cubism SDK viewer folder (`LIVE2D_SDK_VIEWER`), a Python with Playwright (`LIVE2D_RENDER_PYTHON`) and ffmpeg; Cubism Core is not bundled.

## Reference samples

`live2d_reference_samples` lists five official free Live2D sample models (Hiyori, Haru, Mark-kun, Mao, Ren) and summarises a present sample's parameters, parts, physics, expressions and motion groups. `live2d_fetch_reference_sample` downloads one from Live2D's own sample-data host into this plugin's data folder, only when told the user agreed to Live2D's licence. They are structural references only; no sample is bundled, and sample artwork must never be copied into a user's model. See [references](llmwiki/references.md).

## Supporting tools and detailed limits

Inspect common resource references in a Cubism `model3.json` file, reporting missing, invalid or unsafe model, texture, physics, pose, userdata, display-info, expression, motion and motion-sound paths. A second tool checks motion segment structure and compares motion targets to IDs in a supplied display-info file. The source files are read only; model, display-info and motion JSON reads reject a file changed or atomically replaced during the bounded read. [Live2D's SDK documentation](https://docs.live2d.com/en/cubism-sdk-tutorials/model-add-to-sample-project/) describes the model settings format.

The diagnostic inspectors are static analysis. They do not parse the MOC3 binary, validate texture contents, load or render a model, exercise parameters, detect clipping/deformation, or inspect every Cubism extension. Production uses the explicitly selected native authoring and rendering tools described in the guide. A present file is not proof of a usable rig. Test in the intended Cubism runtime and visually review the animation. The experimental route has been exercised with synthetic artwork and a provisional animated character; it is not a polished or fully featured rig.

Motion checks follow Live2D's [motion format](https://github.com/Live2D/CubismSpecs/blob/master/FileFormats/motion3.json.md) and [display-info format](https://github.com/Live2D/CubismSpecs/blob/master/FileFormats/cdi3.json.md). A missing display-info ID is a warning, not proof that the MOC lacks it. Seven synthetic tests pass; no real motion package or rendered rig has been checked.

## Optional Umamo static layer export

The adapter also offers an **early static export**: it makes a MOC3 package from independently painted, positioned layers, with no controls, deformations or physics. The visible result still needs Core and visual review; this route does not create a Cubism Editor document. Call `live2d_model_rig` without source, then `live2d_build_model` without a command. Arrange layers with `live2d_arrange_layers` in back-to-front order and include a full-canvas layer to define the canvas.

Provide your own installed JDK 21 via `LIVE2D_JAVA` or `JAVA_HOME`, plus the installed Kotlin compiler classpath in `LIVE2D_UMAMO_COMPILER_CLASSPATH` and Umamo runtime classpath in `LIVE2D_UMAMO_RUNTIME_CLASSPATH` (platform path separator between entries). No libraries or proprietary Live2D software are bundled. This uses the separately installed [Umamo](https://github.com/umamoorg/umamo), licensed GPL-3.0; its API and dependencies must be compatible.

Use `live2d_configure_umamo` to check the Java and Umamo classpaths you set in the plugin settings (`java`, `umamo_classpath_file`, a JSON file with `compiler` and `runtime` arrays of installed classpath entries) for one private project. The model cannot supply paths. `live2d_place_layer` sets the canvas position and uniform scale without resampling source pixels. Placement and order changes require a new build and an inspected preview.

An optional experimental `source="prototype-roll"` mode adds a head-roll parameter derived from the imported face bounds basic body sway and breathing when a torso is present, and provisional blink/gaze and mouth opening for consistently named eye-white, iris and mouth-cavity layers; it is a rough prototype, not the requested complete rig. A simple experimental back-hair physics group is generated when hair is present. XY turns, mouth-form controls and a native editable document are not provided. Inspect the Core output before drawing conclusions about the result.
