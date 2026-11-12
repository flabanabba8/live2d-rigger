"""Read-only checks for Cubism display-info IDs and motion curve structure."""
import hashlib
import json
import math
from pathlib import Path
from .core import stable_bytes

PRIVATE = {'.ssh', '.gnupg', '.aws', '.azure', '.codex', '.docker', '.kube', '.pki', '.config', '.hermes'}


def _private(path, own_root=None):
    """True when the path runs through a private folder. The plugin's OWN project folder (internal calls only) may sit under .hermes, so only the part below it counts."""
    parts = path.parts
    if own_root is not None:
        try: parts = path.resolve().relative_to(Path(own_root).resolve()).parts
        except (ValueError, OSError): pass
    return any(x.casefold() in PRIVATE for x in parts)


def read_json(value, suffix, own_root=None):
    path = Path(value).expanduser()
    if path.is_symlink() or _private(path, own_root): raise ValueError('Private paths and symlink inputs are unsupported')
    path = path.resolve(strict=True)
    if _private(path, own_root) or not path.is_file() or not path.name.endswith(suffix):
        raise ValueError('Choose the requested Cubism JSON file outside private configuration')
    raw = stable_bytes(path, 8 * 1024**2)
    try: data = json.loads(raw.decode('utf-8-sig'))
    except (ValueError, RecursionError) as exc: raise ValueError('Invalid Cubism JSON') from exc
    if not isinstance(data, dict): raise ValueError('Expected a JSON object')
    return data, hashlib.sha256(raw).hexdigest()


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def check_motion(cdi_path, motion_path, own_root=None):
    cdi, cdi_sha = read_json(cdi_path, '.cdi3.json', own_root)
    motion, motion_sha = read_json(motion_path, '.motion3.json', own_root)
    parameters, parts, curves = cdi.get('Parameters'), cdi.get('Parts', []), motion.get('Curves')
    if not isinstance(parameters, list) or not isinstance(parts, list) or not isinstance(curves, list):
        raise ValueError('Missing or invalid parameter, part or curve list')
    if len(parameters) + len(parts) + len(curves) > 30000: raise ValueError('Too many parameters, parts or curves')
    errors, warnings = [], []
    def ids(items, kind):
        result = set()
        for item in items:
            ident = item.get('Id') if isinstance(item, dict) else None
            if not isinstance(ident, str) or not ident or len(ident) > 256:
                errors.append({'kind': 'invalid_display_id', 'target': kind})
            elif ident in result:
                errors.append({'kind': 'duplicate_display_id', 'target': kind, 'id': ident})
            else: result.add(ident)
        return result
    param_ids, part_ids = ids(parameters, 'Parameter'), ids(parts, 'PartOpacity')
    meta = motion.get('Meta')
    duration = meta.get('Duration') if isinstance(meta, dict) else None
    if not number(duration) or duration <= 0: raise ValueError('Motion duration must be positive and finite')
    total_segments, total_points, invalid = 0, 0, False
    for index, curve in enumerate(curves):
        if not isinstance(curve, dict):
            errors.append({'kind': 'invalid_curve', 'curve': index}); invalid = True; continue
        target, ident, values = curve.get('Target'), curve.get('Id'), curve.get('Segments')
        if target not in ('Model', 'Parameter', 'PartOpacity') or not isinstance(ident, str) or not ident or len(ident) > 256:
            errors.append({'kind': 'invalid_curve_target', 'curve': index}); invalid = True; continue
        if target == 'Parameter' and ident not in param_ids:
            warnings.append({'kind': 'parameter_not_in_display_info', 'curve': index, 'id': ident})
        if target == 'PartOpacity' and ident not in part_ids:
            warnings.append({'kind': 'part_not_in_display_info', 'curve': index, 'id': ident})
        if not isinstance(values, list) or len(values) < 2 or any(not number(x) for x in values):
            errors.append({'kind': 'invalid_segment_numbers', 'curve': index}); invalid = True; continue
        previous = values[0]
        if previous < 0 or previous > duration:
            errors.append({'kind': 'point_time_outside_motion', 'curve': index}); invalid = True; continue
        cursor, segments, points = 2, 0, 1
        while cursor < len(values):
            code = values[cursor]
            if not number(code) or code not in (0, 1, 2, 3):
                errors.append({'kind': 'unsupported_segment_type', 'curve': index}); invalid = True; break
            point_count = 3 if code == 1 else 1
            end = cursor + 1 + point_count * 2
            if end > len(values):
                errors.append({'kind': 'incomplete_segment', 'curve': index}); invalid = True; break
            end_time = values[end-2]
            if end_time < previous or end_time > duration:
                errors.append({'kind': 'segment_time_out_of_order', 'curve': index}); invalid = True; break
            previous = end_time
            cursor = end
            segments += 1
            points += point_count
        total_segments += segments
        total_points += points
    if not invalid:
        for field, actual in [('CurveCount', len(curves)), ('TotalSegmentCount', total_segments), ('TotalPointCount', total_points)]:
            if field in meta and (not number(meta[field]) or meta[field] != actual):
                errors.append({'kind': 'metadata_count_mismatch', 'field': field, 'actual': actual})
    return {'display_info_sha256': cdi_sha, 'motion_sha256': motion_sha, 'curves': len(curves),
            'computed_segments': total_segments, 'computed_points': total_points, 'errors': errors, 'warnings': warnings,
            'notice': 'Display info is supplementary, so a missing ID does not prove the parameter is absent from the MOC. No parameter ranges, deformation or visual quality were verified.'}
