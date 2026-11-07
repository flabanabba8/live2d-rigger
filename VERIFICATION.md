# Verification

- Mixed-case protected-directory fixtures passed on Linux and native Windows; no real credentials were used. This is not a full platform or publication audit.

- Native Windows Python 3.14 checked the references in a synthetic model file with dummy resources. No user rig was accessed.
- Earlier Linux fixture tests checked model references and motion/display-ID structure. No real rig was loaded, rendered or exercised.
- Static checks cannot establish visual quality or MOC contents. Real rig validation, a reviewed demo and a complete publication audit remain open.

- 2026-11-07: tools renamed `live2d_inspect_resources` and `live2d_check_motion` so the Live2D association is explicit. Read-only copies of five official Live2D reference samples (Haru, Mao, Mark, Natori, Ren) and two user-made rigs (male orc, coral squid) were checked: 175 resources all present, 55 motion files with no problems. A copy of Haru with its texture folder and physics file deleted reported 3 missing resources. This is static resource checking only: no MOC3 parsing, rendering or parameter testing. Sample redistribution terms are unchanged; nothing was bundled.
