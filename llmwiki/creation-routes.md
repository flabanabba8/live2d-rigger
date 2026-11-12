---
status: SOURCE-DERIVED (vendor pages, model cards, READMEs and Live2D's own pages read on 2026-11-12; nothing here was generated or run by us)
curated: 2026-11-12
---
# Creating and rigging a character: image routes, cutout tools and rigging toolchains

Read this before recommending a route. It is what `live2d_setup` draws its suggestions from (`live2d_catalog.json`, the same data). **The plugin never picks for the user:** it
scans, lists the options with their limits and licences, asks, and uses only what the user chose (an image route, a cutout tool and a rigging toolchain).

Prices, licences and limits change often; every row carries its source link and the date it was read (2026-11-12). Re-open the link before quoting. UNVERIFIED means no primary page confirmed it.

## 1. Making the art: hosted image services (the image is sent to the service)

| Service | Models | Price | Free tier | Transparent background | Reference-image edit | Source |
|---|---|---|---|---|---|---|
| OpenAI image models | gpt-image-2.6-sunburst; gpt-image-2.6-flare (the guide also names 2.5 versions) | Token priced: image input $8.00 and output $30.00 per 1M tokens; no per-image figure on the page | No free credits on the pricing page; API credits are separate from the ChatGPT subscription; eligible subscriptions "may offer promotional credits" (the benefit article itself was UNVERIFIED) | UNVERIFIED (only a summary claimed it) | Yes: edits take reference images, a markup layer or a mask with alpha | https://developers.openai.com/api/docs/guides/image-generation |
| Google Gemini image models (Nano Banana family) | gemini-3.1-flash-image; gemini-3.1-flash-lite-image; gemini-3-pro-image; gemini-nano-banana-2.1 | gemini-3.1-flash-image $0.045 (0.5K) to $0.151 (4K) per image; flash-lite $0.0336 per 1K image; 3-pro-image $0.134 per 1K/2K image | Free tier "Not available" for the models where the page shows it; others UNVERIFIED | UNVERIFIED | Described as conversational editing with multi-turn character consistency; parameters UNVERIFIED | https://aistudio.google.com/docs/pricing |
| Black Forest Labs FLUX API | FLUX 3 Image; FLUX 3 Image Klein; FLUX.2 [klein] 4B/9B, [flex], [pro], [max] | FLUX 3 Image $0.041 (768) to $0.607 (4K); Klein $0.008 to $0.036 | Pay as you go; free credits UNVERIFIED | UNVERIFIED | UNVERIFIED | https://bfl.ai/pricing |
| Stability AI API | Stable Image Ultra; SD 3.5 Large/Medium/Flash; Remove Background; Inpaint | 1 credit = $0.01: Ultra 8 credits, SD 3.5 Large 6.5, Remove Background 5, Inpaint 5 | 25 free credits (card requirement not stated) | Remove Background product exists; native alpha output UNVERIFIED | Inpaint (mask or alpha), Structure, Sketch, Style Guide, Style Transfer products | https://docs.stability.ai/pricing |
| Ideogram API | Ideogram 4.0 and 3.0 (including transparent-image endpoints) | 1 cent per credit; API per-image price UNVERIFIED | Prepaid only: $10/$20/$50/$100 or $1-$300; no free tier | Yes: transparent-image endpoints for 4.0 and 3.0 exist (the "(Transparent Background) (legacy)" variants are legacy) | not read | https://developer.ideogram.ai/ideogram-api/api-setup |
| Recraft API | V4.1 Flash; V4.1; V4; V3; V2 | V4.1 Flash $0.007; V4.1 $0.035; V4/V3 $0.04; remove background $0.01; vectorize $0.01 | No free API tier stated; the web Free plan images are owned by Recraft, public and NOT licensed for commercial use | Remove-background operation exists; native alpha UNVERIFIED | Image to image, inpaint, replace background ($0.04 raster) | https://recraft.ai/docs/api-reference/pricing |
| Leonardo, Midjourney, Adobe Firefly | - | UNVERIFIED (pricing pages unreachable or no public API found) | UNVERIFIED | UNVERIFIED | UNVERIFIED | https://docs.leonardo.ai/docs/getting-started |

Terms-of-service limits on character art were not read for any vendor (UNVERIFIED). A chat subscription is usually billed separately from API use; only OpenAI's own pages hint at promotional credits for eligible subscriptions, and that article was not readable.

## 2. Making the art: local models (nothing leaves the computer)

| Model | Memory need (basis) | Licence (commercial) | Notes | Source |
|---|---|---|---|---|
| FLUX.2 klein 4B | stated: fits in about 13 GB VRAM (RTX 3090 / 4070 and above) | Apache-2.0 (yes) | Cleanly licensed local generator verified for this use. | https://huggingface.co/black-forest-labs/FLUX.2-klein-4B |
| Z-Image-Turbo | stated: fits comfortably within 16 GB VRAM consumer devices; 8 NFEs | Apache-2.0 (yes) | Sub-second on an H800 (stated). | https://huggingface.co/Tongyi-MAI/Z-Image-Turbo |
| Qwen-Image / Qwen-Image-Edit | UNVERIFIED on the model card; the README says DiffSynth-Studio offers layer-by-layer offload ("inference within 4 GB VRAM") and FP8 | Apache-2.0 (yes) | Edit models take a reference image. Check the VRAM yourself. | https://github.com/QwenLM/Qwen-Image |
| Qwen-Image-Layered | UNVERIFIED (repo is 57.7 GB; bf16 on CUDA in the quick start) | Apache-2.0 (yes) | Decomposes an image into multiple RGBA layers (3 or 8 shown, recursive; 640 resolution recommended). Part-level quality for anime face parts is not shown on the card. | https://github.com/QwenLM/Qwen-Image-Layered |
| HiDream-I1-Full | UNVERIFIED | MIT for the transformer; its text encoder includes Llama 3.1 under its own licence (check) | - | https://huggingface.co/HiDream-ai/HiDream-I1-Full |
| FLUX.1 schnell | UNVERIFIED | Apache-2.0 (yes) | - | https://huggingface.co/black-forest-labs/FLUX.1-schnell |
| FLUX.1 dev / FLUX.2 dev | FLUX.2 dev is 32B BF16; the example uses a 4-bit model plus a remote text encoder on an RTX 4090; no minimum given | FLUX non-commercial licence ("other") (no) | Non-commercial model use. | https://huggingface.co/black-forest-labs/FLUX.2-dev |
| SDXL base, Illustrious-XL, NoobAI-XL | UNVERIFIED | SDXL openrail++; Illustrious and NoobAI licence terms not read (UNVERIFIED) (check) | Anime fine-tunes of SDXL. | https://huggingface.co/OnomaAIResearch/Illustrious-xl-early-release-v0 |
| LayerDiffuse (Forge extension) | UNVERIFIED | Apache-2.0 (yes) | SDXL transparent generation and foreground/background layers; handles glass and semi-transparent effects better than background removal. Last push 2024. | https://github.com/lllyasviel/LayerDiffuse |

Only FLUX.2 klein 4B (about 13 GB) and Z-Image-Turbo (16 GB) have a memory figure on a primary page; for the others the setup says the need is not stated and asks the user to check before installing.

### Runtimes that run them

| Runtime | Platforms | Notes | Source |
|---|---|---|---|
| ComfyUI | Windows, Linux, macOS; NVIDIA, AMD, Intel, Apple Silicon | GPL-3.0; v0.45.0 (2026-11-10); weight streaming "as low as 4 GB VRAM + 8 GB RAM"; portable Windows build can run CPU-only | https://github.com/Comfy-Org/ComfyUI |
| Stable Diffusion WebUI Forge | based on SD-WebUI 1.10.1 | AGPL-3.0; stale (last push 2025-07) | https://github.com/lllyasviel/stable-diffusion-webui-forge |
| InvokeAI | desktop/web | Apache-2.0; active (2026-11-12) | https://github.com/invoke-ai/InvokeAI |
| stable-diffusion.cpp | pure C/C++; backends Vulkan/Metal/CUDA not confirmed | MIT; lists Flux, FLUX.2-klein, Qwen-Image, Qwen-Image-Edit, Z-Image | https://github.com/leejet/stable-diffusion.cpp |
| Diffusers (Python) | Python | Apache-2.0; active | https://github.com/huggingface/diffusers |
| Draw Things (Apple) | macOS/iOS app | GPL-3.0 community repo; v26.1023.0 (2026-10-23) | https://github.com/drawthingsai/draw-things-community |

## 3. Cutting out and splitting parts

| Tool | Licence (commercial) | Notes | Status | Source |
|---|---|---|---|---|
| rembg | MIT (yes) | Python 3.11-3.13; CLI, library, HTTP server, Docker; CPU by default, GPU via onnxruntime-gpu (CUDA) or ROCm | maintained (2026-11-06) | https://github.com/danielgatis/rembg |
| BiRefNet | MIT (yes) | FP16 1024x1024 at 17 FPS in 3.45 GB GPU memory on an RTX 4090 (stated); ONNX available | maintained (2026-10-25) | https://github.com/ZhengPeng7/BiRefNet |
| ToonOut (BiRefNet fine-tuned for anime) | MIT code and weights; dataset CC-BY 4.0 (yes) | 1,228 annotated anime images; fork MatteoKartoon/BiRefNet | maintained (2026-06-12) | https://github.com/MatteoKartoon/BiRefNet |
| BRIA RMBG-2.0 | CC BY-NC 4.0; commercial use needs an agreement with BRIA (no) | Avoid for commercial work. | updated 2026-10-21 | https://huggingface.co/briaai/RMBG-2.0 |
| SAM 2 / 2.1 | Apache-2.0 (yes) | Promptable segmentation for part masks | maintained (2026-05-30) | https://github.com/facebookresearch/sam2 |
| SAM 3 | custom SAM License (Nov 19, 2025); excludes ITAR/trade-control uses; Hugging Face gated (check) | Needs Python 3.12+, PyTorch 2.7+, a CUDA GPU with CUDA 12.6+ | maintained (2026-11-10) | https://github.com/facebookresearch/sam3 |

No dedicated anime part-segmentation ("see-through layer") tool was found on a primary page (UNVERIFIED that none exists). Qwen-Image-Layered produces RGBA layers but its card does not show anime face-part quality.

## 4. Rigging toolchains

| Toolchain | Cost | Licence / limits | Notes | Source |
|---|---|---|---|---|
| Live2D Cubism Editor FREE | always free | Free for General Users and Small-Scale Enterprises (annual sales under 10 million yen) including commercial use; others non-commercial/supervision only; limits: texture files 1, texture px 2048, artmeshes 100, motion parameters 30, blend shape parameters 3, deformers 50, parts 30, warp divisions 9x9 | Exceeding a limit means you cannot save the file. PRO files open in FREE. Windows and macOS only (no Linux build listed). | https://www.live2d.com/en/cubism/comparison/ |
| Live2D Cubism Editor PRO | price UNVERIFIED (purchase page did not load); 42-day trial; student discount 76% off a 3-year subscription | subscription; no texture/ArtMesh limits; warp divisions up to 100x100; limits: - | Windows and macOS. Current build 5.3.04 (2026-09-03). | https://www.live2d.com/en/cubism/download/editor/ |
| Umamo | free (GPL-3.0) | GPL-3.0; limits: - | ALPHA, early development (v0.5.0, 2026-11-07); imports/exports CMO3 and MOC3, native .uma; no animation yet; Windows, macOS, Linux; the .jar needs Java 21+, packaged builds do not. This plugin builds through it. | https://github.com/umamoorg/umamo |
| Inochi2D / Inochi Creator | free (BSD-2-Clause) | BSD-2-Clause; limits: - | Inochi Creator latest release v0.8.6 (2024-09-18), last push 2025-06-16: effectively unmaintained. VTube Studio loading Inochi formats: UNVERIFIED. | https://github.com/Inochi2D/inochi-creator |
| nijigenerate | free (BSD-2-Clause) | BSD-2-Clause; limits: - | v1.0.0-beta4 (2026-10-10); no official stable build; nijilive format derived from Inochi2D 0.8; companion VTuber app nijiexpose. | https://github.com/nijigenerate/nijigenerate |

**Cubism FREE cannot save a file that exceeds a limit** (1 texture of 2048 px, 100 ArtMeshes, 30 parts, 50 deformers, 30 motion parameters, 9x9 warp divisions). A fully rigged character will often need PRO.
FREE commercial use is for General Users and Small-Scale Enterprises (annual sales under 10 million yen). The plugin's `cubism_free_check` compares a described rig with these limits.

## 5. Publishing and compatibility

| Topic | What the sources say | Source |
|---|---|---|
| Cubism SDK / Publication License | The SDK is downloadable at no initial cost. Business entities must sign the SDK Release License (Publication License Agreement) at least one month before release; individuals and Small-Scale Enterprises are exempt except for "Expandable Applications". VTubing needs a separate agreement above 20 million yen annual revenue "under certain conditions"; VTuber tracking software counts as an Expandable Application. | https://www.live2d.com/en/sdk/license/ |
| VTube Studio model requirements | Needs <model>.model3.json, <model>.moc3 and the texture folder in a Live2DModels folder. Export from Cubism with File > Export For Runtime > Export as .moc3 (export version SDK 3.0, 3.3, 4.0, 5.0 or newer) and export physics3.json. Large textures may lag or crash on mobile. Only Cubism .moc3 is confirmed; Inochi formats are UNVERIFIED. | https://github.com/DenchiSoft/VTubeStudio/wiki/Loading-your-own-Models |
| Official sample models | Governed by the Free Material License Agreement and the Cubism Sample Data Terms of Use; commercial rights UNVERIFIED (terms not read). Sample code CubismWebSamples/NativeSamples 5-r.5 (2026-04-02). | https://www.live2d.com/en/learn/sample/ |

## 6. Staleness: how the plugin checks its own knowledge

`live2d_setup` returns `knowledge_freshness`. Knowledge is stale when last checked more than 30 days ago (counting approved research) or when a known deadline passed after the last check:

| Date | What changes | Source |
|---|---|---|
| 2027-03-15 | Google shuts down gemini-2.5-flash-image (migrate to 3.1 Flash Lite Image) | https://aistudio.google.com/docs/pricing |

If stale or a deadline is near, tell the user and **ask whether they want you to research the current facts online. Never research without their yes.** If they agree, read the source link of each
affected row (primary pages only) and save only what you verified with `knowledge_updates` (`{id, field, value, source, date}`; stored as dated overrides in the user's plugin data; the shipped catalog is unchanged).

Still UNVERIFIED on 2026-11-12: OpenAI transparent-background support and per-image cost; Gemini free-tier status for some models; alpha output for most services; BFL free credits and self-host prices; Ideogram per-image API price;
Leonardo, Midjourney and Adobe Firefly pricing; every vendor's terms on character art; most local model memory needs and quantized sizes; Cubism PRO price, Linux support and sample-data commercial terms;
whether VTube Studio loads Inochi formats.

## 7. Evidence boundary

Documentation review only. Nothing here generated an image or ran a rig tool. A catalog entry is not an installation and not authorization to spend money.
