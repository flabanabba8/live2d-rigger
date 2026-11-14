# Live2D Rigger

![Live2D Rigger: describe a character and Hermes creates and rigs her](assets/thumbnail.jpg)

Describe a character and Hermes makes her as a Live2D model: it draws her as separate complete parts, cuts them out, lays them out on one canvas, rigs them, compiles a MOC3 with your own toolchain, and shows you a clip of her moving. You say what looks wrong; Hermes fixes that one thing and renders the same motion again so you can compare. It also opens a model you already have and works on a copy.

**Status: the built-in rig is experimental.** Read [what you get today](#what-you-get-today) before planning a finished VTuber model around it.

## Install

```
hermes plugins install flabanabba8/live2d-rigger
hermes plugins enable live2d-rigger
```

Needs Hermes 0.22 or newer on Linux (the tested platform), Pillow and NumPy. To build a model you also need your own JDK 21+ and [Umamo](https://github.com/umamoorg/umamo); to see her move you need your own Cubism SDK web viewer folder, a Python with Playwright, and ffmpeg. The plugin installs none of these and bundles no Cubism Core, SDK, viewer or sample model. You accept Live2D's licence yourself.

## Creating a character

Ask in plain words, for example: "Make me a Live2D character: a fox girl with short silver hair and a red scarf, for streaming."

1. **Scan and ask (`live2d_setup`).** The plugin looks at this computer (Java, Umamo, image tools, GPU, which image-service keys exist as yes or no) and lists your options with prices, licences and limits:
   - where the art comes from: a hosted image service, a local image model that fits your GPU, or art you already have;
   - which cutout tool removes backgrounds;
   - which rigging toolchain to use: Umamo (free, GPL-3.0, alpha), Live2D Cubism Editor FREE or PRO, Inochi2D or nijigenerate.

   **The plugin never picks for you.** It asks what the character is for, whether online services are OK, your budget and what you already own, and refuses combinations the sources rule out (for example Cubism FREE for commercial use above 10 million yen of annual sales, or a rig that exceeds FREE's limits of 1 texture, 100 ArtMeshes, 30 parts and 50 deformers). Nothing is installed, downloaded or generated without your yes. Facts older than 30 days are flagged as stale, and Hermes researches current ones online only if you agree.
2. **Brief (`live2d_begin_model`).** Saves the character description, the intended expressions and motion, and the choices from step 1.
3. **Artwork as complete parts (`live2d_model_layer`).** Each part (face, front hair, back hair, eye whites, irises, mouth, torso and so on) is generated on its own with Hermes's image tools, as an edit of one approved full-figure reference so every part keeps its place on the same canvas, and painted complete, including what the neutral pose hides. A flat portrait sliced into pieces is not accepted. Parts drawn on a flat key colour are cut out, and you get a before and after preview with the removed areas tinted to review.
4. **Layout (`live2d_arrange_layers`, `live2d_place_layer`, `live2d_set_canvas`, `live2d_default_layout`, `live2d_remove_layer`).** Order the parts back to front and move or scale one without redrawing it.
5. **Rig (`live2d_model_rig`, `live2d_check_rig_domains`).** `source="prototype-roll"` applies the built-in experimental rig; without a source you get a static layered model with no controls.
6. **Build (`live2d_configure_umamo`, `live2d_build_model`).** Compiles a MOC3 package through your Umamo and JDK. For another toolchain, set your own trusted `authoring_command` in the plugin settings.
7. **Watch her move (`live2d_render_model_motion`).** Renders a clip and a contact sheet through the official Cubism Core in your own viewer folder.
8. **Tell Hermes what is wrong.** "Her hair comes off her head when she tilts", "the scarf is too big". Hermes makes one targeted fix, keeps the earlier build (`live2d_rebuild_prototype`, `live2d_clone_model`) and renders the same motion so the two compare frame for frame. `live2d_model_status` shows where a project stands.

The full recipe, the part contract and the review rules are in the [task guide](llmwiki/task-guide.md), the [skill](skills/live2d-rigger/SKILL.md) and the [creation routes](llmwiki/creation-routes.md) (every option with its source link and the date it was read).

### What you get today

The built-in rig supplies head roll, basic body sway, breathing, a simple blink, approximate gaze, mouth opening and one back-hair physics group, when the matching parts exist. It does **not** supply left-right or up-down head turns, independent arms or legs, polished eyes, mouth shapes, or a native editable Cubism Editor document. Separately generated parts can drift out of alignment, so every part and every clip needs your eyes. A successful build is not proof that she looks right.

What was actually run is listed in [VERIFICATION.md](VERIFICATION.md): a model built from layers with the real Umamo 0.5.0 release and rendered with the official Cubism Core. Image generation through the listed services, the Cubism Editor routes and a polished finished character have not been tested.

## A character you already have

Give Hermes the folder of a `.model3.json`. The original is never changed.

- `live2d_open_model` copies her into a project.
- `live2d_inspect_model` explains how she is put together: parts, controls and their ranges, expressions, motions, and what makes her hair or skirt swing.
- `live2d_adjust_physics` changes how loose parts swing.
- `live2d_write_motion` writes a new idle motion from plain curve descriptions (breathing, sway, head turns, blinks) on her real parameters.
- `live2d_render_clip` renders a labelled clip through the Cubism Core, so before and after compare frame for frame.

## Reference samples

`live2d_reference_samples` lists five official free Live2D samples (Hiyori, Haru, Mark, Mao, Ren) and summarises one that is present. `live2d_fetch_reference_sample` downloads one from Live2D's own sample-data host, only after you accept Live2D's terms. They are structure references only; sample artwork must never be copied into your model. See [references](llmwiki/references.md).

## File checks

`live2d_inspect_resources` reads a `model3.json` and reports missing, invalid or unsafe paths (model, textures, physics, pose, expressions, motions, sounds). `live2d_check_motion` checks a motion file's structure and compares its targets with a display-info file. Both only read files; they do not load or render the model, so a clean report is not proof of a usable rig.

## Settings

Set by you in the plugin settings; the model cannot change them.

| Setting | What it is |
|---|---|
| `java` | Your Java (JDK 21+) executable, for Umamo |
| `umamo_classpath_file` | A JSON file with `compiler` and `runtime` arrays of your installed Umamo and Kotlin library paths |
| `viewer_dir` | Your Cubism SDK web viewer folder (`index.html`, `viewer.js`, `core.min.js`, `framework/Shaders`) |
| `render_python` | A Python that has Playwright, used for rendering |
| `authoring_command` | Optional: your own trusted build command, with `{project}` and `{output}` |
| `motion_command` | Optional: your own trusted motion renderer |

## Licence and disclosure

GPL-3.0-or-later. Umamo is a separate GPL-3.0 project. The thumbnail contains character artwork; no character model, layers or textures are bundled. If you pick a hosted image service, your prompts and reference images are sent to that service. This plugin was made with AI assistance.
