# Official free sample models as structure references

Checked against Live2D's own pages on 2026-11-10. Re-check the pages before relying on this; licence terms can be amended by Live2D at any time.

## What Live2D offers (verified)

Live2D's sample page (https://www.live2d.com/en/learn/sample/) lists 28 free sample models. This plugin knows five: Hiyori Momose, Haru, Mark-kun, Niziiro Mao and Ren Foster. Each model page has a Download button that points to a zip on Live2D's sample-data host (https://cubism.live2d.com/sample-data/bin/). Zips contain the editor document (.cmo3), basic motions (.can3) and a runtime folder (.moc3, .model3.json, .motion3.json, .physics3.json, .pose3.json, .cdi3.json). The Haru archive listed on the site is the Japanese-language one.

Known and not offered here: the collaboration characters (for example Jin Natori) have stricter, per-character terms.

## Licence facts (verified 2026-11-10, Free Material License Agreement version 1.6, revised 3 February 2025, plus the Sample Data Terms of Use)

- The sample pages say general users and small-scale enterprises (under 10 million yen annual sales) may use the materials in creative activities, commercial or not, when publishing works that use them, and that consent to the Free Material License Agreement and the Sample Data Terms is required.
- Section 4.1.1 says the customer may not redistribute all or part of the Material to a third party. Redistribute is defined to include displaying or distributing part or whole copies.
- Section 4.1.2 says the customer may not modify, port, adapt or translate the Material except as expressly permitted.
- Section 4.1.3 bars reverse engineering of the "Freeware" (the editor software), not named for the model data.
- The English agreement has no general "study or reference" permission. The agreement says Japanese text prevails over translations.
- Character terms apply per character: for example the page states for Hiyori Momose and Miara that no changes to the character design are permitted.

Consequences for this plugin: nothing is bundled; samples go only into the user's own plugin data folder for their own use; never copy sample artwork into the user's model; never re-share or publish sample files; ask the user to read the licence links and agree before every first fetch. If the user is unsure, do not fetch, and continue without references. This is a summary of the vendor pages, not legal advice.

## Procedure

1. Call live2d_reference_samples to see which samples are present.
2. If you want one that is missing, tell the user which sample, where it comes from, and show the licence links from the tool result. Only after a clear yes, call live2d_fetch_reference_sample with that sample_id and accept_licence=true. Fetch one sample at a time.
3. Call live2d_reference_samples with sample_id to get parameters, parts, physics settings, expressions and motion groups. Use live2d_inspect_resources and live2d_check_motion on its model3.json and motion files if you need more.
4. Apply what you learn as structure: how finely the parts are split, which parameters exist, physics input/output pairing, expression files. Draw order and the deformer hierarchy are in the .moc3/.cmo3 and are not read by these tools; say so rather than guessing.
5. Make the user's rig from the user's artwork. Do not copy sample images, parts, or rig files into the user's project.
