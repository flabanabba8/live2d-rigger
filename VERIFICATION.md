# Verification

- Mixed-case protected-directory fixtures passed on Linux and native Windows; no real credentials were used. This is not a full platform or publication audit.

- Native Windows Python 3.14 checked the references in a synthetic model file with dummy resources. No user rig was accessed.
- Earlier Linux fixture tests checked model references and motion/display-ID structure. No real rig was loaded, rendered or exercised.
- Static checks cannot establish visual quality or MOC contents. Real rig validation, a reviewed demo and a complete publication audit remain open.

- 2026-11-07: tools renamed `live2d_inspect_resources` and `live2d_check_motion` so the Live2D association is explicit. Read-only copies of five official Live2D reference samples (Haru, Mao, Mark, Natori, Ren) and two user-made rigs were checked: 175 resources all present, 55 motion files with no problems. A copy of Haru with its texture folder and physics file deleted reported 3 missing resources. This is static resource checking only: no MOC3 parsing, rendering or parameter testing. Sample redistribution terms are unchanged; nothing was bundled.

## 0.6.1 - maintainer review (2026-11-12)

Maintainer review. Java, Umamo classpaths, render python/viewer, authoring command and motion command are owner settings, not tool arguments; model creation and build tools ask the user first; no key or credential scanning; every subprocess gets a minimal environment. Re-tested: 77 offline tests (1 skipped: needs a real Java toolchain), all passing; plugin preflight reports no findings.

Live test through Hermes 0.23.0 (2026-11-12, own profile) on a real rigged model (CoralSquid): open as a working copy, inspect, physics change, write and check a motion. Found and fixed: write_motion failed whenever the plugin data folder was under .hermes (every normal install). Not covered: the Cubism Core renderer and the Umamo build (no Cubism SDK viewer or Umamo classpath on the test machine); they report plainly that they are not ready.

## 2026-11-10 maintained scope revision

Eight offline tests pass, including actual RGBA layer import/rig-source persistence and rejection of unsafe/missing compiled resources and a fake MP4. Native authoring and full character generation have not been live-tested through the new bridge. A previously accepted user-owned motion is a separate existing-model demonstration, not a newly built plugin output. Hermes admission and retirement preflight pass; detailed local receipts are retained in the contest maintenance evidence. Old evidence above keeps its original scope.

## 2026-11-10 reference samples (version 0.3.0)

- Verified from Live2D's own pages on 2026-11-10 (fetched raw with curl and cross-read): the sample list page, the Hiyori and Haru pages (download button, data-model-id), cubism.live2d.com/sample-data/js/download.js (archive locations), the Free Material License Agreement (version 1.6, revised 3 February 2025: sections 4.1.1 no redistribution, 4.1.2 no modification, no general study permission in English text) and the Sample Data Terms of Use (per-character terms). Details in llmwiki/references.md.
- Implemented: references.py with two tools, an official-host-only download gated on an explicit licence flag, safe extraction, reuse of present samples and a JSON-only structure summary. Three offline tests with a fake downloader pass (gate, reuse, summary, unsafe archive, no-model archive, host allowlist). 
- Not live-tested: no real sample was downloaded in this change, by design. A live download, and a real Hermes run that uses a sample as reference while rigging, remain open. Draw order and deformer hierarchy are not read.

- 2026-11-10 (0.3.0) gap-analysis P1: complete-part contract, rig recipe, adaptive build route and real-Core motion review are guidance text only and untested live. live2d_model_layer now rejects duplicate names and mixed canvas sizes (unless x/y placement is given); covered by an offline test. No adapter, Core evaluator or renderer was added. Issue loop and failure signatures (P2) added as text.

## 2026-11-11 existing models, motion writing, Core renderer (version 0.4.0)

- New tools: live2d_open_model (working copy of an existing model; original never changed), live2d_inspect_model, live2d_adjust_physics, live2d_write_motion, live2d_render_clip; shipped corebridge.py (Core render and inspect through the user's own SDK viewer, Playwright and ffmpeg; Cubism Core and the SDK are not bundled).
- Offline tests (tests/test_existing_model.py, 11): copy and original-hash safety, refusal of links and missing resources, plain-words inspection, non-compounding physics change and restore, motion validation/clamping/registration/loop, motion name resolution, render argument contract, deterministic standard pose.
- Live on this machine (not in the offline tests): Core inspect (63 drawables, 37 parameters with ranges) and 8 s clips rendered through the official Cubism Core and framework with physics running, on a copy of the accepted user-owned model; the MOC hash seen by the viewer is checked against the requested file. Visual quality of any motion is a human judgement; the structural motion check does not establish it.
- Limits: loose-part swing cannot exceed the range the artist authored in the model; no MOC rebuild, no deformer or keyform editing, no VTube Studio, camera or tracking.


## 2026-11-11 experimental creation route (0.5.0)

A real Hermes session generated a reference and separately reviewed parts, used flat-key cutout and placement tools, compiled a new user-owned MOC3 with an installed Umamo/JDK toolchain, and rendered it through the user's Cubism Core viewer. The final demonstration used a combined body, combined eyes, separate upper lids and a simple mouth. Its eight-second motion exercised head roll, body sway, breathing, blink, approximate eye look, mouth opening and back-hair physics. A plain-words eyelash issue was followed by a prototype rebuild and a same-view before/after render. This is a provisional rig, not a polished or human-approved model: XY head turns, independent limbs, independently painted irises and a native editable Cubism document are absent. The rejected arm-split experiment and image-generation/registration failures are not evidence of completed features.

Synthetic tests cover key-colour cutout and ambiguity rejection, placement and ordering, registration including absent and scaled shapes, project copy/removal, native export and error handling. The real Umamo integration test is opt-in and needs a configured local toolchain. Core endpoint/diagonal checks and direct frame reviews were performed locally; they do not prove visual quality in every pose or any physical camera, tracking or external application workflow. No generated model layers, textures, third-party model or Cubism runtime files are bundled; the approved promotional thumbnail contains character artwork.

## 2026-11-11 parameter-report correction (0.5.1)

A real Core render of a prototype without placed eyelids produced three eye-close parameter crossings but no visible blinks. Reports now name those crossings explicitly, describe all ranges as evaluated parameter values, and require visual inspection before claiming movement; the skill carries the same distinction. The compatibility field `measured_movement` remains, but its former `blinks` key is now `eye_close_parameter_crossings`.

## 0.6.0 - scan, ask, never pick (2026-11-12)

- New `live2d_setup`: scans this computer (JDK, Umamo and image tools on PATH, GPU, which image-service keys exist as yes/no), lists the image routes (hosted services with price, free tier, transparent-background and reference-edit support; local models that fit the GPU, with memory figures only where a primary page states one), cutout tools with licences, and rigging toolchains with their limits (Cubism FREE caps, Umamo alpha, Inochi2D / nijigenerate), asks the user, and saves the image route, cutout tool and rigging toolchain the user picked. The plugin never picks. `live2d_begin_model` and `live2d_build_model` return the interview until it is answered. A consistency check refuses combinations the sources rule out (an online image service after "nothing online", Cubism FREE for commercial use above 10 million yen of annual sales).
- New wiki `llmwiki/creation-routes.md` and `live2d_catalog.json` from vendor pages, model cards, READMEs and Live2D's own pages read on 2026-11-12; Cubism PRO price, most alpha-output claims, vendor terms on character art and most local memory needs are marked UNVERIFIED. Knowledge freshness: stale after 30 days or a passed deadline; online research only if the user says yes; approved research stored as dated overrides.
- Tested here: 66 Python tests (existing 49 unchanged). Not tested: any image generation, any rig built through the new routes, the Cubism Editor, Umamo installs.


## 0.6.2 - found by running every tool through Hermes (2026-11-12)

- Built a model from layers with the real Umamo v0.5.0 release jar (sha256 ede3959940dc37696eef2092208a4424c75f5533811b3ff0423c5b7a7bfbae63, linux-x64) and a Kotlin 2.4.20 compiler from a Gradle cache: set canvas, add/remove/place/register layers, rig (prototype-roll and static-layers), build, inspect, physics change, write and check a motion, rebuild, clone, domain check, and a Core-rendered clip with the official Cubism Core and a viewer folder.
- Bugs this found and fixed: the Kotlin sources were written for Umamo 0.4.0 and did not compile against the 0.5.0 release (`DrawableMesh` takes a separate local position array; `Moc3Sidecars.bundle` no longer takes `canvasToParentSpace`), now written for 0.5.0; the plugin's own post-build resource check refused its own output because the data folder sits under `.hermes` (same class as the earlier write_motion bug); `corebridge.py` defined `_clean_env` after its `main()` call, so every Core render died with a NameError after the frames were drawn; `live2d_render_clip` on a project with no model reported a bare KeyError.
- Tested here: 79 Python tests (1 skipped). Not tested: Umamo 0.4.0 (the sources no longer compile against it), the Cubism Editor, any image generation, `live2d_fetch_reference_sample` with the licence accepted (the user must accept Live2D's terms, so a test must not).
- The viewer folder is the user's own (index.html, viewer.js, core.min.js and framework/Shaders); the one used here was assembled from earlier local Cubism SDK for Web files.

## 0.6.3 - README rewritten around creation (2026-11-13)

- Documentation only: the README now leads with creating a character (scan and ask, brief, complete parts, layout, rig, build, motion review, reported fixes), states what the experimental rig does and does not supply, and lists the owner settings from the manifest in place of environment variables. No code changed.
- Checked: every tool named in the README is declared in `plugin.yaml`; the Python tests and `hermes plugins validate` pass. Not checked: whether the older environment variables still work (the README no longer mentions them).
