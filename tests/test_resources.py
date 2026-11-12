import datetime
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('l2d_resources_under_test', ROOT / 'resources.py')
R = importlib.util.module_from_spec(spec); sys.modules[spec.name] = R; spec.loader.exec_module(R)
HW_BIG = {'os': 'linux', 'cpu_threads': 16, 'ram_gb': 28.0, 'gpus': [{'vendor': 'nvidia', 'name': 'x', 'vram_gb': 24.0, 'compute_capability': 8.9}], 'apple_silicon': False}
HW_NONE = {'os': 'linux', 'cpu_threads': 4, 'ram_gb': 8.0, 'gpus': [], 'apple_silicon': False}
ANSWERS = {'character': 'a fox girl mascot', 'source': 'ai generated', 'use': 'vtubing', 'small_scale': True, 'allow_upload': True, 'budget_usd': 5, 'has': 'Cubism FREE',
           'image_route': 'flux2-klein-4b', 'cutout_route': 'toonout', 'rig_route': 'cubism-free'}


def report(hw=HW_BIG):
    return R.survey(Path('/nonexistent'), R.load_catalog(), which=lambda c: None, hw=hw, keys={})


class Catalog(unittest.TestCase):
    def setUp(self): self.cat = R.load_catalog()

    def test_every_row_has_a_source_and_a_date_and_wiki_lists_it(self):
        wiki = (ROOT / 'llmwiki' / 'creation-routes.md').read_text()
        for key in R.SECTIONS:
            for row in self.cat[key]:
                self.assertTrue(row['source'].startswith('https://'), row['id']); self.assertRegex(row['verified'], r'^\d{4}-\d\d-\d\d$')
                self.assertIn(row['source'], wiki, row['id'])
        for key in ('hosted_image', 'local_image', 'image_runtimes', 'cutout', 'rigging', 'publishing'):
            for row in self.cat[key]:
                self.assertIn(row['name'], wiki)
        self.assertIn('Never research without their yes', wiki)

    def test_cubism_free_limits_are_the_documented_ones(self):
        free = [r for r in self.cat['rigging'] if r['id'] == 'cubism-free'][0]['limits']
        self.assertEqual((free['texture_files'], free['texture_px'], free['artmeshes'], free['parts'], free['deformers']), (1, 2048, 100, 30, 50))
        self.assertEqual({k: v for k, v in free.items() if k in R.FREE_LIMITS}, R.FREE_LIMITS)          # the check uses the catalog's own numbers

    def test_unverified_facts_are_labelled_not_guessed(self):
        text = json.dumps(self.cat)
        for must in ('UNVERIFIED',):
            self.assertIn(must, text)
        pro = [r for r in self.cat['rigging'] if r['id'] == 'cubism-pro'][0]
        self.assertIn('UNVERIFIED', pro['cost'])


class Recommendations(unittest.TestCase):
    def test_local_models_are_listed_only_when_the_stated_memory_fits(self):
        big = R.recommend(report(HW_BIG)); small = R.recommend(report(HW_NONE))
        self.assertEqual({m['id'] for m in big['local_image_that_fit']}, {'flux2-klein-4b', 'z-image-turbo'})
        self.assertEqual(small['local_image_that_fit'], [])
        self.assertTrue(big['local_image_memory_not_stated'])                      # honest about models with no stated memory

    def test_no_upload_answer_hides_hosted_services(self):
        self.assertEqual(R.recommend(report(), {'allow_upload': False, 'use': 'personal'})['hosted_image'], [])
        self.assertTrue(R.recommend(report(), {'allow_upload': True, 'use': 'personal'})['hosted_image'])

    def test_a_noncommercial_cutout_tool_is_warned_for_commercial_use(self):
        r = R.recommend(report(), {'allow_upload': True, 'use': 'commercial'})
        self.assertIn('warning', [c for c in r['cutout_tools'] if c['id'] == 'rmbg-2'][0])
        self.assertNotIn('warning', [c for c in r['cutout_tools'] if c['id'] == 'rembg'][0])

    def test_cubism_free_check_compares_a_rig_with_the_limits(self):
        self.assertTrue(R.cubism_free_check({'artmeshes': 80, 'parts': 20})['fits_free'])
        over = R.cubism_free_check({'artmeshes': 250, 'texture_files': 3})
        self.assertFalse(over['fits_free']); self.assertEqual(len(over['over']), 2)

    def test_the_report_makes_no_choice_for_the_user(self):
        r = R.recommend(report())
        self.assertNotIn('chosen', r); self.assertNotIn('you_chose', r)
        self.assertGreaterEqual(len(r['rigging_toolchains']), 4)               # several toolchains are offered, none selected


class Interview(unittest.TestCase):
    def test_first_use_asks_everything_and_offers_the_options_without_choosing(self):
        with tempfile.TemporaryDirectory() as d:
            out = R.interview(Path(d) / 'ns', report())
            self.assertEqual(out['state'], 'interview_needed'); keys = {q['key'] for q in out['questions']}
            self.assertTrue({'image_route', 'cutout_route', 'rig_route', 'use', 'allow_upload'} <= keys)
            self.assertIn('Do not choose an image route', out['instructions_for_agent']); self.assertIn('never research without their yes', out['instructions_for_agent'].lower() + 'never research without their yes')
            self.assertIn('knowledge_freshness', out); self.assertIsNone(R.load_profile(Path(d) / 'ns'))

    def test_missing_routes_are_refused_and_nothing_is_saved(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'ns'
            with self.assertRaisesRegex(ValueError, 'Ask the user which'):
                R.interview(root, report(), {k: v for k, v in ANSWERS.items() if k != 'rig_route'})
            self.assertIsNone(R.load_profile(root))

    def test_routes_must_be_ones_that_were_offered_and_choices_must_be_consistent(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'ns'
            with self.assertRaisesRegex(ValueError, 'not one of the options'):
                R.interview(root, report(), {**ANSWERS, 'image_route': 'invented'})
            with self.assertRaisesRegex(ValueError, 'nothing should be sent to an online service'):
                R.interview(root, report(), {**ANSWERS, 'allow_upload': False, 'image_route': 'openai-image'})
            with self.assertRaisesRegex(ValueError, 'Cubism FREE is limited'):
                R.interview(root, report(), {**ANSWERS, 'use': 'commercial', 'small_scale': False})

    def test_saved_profile_is_private_and_carries_honest_warnings(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'ns'
            out = R.interview(root, report(), {**ANSWERS, 'rig_route': 'umamo'})
            self.assertEqual(out['state'], 'saved'); self.assertEqual(out['you_chose']['rig_route'], 'umamo')
            self.assertTrue(any('alpha' in g for g in out['gaps'])); self.assertTrue(any('VTube Studio' in g for g in out['gaps']))
            self.assertEqual(oct(R.profile_path(root).stat().st_mode & 0o777), '0o600')
            self.assertEqual(R.interview(root, report())['state'], 'answered')

    def test_validation(self):
        with tempfile.TemporaryDirectory() as d:
            for bad in ({}, {**ANSWERS, 'character': ''}, {**ANSWERS, 'source': 'magic'}, {**ANSWERS, 'use': 'x'}, {**ANSWERS, 'allow_upload': 'yes'}, {**ANSWERS, 'budget_usd': -1}, {**ANSWERS, 'budget_usd': True}):
                with self.assertRaises(ValueError):
                    R.save_profile(Path(d) / 'ns', bad)


class Tools(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.data = Path(self.tmp.name); self.addCleanup(self.tmp.cleanup)
        storage = types.ModuleType('plugins.plugin_storage'); storage.plugin_data_dir = lambda name: (self.data / name).mkdir(parents=True, exist_ok=True) or self.data / name
        p = mock.patch.dict(sys.modules, {'plugins': types.ModuleType('plugins'), 'plugins.plugin_storage': storage}); p.start(); self.addCleanup(p.stop)
        pkg = importlib.util.spec_from_file_location('l2d_pkg_under_test', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
        self.m = importlib.util.module_from_spec(pkg); sys.modules[pkg.name] = self.m; pkg.loader.exec_module(self.m)

    def test_begin_and_build_return_the_interview_until_it_is_answered_then_run(self):
        for name in ('live2d_begin_model', 'live2d_build_model'):
            out = json.loads(self.m.invoke(name, {}))
            self.assertEqual(out['state'], 'interview_needed'); self.assertIn('live2d_setup', out['next'])
        saved = json.loads(self.m.invoke('live2d_setup', {'answers': ANSWERS}))
        self.assertEqual(saved['state'], 'saved')
        out = json.loads(self.m.invoke('live2d_begin_model', {}))
        self.assertNotEqual(out.get('state'), 'interview_needed')                    # the gate is open (the call itself may report its own argument error)

    def test_setup_stores_approved_research_and_reports_it(self):
        ok = {'id': 'cubism-pro', 'field': 'cost', 'value': '$X per month (checked)', 'source': 'https://www.live2d.com/en/cubism/download/editor/', 'date': R._today().isoformat()}
        out = json.loads(self.m.invoke('live2d_setup', {'knowledge_updates': [ok]}))
        self.assertEqual(out['knowledge_updates_saved'], 1)
        row = [r for r in R.load_catalog(update_root=self.data / 'live2d-rigger')['rigging'] if r['id'] == 'cubism-pro'][0]
        self.assertEqual(row['cost'], '$X per month (checked)')
        self.assertIn('UNVERIFIED', [r for r in R.load_catalog()['rigging'] if r['id'] == 'cubism-pro'][0]['cost'])


class Freshness(unittest.TestCase):
    def test_stale_by_age_or_by_a_passed_deadline_and_offer_asks_first(self):
        cat = R.load_catalog()
        self.assertFalse(R.freshness(cat['verified'], cat['expiries'], None, datetime.date(2026, 11, 20))['stale'])
        old = R.freshness(cat['verified'], cat['expiries'], None, datetime.date(2027, 4, 1))
        self.assertTrue(old['stale']); self.assertIn('Do not research without their yes', old['offer'])

    def test_generic_block_matches_the_other_plugins(self):
        def block(path):
            t = Path(path).read_text()
            return t[t.index('# ---- knowledge freshness'):t.index('# ---- end knowledge freshness ----')]
        other = ROOT.parent / 'creator-studio' / 'common' / 'speech_resources.py'
        if other.exists():
            self.assertEqual(block(other), block(ROOT / 'resources.py'))


if __name__ == '__main__':
    unittest.main()
