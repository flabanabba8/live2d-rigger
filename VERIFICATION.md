# Verification

- Mixed-case protected-directory fixtures passed on Linux and native Windows; no real credentials were used. This is not a full platform or publication audit.

- Native Windows Python 3.14 checked the references in a synthetic model file with dummy resources. No user rig was accessed.
- Earlier Linux fixture tests checked model references and motion/display-ID structure. No real rig was loaded, rendered or exercised.
- Static checks cannot establish visual quality or MOC contents. Real rig validation, a reviewed demo and a complete publication audit remain open.

- 2026-11-07: tools renamed `live2d_inspect_resources` and `live2d_check_motion` so the Live2D association is explicit. Read-only copies of five official Live2D reference samples (Haru, Mao, Mark, Natori, Ren) and two user-made rigs were checked: 175 resources all present, 55 motion files with no problems. A copy of Haru with its texture folder and physics file deleted reported 3 missing resources. This is static resource checking only: no MOC3 parsing, rendering or parameter testing. Sample redistribution terms are unchanged; nothing was bundled.

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
