"""Read-only inspection of common Cubism model3 resource references."""
import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath

PRIVATE = {'.ssh', '.gnupg', '.aws', '.azure', '.codex', '.docker', '.kube', '.pki', '.config', '.hermes'}


def stable_bytes(path, limit):
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode): raise ValueError('Choose a regular Cubism JSON file')
        raw = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    if len(raw) > limit: raise ValueError('Cubism JSON exceeds size limit')
    current = Path(path).lstat()
    identity = lambda x: (x.st_dev, x.st_ino, x.st_size, x.st_mtime_ns)
    if identity(before) != identity(after) or identity(after) != identity(current) or not stat.S_ISREG(current.st_mode):
        raise ValueError('Cubism JSON changed while reading')
    return raw


def _private(path, own_root=None):
    """True when the path runs through a private folder. The plugin's OWN project folder (internal calls only) may sit under .hermes, so only the part below it counts."""
    parts = path.parts
    if own_root is not None:
        try: parts = path.resolve().relative_to(Path(own_root).resolve()).parts
        except (ValueError, OSError): pass
    return any(x.casefold() in PRIVATE for x in parts)


def inspect_resources(model_path, own_root=None):
    p = Path(model_path).expanduser()
    if p.is_symlink() or _private(p, own_root):
        raise ValueError('Private paths and symlink inputs are unsupported')
    p = p.resolve(strict=True)
    if _private(p, own_root) or not p.is_file() or not p.name.endswith('.model3.json'):
        raise ValueError('Select a model3.json file outside private configuration')
    raw = stable_bytes(p, 4 * 1024**2)
    try:
        model = json.loads(raw)
    except (ValueError, RecursionError) as exc:
        raise ValueError('Invalid model settings JSON') from exc
    refs = model.get('FileReferences') if isinstance(model, dict) else None
    if not isinstance(refs, dict):
        raise ValueError('Missing FileReferences object')
    entries, issues = [], []
    def add(kind, value):
        if not isinstance(value, str) or not value:
            issues.append({'kind': kind, 'status': 'missing_or_invalid_reference'})
            return
        path = PurePosixPath(value)
        if '\\' in value or path.is_absolute() or any(x == '..' or ':' in x for x in path.parts):
            issues.append({'kind': kind, 'status': 'unsafe_reference', 'path': value})
            return
        target = p.parent.joinpath(*path.parts)
        resolved = target.resolve()
        if p.parent not in resolved.parents or target.is_symlink():
            issues.append({'kind': kind, 'status': 'outside_directory_or_symlink', 'path': value})
            return
        entries.append({'kind': kind, 'path': value, 'status': 'present' if target.is_file() else 'missing'})
    add('Moc', refs.get('Moc'))
    textures = refs.get('Textures')
    if not isinstance(textures, list) or not textures:
        issues.append({'kind': 'Textures', 'status': 'missing_or_invalid_reference'})
    else:
        for item in textures[:1000]: add('Texture', item)
        if len(textures) > 1000: raise ValueError('Too many textures')
    for key in ('Physics', 'Pose', 'UserData', 'DisplayInfo'):
        if key in refs: add(key, refs[key])
    expressions = refs.get('Expressions', [])
    motions = refs.get('Motions', {})
    if not isinstance(expressions, list) or not isinstance(motions, dict):
        raise ValueError('Invalid expression or motion references')
    if len(expressions) > 1000 or len(motions) > 1000:
        raise ValueError('Too many expressions or motion groups')
    for entry in expressions:
        add('Expression', entry.get('File') if isinstance(entry, dict) else None)
    count = 0
    for group, values in motions.items():
        if not isinstance(values, list): raise ValueError('Invalid motion group')
        count += len(values)
        if count > 1000: raise ValueError('Too many motions')
        for entry in values:
            add('Motion', entry.get('File') if isinstance(entry, dict) else None)
            if isinstance(entry, dict) and 'Sound' in entry: add('Motion sound', entry['Sound'])
    return {'settings_sha256': hashlib.sha256(raw).hexdigest(), 'version': model.get('Version'), 'resources': entries, 'issues': issues,
            'notice': 'Presence is not content validity. This does not load the model, exercise parameters, inspect deformation or verify all extensions.'}
