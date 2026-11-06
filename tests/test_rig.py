import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('rig_core', Path(__file__).parents[1] / 'core.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

class RigTests(unittest.TestCase):
    def test_common_resources_and_missing(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as tmp:
            root = Path(tmp)
            (root / 'model.moc3').write_bytes(b'fixture')
            (root / 'texture.png').write_bytes(b'fixture')
            model = root / 'model.model3.json'
            model.write_text(json.dumps({'Version': 3, 'FileReferences': {'Moc': 'model.moc3', 'Textures': ['texture.png'], 'Motions': {'Idle': [{'File': 'missing.motion3.json'}]}}}))
            result = core.inspect_resources(str(model))
            self.assertEqual([x['status'] for x in result['resources']], ['present', 'present', 'missing'])
            self.assertEqual(result['issues'], [])

    def test_escape_and_required_references(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as tmp:
            p = Path(tmp) / 'model.model3.json'
            p.write_text(json.dumps({'FileReferences': {'Moc': '../outside.moc3', 'Textures': []}}))
            result = core.inspect_resources(str(p))
            self.assertEqual([x['status'] for x in result['issues']], ['unsafe_reference', 'missing_or_invalid_reference'])

if __name__ == '__main__':
    unittest.main()
