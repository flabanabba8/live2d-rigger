"""Live2D Rigger: scan this computer, interview the user, recommend, and remember the choices.

Nothing here generates an image, installs a tool, starts a model or sends anything over the network. It looks at installed programs and the hardware,
then lists the image-generation routes (hosted and local), cutout tools and rigging toolchains from the plugin's dated catalog and ASKS the user which to use.
The plugin never picks for the user. Its knowledge is checked for staleness and the user may approve online research to refresh it (freshness block below)."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def profile_path(root):
    return Path(root) / 'live2d-profile' / 'profile.json'


# ---- knowledge freshness (generic block; identical in modlab/resources.py) ----
import datetime as _dt
MAX_AGE_DAYS = 30
UPDATE_FIELDS = ('free_tier', 'paid', 'needs', 'caveats', 'models', 'min_vram_gb', 'vram_basis', 'min_ram_gb', 'license', 'commercial', 'cloning', 'languages',
                 'status', 'notes', 'openai_endpoint', 'openai_style', 'install', 'platforms', 'how_to_run', 'smaller_variants', 'gpu_requirements', 'recommend',
                 'cost', 'price', 'limits', 'finding', 'rules', 'meaning', 'transparent_background', 'reference_image_edit', 'timestamps', 'subtitle_output', 'diarization',
                 'data_use', 'works_with_this_plugin', 'word_timestamps', 'rtf', 'free_minutes')


def _today(today=None):
    return today or _dt.date.today()


def _parse_day(text):
    try:
        return _dt.date.fromisoformat(str(text))
    except ValueError:
        return None


def freshness(verified, expiries=(), last_refresh=None, today=None, max_age_days=MAX_AGE_DAYS):
    """Is the shipped knowledge out of date? Returns {'verified', 'age_days', 'stale', 'reasons', 'coming_up', 'offer'}.
    Stale when older than max_age_days (counting the latest user-approved research refresh) or when a known deadline has passed."""
    now = _today(today)
    days = [d for d in (_parse_day(verified), _parse_day(last_refresh)) if d]
    newest = max(days) if days else None
    age = (now - newest).days if newest else None
    reasons, coming = [], []
    if age is None:
        reasons.append('the knowledge has no verification date')
    elif age > max_age_days:
        reasons.append('it was last checked %d days ago (checked %s; this plugin treats more than %d days as stale)' % (age, newest.isoformat(), max_age_days))
    for e in expiries:
        d = _parse_day(e.get('date'))
        if not d:
            continue
        if d <= now:
            if newest is None or d > newest:   # a deadline that passed before the last check is already reflected in what was checked
                reasons.append('a known deadline has passed (%s): %s' % (d.isoformat(), e.get('what')))
        elif (d - now).days <= max_age_days:
            coming.append('%s (%s): %s' % (d.isoformat(), '%d days away' % (d - now).days, e.get('what')))
    stale = bool(reasons)
    offer = None
    if stale or coming:
        offer = ('Some of this built-in knowledge may be out of date%s. Tell the user plainly what may have changed and ASK whether they want you to research '
                 'the current facts on the internet now, using the source links in the wiki (primary pages only). Do not research without their yes. If they say yes, '
                 'read the primary pages, then save only what you verified with the setup tool\'s knowledge_updates argument (each with its source link and date), '
                 'and tell the user what changed and what you could not verify. If they say no, carry on and say the numbers may be old.') % (' (' + '; '.join(reasons) + ')' if reasons else '')
    return {'verified': newest.isoformat() if newest else None, 'age_days': age, 'stale': stale, 'reasons': reasons, 'coming_up': coming, 'offer': offer}


def _updates_path(root):
    return profile_path(root).parent / 'knowledge-updates.json'


def load_updates(root):
    try:
        data = json.loads(_updates_path(root).read_text())
        return data if isinstance(data, dict) and isinstance(data.get('updates'), list) else {'updates': [], 'last_refresh': None}
    except (OSError, ValueError):
        return {'updates': [], 'last_refresh': None}


def save_updates(root, updates, known_ids, today=None):
    """Store research results the user approved. Each update: {id, field, value, source (https URL), date}. Nothing is trusted blindly:
    unknown ids/fields, non-https sources, future dates and oversized values are refused. Returns the stored file contents."""
    now = _today(today)
    if not isinstance(updates, list) or not 1 <= len(updates) <= 100:
        raise ValueError('knowledge_updates must be a list of 1 to 100 items')
    clean = []
    for u in updates:
        if not isinstance(u, dict) or set(u) - {'id', 'field', 'value', 'source', 'date', 'note'}:
            raise ValueError('each update needs id, field, value, source and date (note is optional)')
        if u.get('id') not in known_ids:
            raise ValueError('unknown id "%s"; use an id from the wiki tables' % u.get('id'))
        if u.get('field') not in UPDATE_FIELDS:
            raise ValueError('field "%s" cannot be updated; allowed: %s' % (u.get('field'), ', '.join(UPDATE_FIELDS)))
        value = u.get('value')
        if not (isinstance(value, (str, bool, int, float, list)) or value is None) or len(json.dumps(value)) > 1500:
            raise ValueError('value is too large or not plain data')
        src = u.get('source')
        if not isinstance(src, str) or not src.startswith('https://') or len(src) > 500:
            raise ValueError('every update needs the https source page it was verified on')
        day = _parse_day(u.get('date'))
        if not day or day > now:
            raise ValueError('every update needs the date you read the source (not in the future)')
        clean.append({'id': u['id'], 'field': u['field'], 'value': value, 'source': src, 'date': day.isoformat(), 'note': str(u.get('note', ''))[:300]})
    data = load_updates(root)
    data['updates'] = (data['updates'] + clean)[-500:]
    data['last_refresh'] = max(c['date'] for c in clean)
    path = _updates_path(root)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2))
    tmp.chmod(0o600)
    tmp.replace(path)
    return data


def apply_updates(rows, updates):
    """Overlay approved research on catalog rows (the shipped catalog file is never modified). Later updates win."""
    by = {r['id']: r for r in rows}
    for u in updates:
        r = by.get(u['id'])
        if r is not None:
            r[u['field']] = u['value']
            r.setdefault('updated_by_research', {})[u['field']] = {'source': u['source'], 'date': u['date']}
    return rows
# ---- end knowledge freshness ----

def hardware(run=subprocess.run, platform=None, which=shutil.which, read_text=None):
    """Numbers only about THIS computer: operating system, CPU threads, RAM, GPUs with memory, Apple Silicon.
    No hostname, serial number or account detail. Reads local files and runs local programs; sends nothing."""
    platform = platform or sys.platform
    def _read(path):
        with open(path) as f:
            return f.read()
    read_text = read_text or _read
    hw = {'os': 'windows' if platform.startswith('win') else 'macos' if platform == 'darwin' else 'linux',
          'cpu_threads': os.cpu_count() or 1, 'ram_gb': None, 'gpus': [], 'apple_silicon': False}

    def out(argv, timeout=15):
        try:
            r = run(argv, capture_output=True, text=True, timeout=timeout)
            return r.stdout if r.returncode == 0 else ''
        except Exception:
            return ''
    try:
        if hw['os'] == 'linux':
            for line in read_text('/proc/meminfo').splitlines():
                if line.startswith('MemTotal:'):
                    hw['ram_gb'] = round(int(line.split()[1]) / 1024 / 1024, 1)
        elif hw['os'] == 'macos':
            mem = out(['sysctl', '-n', 'hw.memsize']).strip()
            hw['ram_gb'] = round(int(mem) / 1024 ** 3, 1) if mem.isdigit() else None
            brand = out(['sysctl', '-n', 'machdep.cpu.brand_string'])
            hw['apple_silicon'] = 'Apple' in brand
        else:
            mem = out(['powershell', '-NoProfile', '-Command', '(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory']).strip()
            hw['ram_gb'] = round(int(mem) / 1024 ** 3, 1) if mem.isdigit() else None
    except Exception:
        pass
    if which('nvidia-smi'):
        text = out([which('nvidia-smi'), '--query-gpu=name,memory.total,compute_cap', '--format=csv,noheader,nounits'])
        for line in text.splitlines():
            parts = [p.strip() for p in line.split(',')]
            if len(parts) == 3 and parts[1].isdigit():
                try:
                    cc = float(parts[2])
                except ValueError:
                    cc = None
                hw['gpus'].append({'vendor': 'nvidia', 'name': parts[0], 'vram_gb': round(int(parts[1]) / 1024, 1), 'compute_capability': cc})
        if not hw['gpus']:   # older drivers do not know compute_cap
            for line in out([which('nvidia-smi'), '--query-gpu=name,memory.total', '--format=csv,noheader,nounits']).splitlines():
                name, _, mem = line.rpartition(',')
                if name and mem.strip().isdigit():
                    hw['gpus'].append({'vendor': 'nvidia', 'name': name.strip(), 'vram_gb': round(int(mem) / 1024, 1), 'compute_capability': None})
    if which('rocm-smi') and not hw['gpus']:
        try:
            data = json.loads(out([which('rocm-smi'), '--showmeminfo', 'vram', '--json']) or '{}')
            for card, info in data.items():
                total = info.get('VRAM Total Memory (B)')
                if total and str(total).isdigit():
                    hw['gpus'].append({'vendor': 'amd', 'name': card, 'vram_gb': round(int(total) / 1024 ** 3, 1)})
        except Exception:
            pass
    return hw


def usable_gpu_memory(hw):
    """GB a model could use: the biggest single GPU's VRAM, or on Apple Silicon about 70 percent of unified memory."""
    best = max((g['vram_gb'] for g in hw['gpus']), default=0)
    if hw['apple_silicon'] and hw['ram_gb']:
        best = max(best, round(hw['ram_gb'] * 0.7, 1))
    return best




# ---------------------------------------------------------------- catalog
SECTIONS = ('hosted_image', 'local_image', 'image_runtimes', 'cutout', 'rigging', 'publishing')


def load_catalog(path=None, update_root=None):
    path = Path(path) if path else Path(__file__).resolve().parent / 'live2d_catalog.json'
    try:
        cat = json.loads(path.read_text())
    except (OSError, ValueError):
        return {'verified': None, 'expiries': [], **{k: [] for k in SECTIONS}}
    if update_root is not None:
        data = load_updates(update_root)
        for key in SECTIONS:
            apply_updates(cat.get(key, []), data['updates'])
        cat['last_refresh'] = data.get('last_refresh')
    return cat


def known_ids():
    cat = load_catalog()
    return {r['id'] for k in SECTIONS for r in cat.get(k, [])}


def live2d_freshness(root, today=None):
    cat = load_catalog(update_root=root)
    return freshness(cat.get('verified'), cat.get('expiries', []), cat.get('last_refresh'), today)


# ---------------------------------------------------------------- environment
def installed(catalog=None, which=shutil.which):
    """Programs on PATH that matter here. Presence only; nothing is executed."""
    cat = catalog or load_catalog()
    out = {'java': which('java'), 'python': which('python3') or which('python'), 'umamo': which('umamo')}
    for r in cat.get('image_runtimes', []) + cat.get('cutout', []) + cat.get('rigging', []):
        for c in r.get('commands', []):
            if which(c):
                out[r['id']] = which(c)
                break
    return {k: v for k, v in out.items() if v}


def survey(root, catalog=None, which=shutil.which, hw=None, keys=None):
    cat = catalog or load_catalog(update_root=root)
    keys = keys if keys is not None else {n: bool(os.environ.get(n)) for n in ('OPENAI_API_KEY', 'GEMINI_API_KEY', 'BFL_API_KEY', 'STABILITY_API_KEY', 'IDEOGRAM_API_KEY', 'RECRAFT_API_TOKEN')}
    return {'installed_on_path': installed(cat, which), 'hardware': hw or hardware(), 'image_service_keys_present': sorted(k for k, v in keys.items() if v),
            'note': 'Presence of a key is reported as yes/no only; the Cubism Editor lives outside PATH, so ask the user whether they have it.'}


# ---------------------------------------------------------------- recommendations
def recommend(report, profile=None, catalog=None):
    cat = catalog or load_catalog()
    hw = report['hardware']; gpu = usable_gpu_memory(hw)
    upload = profile is None or profile.get('allow_upload', True)
    local_fit, local_unknown = [], []
    for m in sorted(cat.get('local_image', []), key=lambda m: (m['tier'], m['name'])):
        row = {k: m.get(k) for k in ('id', 'name', 'license', 'commercial', 'vram_basis', 'notes', 'source', 'verified', 'role')}
        if m.get('min_vram_gb') is None:
            local_unknown.append({**row, 'fit': 'memory need not stated on a primary page; check before installing'})
        elif gpu >= m['min_vram_gb']:
            local_fit.append({**row, 'fit': 'fits your GPU (%.0f GB available, about %s GB stated)' % (gpu, m['min_vram_gb'])})
    hosted = [{k: h.get(k) for k in ('id', 'name', 'models', 'price', 'free_tier', 'transparent_background', 'reference_image_edit', 'caveats', 'source', 'verified')} for h in cat.get('hosted_image', [])] if upload else []
    commercial = (profile or {}).get('use') in ('commercial', 'game')
    cutouts = [{k: c.get(k) for k in ('id', 'name', 'license', 'commercial', 'notes', 'status', 'source', 'verified')} | ({'warning': 'not licensed for commercial use'} if commercial and c.get('commercial') == 'no' else {}) for c in cat.get('cutout', [])]
    return {'hardware': hw, 'local_image_that_fit': local_fit, 'local_image_memory_not_stated': local_unknown, 'hosted_image': hosted,
            'image_runtimes': cat.get('image_runtimes', []), 'cutout_tools': cutouts, 'rigging_toolchains': cat.get('rigging', []), 'publishing_notes': cat.get('publishing', []),
            'catalog_verified': cat.get('verified'),
            'note': 'Suggestions only; the user chooses. Prices, licences and limits were read on the dates shown and change often: re-check the source link before quoting. Nothing was generated, downloaded or installed.'}


FREE_LIMITS = {'texture_files': 1, 'texture_px': 2048, 'artmeshes': 100, 'parts': 30, 'deformers': 50, 'motion_parameters': 30}


def cubism_free_check(plan):
    """Compare the rig the user describes with Cubism FREE's documented limits. plan: {artmeshes, parts, deformers, texture_files, texture_px, motion_parameters}."""
    over = [(k, v, FREE_LIMITS[k]) for k, v in (plan or {}).items() if k in FREE_LIMITS and isinstance(v, (int, float)) and v > FREE_LIMITS[k]]
    if over:
        return {'fits_free': False, 'over': ['%s: %s (limit %s)' % o for o in over], 'note': 'FREE cannot save a file that exceeds a limit. Cubism PRO, Umamo (alpha) or another toolchain is needed.'}
    return {'fits_free': True, 'over': [], 'note': 'Within the documented FREE limits. FREE commercial use needs annual sales under 10 million yen.'}


# ---------------------------------------------------------------- interview / profile
USES = ('personal', 'vtubing', 'game', 'commercial')
SOURCES = ('own art', 'ai generated', 'existing model', 'official sample')
QUESTIONS = [
    {'key': 'character', 'ask': 'Describe the character you want (or the model you already have).', 'type': 'text'},
    {'key': 'source', 'ask': 'Where does the artwork come from?', 'type': 'choice', 'choices': list(SOURCES)},
    {'key': 'use', 'ask': 'What is the model for?', 'type': 'choice', 'choices': list(USES)},
    {'key': 'small_scale', 'ask': 'Is your (or your company\'s) annual sales under 10 million yen? (Cubism FREE\'s commercial use depends on it.)', 'type': 'yes/no/unknown'},
    {'key': 'allow_upload', 'ask': 'Is it OK to send prompts or art to an online image service? (A local model sends nothing anywhere.)', 'type': 'yes/no'},
    {'key': 'budget_usd', 'ask': 'Most you want to spend on image generation for this character, in US dollars (0 for free only)?', 'type': 'number'},
    {'key': 'has', 'ask': 'What do you already have: the Cubism Editor (FREE or PRO), Umamo, ComfyUI or another image tool, an image-service key in this plugin\'s settings, a JDK?', 'type': 'text'},
]
ROUTE_KEYS = ('image_route', 'cutout_route', 'rig_route')


def route_options(cat):
    return {'image_route': sorted({h['id'] for h in cat.get('hosted_image', []) if h['id'] != 'others-unverified'} | {m['id'] for m in cat.get('local_image', [])} | {'own-art'}),
            'cutout_route': sorted({c['id'] for c in cat.get('cutout', [])} | {'none'}),
            'rig_route': sorted({r['id'] for r in cat.get('rigging', [])})}


def save_profile(root, answers, options=None):
    if not isinstance(answers, dict):
        raise ValueError('answers must be an object with the interview keys')
    out = {'answered': True}
    c = answers.get('character')
    if not isinstance(c, str) or not c.strip() or len(c) > 600:
        raise ValueError('character: describe the character in up to 600 characters')
    out['character'] = c.strip()
    if answers.get('source') not in SOURCES: raise ValueError('source must be one of: ' + ', '.join(SOURCES))
    if answers.get('use') not in USES: raise ValueError('use must be one of: ' + ', '.join(USES))
    out['source'], out['use'] = answers['source'], answers['use']
    if answers.get('small_scale') not in (True, False, None): raise ValueError('small_scale must be true, false or null (unknown)')
    out['small_scale'] = answers.get('small_scale')
    if type(answers.get('allow_upload')) is not bool: raise ValueError('allow_upload must be true or false')
    out['allow_upload'] = answers['allow_upload']
    b = answers.get('budget_usd')
    if isinstance(b, bool) or not isinstance(b, (int, float)) or not 0 <= b <= 10000: raise ValueError('budget_usd must be a number from 0 to 10000')
    out['budget_usd'] = float(b)
    h = answers.get('has', '')
    if not isinstance(h, str) or len(h) > 400: raise ValueError('has: up to 400 characters')
    out['has'] = h.strip()
    for key in ROUTE_KEYS:
        v = answers.get(key)
        if v is not None:
            if not isinstance(v, str) or len(v) > 100: raise ValueError('%s must be the id of an option you were shown' % key)
            if options is not None and v not in options[key]: raise ValueError('%s "%s" is not one of the options: %s' % (key, v, ', '.join(options[key])))
        out[key] = v
    if out['image_route'] and not out['allow_upload'] and out['image_route'] in {'openai-image', 'gemini-image', 'bfl-flux', 'stability', 'ideogram', 'recraft'}:
        raise ValueError('You said nothing should be sent to an online service, so choose a local route or your own art for images')
    if out['use'] in ('commercial', 'game') and out['small_scale'] is False and out['rig_route'] == 'cubism-free':
        raise ValueError('Cubism FREE is limited to non-commercial use above 10 million yen annual sales; choose another toolchain or PRO')
    path = profile_path(root)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(out, indent=2))
    tmp.chmod(0o600)
    tmp.replace(path)
    return out


def load_profile(root):
    try:
        data = json.loads(profile_path(root).read_text())
        return data if isinstance(data, dict) and data.get('answered') else None
    except (OSError, ValueError):
        return None


def interview(root, report, answers=None):
    """Without answers: the report, suggestions, questions, freshness. With answers: validates, saves the three routes the user picked. Never picks."""
    cat = load_catalog(update_root=root)
    options = route_options(cat)
    if answers is not None:
        missing = [k for k in ROUTE_KEYS if not (isinstance(answers, dict) and answers.get(k))]
        if missing:
            raise ValueError('Ask the user which to use and pass %s (nothing was saved). Options: %s' % (', '.join(missing), '; '.join('%s: %s' % (k, ', '.join(options[k])) for k in missing)))
        profile = save_profile(root, answers, options)
        gaps = []
        if profile['rig_route'] == 'umamo':
            gaps.append('Umamo is alpha software (early development); expect missing features such as animation.')
        if profile['use'] == 'vtubing':
            gaps.append('VTube Studio loads Cubism .moc3 models; Inochi formats are UNVERIFIED there.')
        if profile['use'] in ('commercial', 'game'):
            gaps.append('Check the Cubism SDK / Publication License before release (see publishing notes).')
        return {'state': 'saved', 'profile': profile, 'you_chose': {k: profile[k] for k in ROUTE_KEYS}, 'gaps': gaps}
    existing = load_profile(root)
    state = 'interview_needed' if not existing or not all(existing.get(k) for k in ROUTE_KEYS) else 'answered'
    questions = list(QUESTIONS) + [{'key': k, 'ask': 'Which do you want to use for %s?' % k.replace('_route', '').replace('_', ' '), 'type': 'choice', 'choices': options[k]} for k in ROUTE_KEYS]
    return {'state': state, 'profile': existing, 'environment': report, 'recommendations': recommend(report, existing, cat), 'knowledge_freshness': live2d_freshness(root), 'questions': questions,
            'instructions_for_agent': 'Do not choose an image route, cutout tool or rigging toolchain for the user. Show them what was found on this computer, then the recommendations as suggestions: image routes (hosted with price, free tier, transparent-background and reference-edit support; local models that fit the GPU), cutout tools with licences, and rigging toolchains with their limits (Cubism FREE caps: 1 texture of 2048 px, 100 ArtMeshes, 30 parts, 50 deformers; PRO price UNVERIFIED) and licence terms. Say plainly what is UNVERIFIED. Quote prices and limits only with their source and date and tell the user to re-check the link. Read knowledge_freshness: if stale or something is coming up, tell the user and ask whether to research the current facts online; never research without their yes. Ask in one short message which route they want for images, cutout and rigging together with the other questions. Do not ask for or accept key values in chat. Then call the setup tool again with answers = {character, source, use, small_scale, allow_upload, budget_usd, has, image_route, cutout_route, rig_route}. Install and generate nothing until the answers are saved.'}


def apply_setup(root, report, answers=None, knowledge_updates=None):
    saved = None
    if knowledge_updates is not None:
        saved = len(save_updates(root, knowledge_updates, known_ids())['updates'])
    out = interview(root, report, answers)
    if saved is not None:
        out['knowledge_updates_saved'] = saved
    return out
