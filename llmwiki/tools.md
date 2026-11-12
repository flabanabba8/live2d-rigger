# Actual tool contracts

Registered source schemas; registration alone does not establish live backend readiness.

## live2d_setup

First-use interview and environment scan. Without answers: returns what this computer has (JDK, Umamo and image tools on PATH, GPU, which image-service keys exist as yes/no), suggestions for image generation (hosted services with price, free tier, transparent-background and reference-edit support; local models that fit the GPU), cutout tools with licences, and rigging toolchains with their limits (Cubism FREE caps, Umamo alpha status, Inochi2D/nijigenerate), whether the built-in knowledge looks out of date (offering online research only if the user says yes), and the questions to ask. With answers: saves them, including the image, cutout and rigging routes the user picked. The plugin never picks for the user. Generates nothing, installs nothing, sends nothing. live2d_begin_model and live2d_build_model return the interview until it is answered.

Inputs: `answers` (optional), `knowledge_updates` (optional).

## live2d_begin_model

Begin creating a complete editable Live2D character from a brief and the user’s actual resources. Artwork, rigging, native compilation and motion review are production stages; inspectors remain diagnostics.

Inputs: `name` (required), `brief` (required), `resources` (optional).

## New-character authoring tools

The exact schemas for `live2d_clone_model`, `live2d_remove_layer`, `live2d_model_layer`, `live2d_set_canvas`, `live2d_arrange_layers`, `live2d_place_layer`, `live2d_default_layout`, `live2d_register_layer`, `live2d_configure_umamo`, `live2d_model_rig`, `live2d_build_model`, `live2d_rebuild_prototype` and `live2d_check_rig_domains` are in [contracts.json](contracts.json). Imports require a reviewed complete-part attestation. The built-in adapter is experimental; its available controls and omissions are described in the [task guide](task-guide.md).

## live2d_render_model_motion

Render the built model with the motion renderer command the owner set in the plugin settings (motion_command) into a real motion MP4 for MAIN-session review; live2d_render_clip uses the built-in Core renderer instead. The model cannot choose a command. No physical camera/tracker/VTS integration is part of this operation.

Inputs: `model_id` (required), `timeout_seconds` (optional).

## live2d_model_status

Read actual model production layers/rig/compiled package/motion state, never a fabricated ready flag.

Inputs: `model_id` (required).

## live2d_open_model

Open an EXISTING compiled runtime model only (not an editable layer project; use live2d_clone_model to copy a plugin-owned layer project). Open an EXISTING Live2D model (the .model3.json the user already has, or the folder that holds it; give a full absolute path) as a working copy inside a new project, so it can be inspected, changed and rendered. The original files are never modified. Use this when the user already has a character; use live2d_begin_model to create a new one.

Inputs: `name` (required), `model_path` (required).

## live2d_inspect_model

Describe an opened model in plain terms: controls, expressions, motions, physics groups (what drives what, how strongly) and, when the Cubism renderer is available, the separate parts and drawable pieces and each control range.

Inputs: `model_id` (required).

## live2d_adjust_physics

Change how loose parts (hair, tentacles, skirt) swing in an opened copy or built project: multipliers for output strength, how strongly head/body motion drives them, and follow-through (swing that continues after the head stops). Applied to the saved original each time, not compounded. restore_original undoes it.

Inputs: `model_id` (required), `output_scale` (optional), `input_weight` (optional), `follow_through` (optional), `groups` (optional), `note` (optional), `restore_original` (optional).

## live2d_write_motion

Write a new motion (for example an idle that makes her breathe, sway, look around and blink) into an opened copy or built project from plain curve descriptions, validated against the model’s real parameter ids and ranges, and register it as the Idle motion. tracks: list of {parameter, wave:sine (center, amplitude, cycles = whole number per loop, optional phase 0-1) | blink (at: [seconds], optional closed_seconds, open_value, closed_value) | keys ([[seconds, value], ...] eased)}. The structural check runs automatically.

Inputs: `model_id` (required), `name` (required), `tracks` (required), `seconds` (optional), `fps` (optional), `as_idle` (optional), `note` (optional).

## live2d_render_clip

Render the opened or built model moving through the official Cubism Core (physics running) into a labelled motion clip. motion: a motion name from the model or one you wrote; left out it plays the model’s own Idle motion (how she moves now), or standard if it has none; standard = test sequence (head turns left and right, blinks, small body sway); rest = no motion. Same camera and length every time so before/after clips compare directly. Look at the contact sheet in the main session.

Inputs: `model_id` (required), `label` (required), `motion` (optional), `seconds` (optional), `view` (optional), `width` (optional), `height` (optional).

## live2d_inspect_resources

Inspect model3.json references for missing or unsafe model, texture, physics, expression and motion resources. This does not inspect or render the rig.

Inputs: `model_path` (required).

## live2d_check_motion

Check Cubism motion curve structure and compare targets with supplementary display-info IDs without rendering.

Inputs: `cdi_path` (required), `motion_path` (required).

## live2d_reference_samples

List the official free Live2D sample models this plugin knows (Hiyori, Haru, Mark, Mao, Ren) with their official pages, whether each is already in the plugin's data folder, and the licence links. With sample_id, summarise that present sample's structure (parameters, parts, physics, expressions, motions) as a reference.

Inputs: `sample_id` (optional).

## live2d_fetch_reference_sample

Download one official free Live2D sample from Live2D's own sample-data host into this plugin's data folder, only as a structural reference. Requires accept_licence=true, which means you showed the user what is being downloaded and the licence links and the user agreed. Reuses a present sample.

Inputs: `sample_id` (required), `accept_licence` (required).
