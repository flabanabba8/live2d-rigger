import importlib.util
import json
from pathlib import Path
import tempfile
import sys
import unittest

root = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('rig_motion_fixture', root/'__init__.py', submodule_search_locations=[str(root)])
plugin = importlib.util.module_from_spec(spec); sys.modules[spec.name] = plugin; spec.loader.exec_module(plugin)
core = plugin.motion


class MotionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir='/tmp')
        root = Path(self.tmp.name)
        self.cdi, self.motion = root/'test.cdi3.json', root/'test.motion3.json'
        self.cdi.write_text(json.dumps({'Parameters':[{'Id':'ParamAngleX'}], 'Parts':[{'Id':'PartHead'}]}))
        self.data = {'Meta':{'Duration':1, 'CurveCount':2, 'TotalSegmentCount':2, 'TotalPointCount':6},
                     'Curves':[{'Target':'Parameter', 'Id':'ParamAngleX', 'Segments':[0,0,0.0,1,30]},
                               {'Target':'PartOpacity', 'Id':'PartMissing', 'Segments':[0,0,1,0.2,0,0.8,1,1,1]}]}
        self.motion.write_text(json.dumps(self.data))
    def tearDown(self): self.tmp.cleanup()

    def test_valid_curve_counts_and_supplementary_warning(self):
        result = core.check_motion(str(self.cdi), str(self.motion))
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['computed_segments'], 2)
        self.assertEqual(result['computed_points'], 6)
        self.assertEqual(result['warnings'][0]['kind'], 'part_not_in_display_info')

    def test_malformed_curve_and_metadata(self):
        self.data['Curves'][1]['Segments'] = [0, 0, 1, 0.2, 0]
        self.motion.write_text(json.dumps(self.data))
        result = core.check_motion(str(self.cdi), str(self.motion))
        self.assertTrue(any(x['kind'] == 'incomplete_segment' for x in result['errors']))
        self.data['Curves'][1]['Segments'] = [0,0,0,1,1]
        self.data['Meta']['TotalPointCount'] = 100
        self.motion.write_text(json.dumps(self.data))
        result = core.check_motion(str(self.cdi), str(self.motion))
        self.assertTrue(any(x['kind'] == 'metadata_count_mismatch' for x in result['errors']))

    def test_nonfinite_and_out_of_order(self):
        self.data['Curves'][0]['Segments'] = [0,0,0,2,1]
        self.motion.write_text(json.dumps(self.data))
        self.assertTrue(any(x['kind'] == 'segment_time_out_of_order' for x in core.check_motion(str(self.cdi), str(self.motion))['errors']))
        self.data['Meta']['Duration'] = float('nan')
        self.motion.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, 'finite'):
            core.check_motion(str(self.cdi), str(self.motion))

if __name__ == '__main__': unittest.main()
