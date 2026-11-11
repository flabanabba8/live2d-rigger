"""Official free Live2D sample models used only as structural references.

Nothing is bundled. Files come from Live2D's own sample-data host into this plugin's
own data folder, only after the caller states the user accepted Live2D's licence.
"""
import hashlib, io, json, shutil, stat, time, urllib.request, uuid, zipfile
from pathlib import Path, PurePosixPath
from .core import inspect_resources

BASE = 'https://cubism.live2d.com/sample-data/bin/'
PAGE = 'https://www.live2d.com/en/learn/sample/'
LICENCE = ('https://www.live2d.com/eula/live2d-free-material-license-agreement_en.html',
           'https://www.live2d.com/en/learn/sample/model-terms/')
CHECKED = '2026-11-10'
# Verified 2026-11-10 against the official sample pages and cubism.live2d.com/sample-data/js/download.js.
CATALOG = {
    'hiyori': ('Hiyori Momose', 'momose-hiyori/', 'hiyori/hiyori_en.zip'),
    'haru': ('Haru', 'haru/', 'haru/haru_ja.zip'),
    'mark': ('Mark-kun', 'mark/', 'mark/mark_en.zip'),
    'mao': ('Niziiro Mao', 'niziiro-mao/', 'mao/mao_en.zip'),
    'ren': ('Ren Foster', 'ren-foster/', 'ren/ren_en.zip'),
}
MAX_ZIP = 256 * 1024**2
MAX_FILES = 2000
CAP = 60


def _json(path, limit=8 * 1024**2):
    p = Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size > limit: raise ValueError('Unsafe or oversized reference JSON')
    return json.loads(p.read_text(encoding='utf-8'))


def _download(url):
    if not url.startswith(BASE): raise ValueError('Only the official Live2D sample-data host is allowed')
    request = urllib.request.Request(url, headers={'User-Agent': 'live2d-rigger-reference-fetch'})
    with urllib.request.urlopen(request, timeout=120) as r:
        if not r.geturl().startswith(BASE): raise ValueError('Redirected away from the official host')
        raw = r.read(MAX_ZIP + 1)
    if len(raw) > MAX_ZIP: raise ValueError('Sample archive exceeds size limit')
    return raw


def _extract(raw, dest):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos = z.infolist()
        if len(infos) > MAX_FILES or sum(i.file_size for i in infos) > 1024**3: raise ValueError('Sample archive too large')
        for i in infos:
            parts = PurePosixPath(i.filename)
            if parts.is_absolute() or '..' in parts.parts or '\\' in i.filename or stat.S_ISLNK(i.external_attr >> 16):
                raise ValueError('Unsafe path in sample archive')
        for i in infos:
            target = dest.joinpath(*PurePosixPath(i.filename).parts)
            if i.is_dir(): target.mkdir(parents=True, exist_ok=True); continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(i))


class References:
    def __init__(self, root, downloader=_download):
        self.root = Path(root) / 'reference-samples'
        self.downloader = downloader

    def _models(self, sample_id):
        base = self.root / sample_id / 'files'
        return sorted(base.rglob('*.model3.json')) if base.is_dir() else []

    def list(self):
        out = []
        for key, (name, page, zipname) in CATALOG.items():
            out.append({'sample_id': key, 'name': name, 'official_page': PAGE + page, 'official_archive': BASE + zipname,
                        'present': bool(self._models(key))})
        return {'samples': out, 'licence_documents': list(LICENCE), 'checked': CHECKED,
                'folder': str(self.root),
                'notice': 'Official free Live2D samples are structural references only. Show the user the licence links and obtain a yes before fetching. Never copy a sample\'s artwork into the user\'s model and never redistribute sample files. No sample is bundled with this plugin.'}

    def fetch(self, sample_id, accept_licence):
        if sample_id not in CATALOG: raise ValueError('Unknown sample; use live2d_reference_samples for the list')
        if accept_licence is not True:
            raise ValueError('Tell the user what will be downloaded from Live2D, show the licence links, and pass accept_licence=true only after the user agrees')
        if self._models(sample_id): return {'sample_id': sample_id, 'status': 'already_present', 'model': str(self._models(sample_id)[0])}
        name, page, zipname = CATALOG[sample_id]
        raw = self.downloader(BASE + zipname)
        staging = self.root / (sample_id + '.' + uuid.uuid4().hex[:8] + '.tmp')
        try:
            _extract(raw, staging / 'files')
            if not list((staging / 'files').rglob('*.model3.json')): raise ValueError('Archive has no model3.json; not accepted as a sample')
            (staging / 'source.json').write_text(json.dumps({'sample_id': sample_id, 'url': BASE + zipname, 'archive_sha256': hashlib.sha256(raw).hexdigest(),
                'fetched_epoch': int(time.time()), 'user_accepted_licence': True, 'licence_documents': list(LICENCE)}, indent=2))
            final = self.root / sample_id
            if final.exists(): shutil.rmtree(final)
            staging.rename(final)
        except Exception:
            shutil.rmtree(staging, ignore_errors=True); raise
        return {'sample_id': sample_id, 'status': 'fetched', 'model': str(self._models(sample_id)[0]), 'source': BASE + zipname}

    def summarize(self, sample_id):
        models = self._models(sample_id) if sample_id in CATALOG else []
        if not models: raise ValueError('Sample not present; fetch it first (with the user\'s licence agreement)')
        model = models[0]; folder = model.parent
        resources = inspect_resources(str(model))
        refs = _json(model).get('FileReferences', {})
        out = {'sample_id': sample_id, 'resource_check': {'issues': resources['issues'], 'resources': len(resources['resources'])},
               'expressions': [Path(e.get('File', '')).name for e in refs.get('Expressions', []) if isinstance(e, dict)][:CAP],
               'motion_groups': {g: len(v) for g, v in (refs.get('Motions') or {}).items() if isinstance(v, list)},
               'cmo3_editor_documents': [str(x.relative_to(self.root / sample_id)) for x in (self.root / sample_id / 'files').rglob('*.cmo3')][:10]}
        def side(key):
            ref = refs.get(key)
            return _json(folder / ref) if isinstance(ref, str) and '..' not in ref and (folder / ref).is_file() else None
        cdi = side('DisplayInfo')
        if cdi:
            params = cdi.get('Parameters', []); parts = cdi.get('Parts', [])
            out['display_info'] = {'parameter_count': len(params), 'parameters': [{'id': p.get('Id'), 'group': p.get('GroupId'), 'name': p.get('Name')} for p in params[:CAP * 3]],
                                   'parameter_groups': [g.get('Name') for g in cdi.get('ParameterGroups', [])][:CAP],
                                   'part_count': len(parts), 'parts': [{'id': p.get('Id'), 'name': p.get('Name')} for p in parts[:CAP * 3]]}
        phys = side('Physics')
        if phys:
            settings = phys.get('PhysicsSettings', [])
            out['physics'] = {'setting_count': len(settings), 'settings': [{'id': (s.get('Id')), 'inputs': [i.get('Source', {}).get('Id') for i in s.get('Input', [])],
                              'outputs': [o.get('Destination', {}).get('Id') for o in s.get('Output', [])], 'particles': len(s.get('Vertices', []))} for s in settings[:CAP]]}
        pose = side('Pose')
        if pose: out['pose_groups'] = len(pose.get('Groups', []))
        out['notice'] = ('Read from the sample\'s model3/cdi3/physics3/pose3 JSON only. Draw order and the deformer hierarchy live in the binary .moc3 and the .cmo3 editor document, which this tool does not parse; '
                         'study those in Cubism Editor if the user has it. Use as structure reference only: do not copy artwork.')
        return out


TOOLS = {
    'live2d_reference_samples': ('List the official free Live2D sample models this plugin knows (Hiyori, Haru, Mark, Mao, Ren) with their official pages, whether each is already in the plugin\'s data folder, and the licence links. With sample_id, summarise that present sample\'s structure (parameters, parts, physics, expressions, motions) as a reference.',
        {'sample_id': {'type': 'string'}}, [], 'summarize_or_list'),
    'live2d_fetch_reference_sample': ('Download one official free Live2D sample from Live2D\'s own sample-data host into this plugin\'s data folder, only as a structural reference. Requires accept_licence=true, which means you showed the user what is being downloaded and the licence links and the user agreed. Reuses a present sample.',
        {'sample_id': {'type': 'string'}, 'accept_licence': {'type': 'boolean'}}, ['sample_id', 'accept_licence'], 'fetch'),
}


def run(refs, name, args):
    if name == 'live2d_fetch_reference_sample': return refs.fetch(args['sample_id'], args.get('accept_licence'))
    return refs.summarize(args['sample_id']) if args.get('sample_id') else refs.list()
