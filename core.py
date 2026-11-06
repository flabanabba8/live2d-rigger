"""Read-only inspection of common Cubism model3 resource references."""
import hashlib
import json
from pathlib import Path, PurePosixPath

PRIVATE = {'.ssh', '.gnupg', '.aws', '.azure', '.codex', '.docker', '.kube', '.pki', '.config', '.hermes'}


def inspect_resources(model_path):
    p = Path(model_path).expanduser()
    if p.is_symlink() or any(x in PRIVATE for x in p.parts):
        raise ValueError('Private paths and symlink inputs are unsupported')
    p = p.resolve(strict=True)
    if any(x in PRIVATE for x in p.parts) or not p.is_file() or not p.name.endswith('.model3.json'):
        raise ValueError('Select a model3.json file outside private configuration')
    with p.open('rb') as f:
        raw = f.read(4 * 1024**2 + 1)
    if len(raw) > 4 * 1024**2:
        raise ValueError('Model settings exceed 4 MiB')
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
