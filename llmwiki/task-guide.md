# live2d-rigger: setup and task guide

Source-reviewed 2026-11-10. Use [actual schemas](contracts.json) for argument details.

## Default workflow

The user describes the character. You generate complete separate artwork parts with the host's native image tools, rig them, build, show motion, and the user simply reports what looks wrong; you fix it with one targeted repair at a time. Early on, fetch (with the user's agreement to Live2D's licence) and study the official free sample models listed in [references](references.md) so the part split, parameter set, physics and expressions of the user's rig follow proven structure. Samples are references only.

## Choose a real production route

For a GPU-limited/offline user, use existing reviewed artwork or their editor and installed CPU-capable Cubism toolchain; native compilation still needs an actual producer. With authorized native image tools, generate complete separated parts in the main session. Remote image generation requires an explicit privacy/cost choice. Different parts need complete hidden backing, matching neutral alignment and source-specific motion domains. Do not borrow another model's camera, coefficients or anatomy.

Cubism Editor with a compatible export license is one authoring route. An existing Umamo/JDK toolchain is another only when its exact API and output contract match the requested project. Inspect the selected version's source/examples before writing Kotlin. The observed producer contract was Umamo commit bb482b162dd4c7e4b0ddf877ea4a77336cec31b1 with JDK21, using a Kotlin rig and a Gradle JavaExec entrypoint; its character-specific build scripts mutate their own sources and are not generic plugin backends. Do not run those scripts or tools/live2d/agent.sh as a producer. An SDK renderer loads compiled runtime data; it does not replace rig authoring. No SDK, editor, image model or license is bundled here.

## Worked character task

For an original waving mascot, begin with a brief and resources. Design a neutral whole figure and complete head/body/arm/eye/mouth/backing parts. Review those images directly; import RGBA layers with meaningful roles. Author deformers, draw order, parameter domains, expression defaults and physics using the chosen real API. Save executable rig source; run the trusted compiler into a fresh output directory. Compilation requires exactly one model3.json, safe present referenced resources and MOC3 bytes. Missing textures/escaped paths stop acceptance. Native editable CMO files are reported only when actually emitted; layers plus Kotlin are not a Cubism Editor document.

Render neutral, blink/mouth, turn/tilt, arm and expression transitions through actual Core. The plugin checks video metadata and full decoding; the main agent must inspect the visible motion. Retain source and per-domain observations; a successful build remains compiled_needs_core_and_motion_review and motion remains motion_review_pending. No user acceptance is fabricated.

## Diagnose and accept

Missing compiler: preserve the authored project and state the exact required compatible producer. MOC header mismatch: actual export failed, no renamed JSON placeholder. Seams/clipping: compare same source domains and complete backing before proposing one targeted repair. Ambiguous preview: get better evidence instead of regenerating. Accepted prior revisions and paused rigs stay frozen. Final acceptance requires an editable source, real compatible runtime package, visible sound deformation and reviewed motion; live tracking is a separate task.

Read the [verification record](../VERIFICATION.md) for dated tested scope. This guide does not install tools or claim new live execution.

## Artwork contract: complete parts

Make separate whole pieces: face skin including the area under the bangs, outline and blush, eyes with lids and irises, brows, nose, mouth, ears, bangs, left and right side hair, back hair, and the body, limb and accessory pieces the character has. Paint hidden roots, overlaps and backfill for the movement the rig will do. A flat portrait cut into slices is not a set of complete parts. Use one common neutral canvas size for every full-canvas part; a cropped part is imported with integer x and y placement on that canvas (live2d_model_layer enforces one canvas size and unique names). Keep transparency and landmark alignment, and use stable role names with one fixed convention for left and right (say whether it is the viewer's or the character's), for example Eye_L_Iris. Reassemble the neutral from the parts and compare it with the approved source before packing; pack only afterwards and without resampling. Part layouts, coordinates and limits belong to each character; never reuse another character's.

## Rig authoring recipe

Build the hierarchy body, then head roll, then regional X/Y warps for face, eyes, brows, nose, mouth, ears and hair; nest gaze and local blink and mouth controls under their regional parent. Keep skull, cheek, jaw, nose and attached pieces on one coherent surface. Author both X and Y for each regional control and look at intermediates, diagonals and combinations, not only endpoints. Clip the iris and highlight to the eye white; check nine gaze directions at open, half and closed. Shape lips and mouth cavity across close, open and form. Use the standard IDs ParamAngleX, ParamAngleY, ParamAngleZ, ParamEyeLOpen, ParamEyeROpen, ParamEyeBallX, ParamEyeBallY, ParamMouthOpenY and ParamMouthForm, and record each range and default. Conventions to record rather than assume: positive X is right, positive Y is up, eye open 0 is closed and 1 is normal, mouth open 0 is closed and 1 is normal. Adapt ranges and anatomy to the model. Add hair sway under head motion. Author physics, expressions and blink/lip-sync groups as real sidecar files where the toolchain supports it; a group needs a runtime input and is not automatic motion. The plugin does not generate a rig for you: the active host writes it against the selected toolchain's API, then live2d_model_rig saves the source.

## Authoring and build route (adaptive)

Detect, do not assume. Ask the user which route they have, then confirm what is actually installed before proposing anything: Cubism Editor with an export licence, or a JVM/Kotlin toolchain such as Umamo. For the Umamo route check, on the user's machine: the Java version (the observed working setup used JDK 21 with JVM target 21), the Umamo checkout and its commit (observed: bb482b162dd4c7e4b0ddf877ea4a77336cec31b1), the Kotlin compiler and runtime classpaths, and that the API your rig source uses exists at that version. The inputs are your rig source plus the imported parts and a config; the outputs to require are model3.json, MOC3 and textures, and optionally a native editable CMO3. Make the render root explicit and keep parent-space keyform mapping correct at that pin; read the exporter's notices and reopen the output. Run it through live2d_build_model with a command using {project} and {output}. Work on a copy of any build script that must be edited. Ask before installing anything; never install silently. Report missing pieces precisely and preserve the layers and rig source. The plugin supplies no adapter for these toolchains; the detection and command are chosen by the host with the user.

## Motion review with the real Core

The plugin's own checks are structural: live2d_inspect_resources, live2d_check_motion, and a decoded-video check in live2d_render_model_motion. They do not evaluate the model. Before calling a rig ready: find the installed Core or SDK and a renderer that can load the model; check MOC consistency; evaluate parameters across each axis and look for non-finite geometry; then render a slow labelled video of neutral, yaw, nod, roll, gaze, blink, mouth and each expression at extremes, intermediates and combinations, with holds at the endpoints and a readback of the parameter values used. Record the model hash next to the video. Decode the video and look at it in the main session. If no Core or renderer is installed, say so, keep the build, and do not claim a reviewed rig. Numerical passes and still frames do not prove pleasant continuous motion.

## User-reported issues

When the user reports a problem: record the complaint, the model and art hashes, the pose, and what should be visible. Reproduce it in the target runtime. Isolate the owning part or motion by comparing a matched baseline and candidate, including intermediate frames. Change one coherent unit, keep a rollback and accepted geometry, rerun the relevant checks and compare the whole head in motion. If the evidence is ambiguous, get better evidence rather than regenerating. If one corrective generation fails to fix the same defect, stop that method until there is new evidence or a materially different method. Report visual acceptance and the user's acceptance separately.

## Common failures

Drawable vanishes though export was valid: inspect render root, draw order and the parameter-axis domain. Hair seams: check complete roots, backing and ownership before touching motion. Blink or gaze fragments: look at eye mask, lids and iris registration at half blink. Holes at jaw or neck: compare source ownership and shared deformation, not just bounds. Outline drifts off keys: check matching topology and the actually interpolated poses.

## Delivery

Deliver generated-part provenance and any licensed references, layered art with placement, the rig and build recipe, the native editable project if one really exists, the complete runtime package with sidecars, control IDs with ranges and defaults, the hash-linked verification and review video, and the outstanding issues. State what the user can edit and what is missing. Keep third-party licence files with anything derived from samples, and do not assume that permission to study is permission to redistribute.

## Working on a character that already exists

Use live2d_open_model with the path of the user's .model3.json: the whole model folder is copied into a project and the original is never changed. live2d_inspect_model then reports the controls, expressions, motion groups and physics groups (which control drives which loose part and how strongly), and, when the Cubism renderer is ready, the separate parts and drawable pieces with each control's range. live2d_render_clip renders one fixed motion (head turns left and right, blinks, small body sway; the same every time) through the official Cubism Core with physics running, so a clip before a change and a clip after it can be compared frame for frame.

The renderer is the user's own: a Cubism SDK viewer folder (LIVE2D_SDK_VIEWER or viewer_dir; it must expose window.rig as described at the top of corebridge.py), a Python with Playwright (LIVE2D_RENDER_PYTHON), any Chromium Playwright can launch, and ffmpeg. Cubism Core and the SDK are Live2D's proprietary software and are not bundled.

Fixing loose-part motion: live2d_adjust_physics multiplies the saved original physics values, so repeating a call does not compound. Raise output_scale for a wider swing, input_weight to react to smaller head turns, follow_through for swing that carries on after the head stops. A swing can never exceed the range the artist authored for that control in the model itself (for example hair controls limited to -1..1): once the control saturates, a larger multiplier changes nothing, and a bigger sweep needs new shapes in the rig. Judge the result by looking at before and after frames at the same moments of the same motion, not from numbers.

Writing a motion: live2d_write_motion takes plain track descriptions (sine: center, amplitude, whole cycles per loop; blink: times; keys: eased [seconds, value] pairs), refuses parameter ids the model does not have, limits values to each control\u2019s real range and says so, runs the structural motion check, and registers the result as the model\u2019s Idle motion in the working copy (the original model3.json is backed up inside the project). Sine tracks use whole cycles so the loop is seamless. It is a motion for the model to play; the structural check does not prove it looks good: render it and look.
