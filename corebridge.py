"""Portable Core motion renderer and inspector. Runs on the user's own machine with the user's own Cubism SDK viewer.

The viewer directory (never bundled here: Cubism Core is Live2D's proprietary library) must hold an index.html that
loads core.min.js and viewer.js, plus framework/Shaders/WebGL, and expose window.rig with frame(params, advance, dt),
draw(params, advance, dt), camera([x, y, w, h]), resetPhysics(), core, hash, coreVersion and parameters, and set
window.ready=true. It must read ?model=, ?width= and ?height= from its address.

usage:
  python corebridge.py render MODEL3_JSON OUTPUT_DIR --viewer DIR [--seconds 8] [--fps 30] [--view full|upper|head] [--width 720] [--height 1080] [--motion standard|rest|FILE.motion3.json]
  python corebridge.py inspect MODEL3_JSON --viewer DIR
Needs Playwright for Python and any Chromium it can launch; ffmpeg for render.
"""
import argparse, functools, glob, hashlib, http.server, json, math, shutil, subprocess, sys, tempfile, threading
from pathlib import Path

VIEWS = {'full': [-30, -30, 1040, 1700], 'upper': [60, 0, 840, 1260], 'head': [160, -20, 680, 980]}


def ease(t, a, b):
    u = min(1.0, max(0.0, (t-a)/(b-a)))
    return u*u*(3-2*u)


def standard_pose(t, seconds):
    """Head turns left, right, back to centre with holds (so loose hair follows through), blinks and a small body sway.
    Deterministic and loops cleanly: before/after renders of one model use exactly the same motion."""
    t = t/(seconds/8.0)
    turn = -ease(t, .4, 1.2) + 2*ease(t, 2.6, 3.6) - ease(t, 5.4, 6.4)
    a = t/8*math.tau
    blink = min(1.0, math.exp(-(((t % 4.0 - 2.1)/.07)**2)) + math.exp(-(((t % 8.0 - 6.9)/.07)**2)))
    return dict(ParamAngleX=26*turn, ParamAngleY=4*math.sin(2*a), ParamAngleZ=5*turn, ParamBodyAngleZ=5*math.sin(2*a),
                ParamBodyAngleX=4*turn, ParamBreath=.5-.5*math.cos(t*1.5), ParamEyeLOpen=1-blink, ParamEyeROpen=1-blink,
                ParamEyeBallX=.5*turn)


def motion_pose(motion, t):
    """Parameter values of a motion3.json document at time t (looped when the motion says so). Handles linear, Bezier, stepped and inverse-stepped segments."""
    meta = motion['Meta']; dur = float(meta['Duration'])
    if meta.get('Loop', True) and dur > 0:
        t = t % dur
    out = {}
    for curve in motion['Curves']:
        if curve.get('Target') != 'Parameter':
            continue
        raw = curve['Segments']; start = (raw[0], raw[1]); i = 2; value = raw[1]
        while i < len(raw):
            kind = int(raw[i])
            n = 3 if kind == 1 else 1
            pts = [start] + [(raw[i+1+2*k], raw[i+2+2*k]) for k in range(n)]
            end = pts[-1]
            if t <= end[0] or i + 1 + 2*n >= len(raw):
                span = (end[0]-start[0]) or 1e-9; u = min(1.0, max(0.0, (t-start[0])/span))
                if kind == 0: value = start[1] + (end[1]-start[1])*u
                elif kind == 1:
                    v = [p[1] for p in pts]
                    while len(v) > 1: v = [(1-u)*a+u*b for a, b in zip(v, v[1:])]
                    value = v[0]
                elif kind == 2: value = start[1]
                else: value = end[1]
                break
            start = end; i += 1 + 2*n
        out[curve['Id']] = value
    return out


def measure(frames, fps):
    """Plain facts about what actually moved in the rendered frames (parameter values as evaluated, physics included)."""
    def rng(*ids):
        vals = [f[i] for f in frames for i in ids if i in f]
        return [round(min(vals), 2), round(max(vals), 2)] if vals else None
    def swing(*ids):
        vals = [abs(f[i]) for f in frames for i in ids if i in f]
        return round(max(vals), 2) if vals else None
    eye = [min(f.get('ParamEyeLOpen', 1), f.get('ParamEyeROpen', 1)) for f in frames]
    blinks = sum(1 for a, b in zip(eye, eye[1:]) if a >= .5 > b)
    keep = {'seconds': round(len(frames)/fps, 1), 'head_turn_left_right_degrees': rng('ParamAngleX'), 'head_nod_degrees': rng('ParamAngleY'), 'head_tilt_degrees': rng('ParamAngleZ'),
            'body_sway_degrees': rng('ParamBodyAngleZ', 'ParamBodyAngleX'), 'breathing_0_to_1': rng('ParamBreath'), 'eyes_look_left_right': rng('ParamEyeBallX'), 'blinks': blinks,
            'hair_swing_strength_0_to_1': swing('ParamHairL1', 'ParamHairL2', 'ParamHairL3', 'ParamHairR1', 'ParamHairR2', 'ParamHairR3', 'ParamHairFront'), 'skirt_swing_0_to_1': swing('ParamSkirt')}
    return {k: v for k, v in keep.items() if v is not None}


def find_chromium():
    for name in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable'):
        if shutil.which(name):
            return shutil.which(name)
    hits = sorted(glob.glob(str(Path.home()/'.cache/ms-playwright/chromium-*/chrome-linux*/chrome')))
    return hits[-1] if hits else None


class Session:
    """Loopback server over viewer + model, headless Chromium, ready viewer page."""
    def __init__(self, model, viewer, width, height):
        self.model, self.viewer = Path(model).resolve(), Path(viewer).resolve()
        for need in ('index.html', 'viewer.js', 'core.min.js'):
            if not (self.viewer/need).is_file():
                raise RuntimeError(f'Viewer directory lacks {need}')
        if not self.model.is_file():
            raise RuntimeError('Model file not found')
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root/'viewer').symlink_to(self.viewer, target_is_directory=True)
        (root/'model').symlink_to(self.model.parent, target_is_directory=True)

        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a, **k):
                pass
        self.srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root)))
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        from playwright.sync_api import sync_playwright
        self.pw = sync_playwright().start()
        exe = find_chromium()
        self.browser = self.pw.chromium.launch(**({'executable_path': exe} if exe else {}), args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        self.page = self.browser.new_page(viewport={'width': width, 'height': height})
        self.page.goto(f'http://127.0.0.1:{self.srv.server_port}/viewer/index.html?model=/model/{self.model.name}&width={width}&height={height}&test=1')
        self.page.wait_for_function('window.ready===true', timeout=120000)
        self.page.add_style_tag(content=f'aside{{display:none!important}}main{{display:block!important}}canvas{{width:{width}px!important;height:{height}px!important;max-height:none!important}}')
        moc = self.model.parent/json.loads(self.model.read_text())['FileReferences']['Moc']
        self.moc_sha256 = hashlib.sha256(moc.read_bytes()).hexdigest()
        if self.page.evaluate('rig.hash') != self.moc_sha256:
            raise RuntimeError('The viewer loaded a different MOC than the one requested')

    def close(self):
        self.browser.close(); self.pw.stop(); self.srv.shutdown(); self.tmp.cleanup()


def inspect(model, viewer):
    s = Session(model, viewer, 540, 810)
    try:
        info = s.page.evaluate('''()=>({coreVersion:rig.coreVersion,parts:Array.from(rig.core.parts.ids),drawables:Array.from(rig.core.drawables.ids),parameters:rig.parameters})''')
        return {'mocSha256': s.moc_sha256, **info}
    finally:
        s.close()


def render(model, output, viewer, seconds=8.0, fps=30, view='full', width=720, height=1080, motion='standard'):
    out = Path(output).resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError('Choose a new or empty output directory')
    if not shutil.which('ffmpeg'):
        raise RuntimeError('ffmpeg is required')
    frames = out/'frames'; frames.mkdir(parents=True, exist_ok=True)
    if motion == 'standard': pose_at = lambda t: standard_pose(t, seconds)
    elif motion == 'rest': pose_at = lambda t: {}
    else:
        doc = json.loads(Path(motion).read_text()); pose_at = lambda t: motion_pose(doc, t)
    s = Session(model, viewer, width, height)
    try:
        s.page.evaluate('v=>rig.camera(v)', VIEWS[view])
        s.page.evaluate('rig.resetPhysics()')
        hair = []; allvals = []
        for i in range(int(seconds*fps)):
            r = s.page.evaluate('([p,dt])=>rig.draw(p,true,dt)', [pose_at(i/fps), 1/fps])
            if r['glError']:
                raise RuntimeError('WebGL error while drawing')
            allvals.append(r['values'])
            hair.append({k: v for k, v in r['values'].items() if k.startswith('ParamHair')})
            s.page.locator('canvas').screenshot(path=str(frames/f'{i:04}.png'))
        info = dict(motion=Path(motion).name if motion not in ('standard', 'rest') else motion, coreVersion=s.page.evaluate('rig.coreVersion'), mocSha256=s.moc_sha256, frames=len(hair), fps=fps, view=view,
                    hair_parameter_range={k: [round(min(h[k] for h in hair), 3), round(max(h[k] for h in hair), 3)] for k in (hair[0] if hair else {})})
        info['measured'] = measure(allvals, fps)
    finally:
        s.close()
    subprocess.run(['ffmpeg', '-v', 'error', '-framerate', str(fps), '-i', str(frames/'%04d.png'), '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2:color=0x26343a,format=yuv420p',
                    '-c:v', 'libx264', '-crf', '18', str(out/'motion.mp4')], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(out/'motion.mp4'), '-vf', f'fps={6/seconds:.5f},scale=360:-2,tile=6x1', '-frames:v', '1', str(out/'contact-sheet.png')], check=False)
    (out/'report.json').write_text(json.dumps(info, indent=2))
    shutil.rmtree(frames)
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mode', choices=['render', 'inspect']); ap.add_argument('model'); ap.add_argument('output', nargs='?')
    ap.add_argument('--viewer', required=True); ap.add_argument('--seconds', type=float, default=8); ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--motion', default='standard', help='standard, rest, or a motion3.json file'); ap.add_argument('--view', choices=list(VIEWS), default='full'); ap.add_argument('--width', type=int, default=720); ap.add_argument('--height', type=int, default=1080)
    a = ap.parse_args()
    if a.mode == 'inspect':
        print(json.dumps(inspect(a.model, a.viewer)))
    else:
        if not a.output:
            ap.error('render needs an output directory')
        print(json.dumps(render(a.model, a.output, a.viewer, a.seconds, a.fps, a.view, a.width, a.height, a.motion)))


if __name__ == '__main__':
    main()
