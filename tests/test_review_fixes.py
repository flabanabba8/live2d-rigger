"""Maintainer review asks: the model cannot choose what runs; subprocesses get a clean environment."""
import ast
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('l2d_review_pkg', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
pkg = importlib.util.module_from_spec(spec); sys.modules[spec.name] = pkg; spec.loader.exec_module(pkg)
from l2d_review_pkg.production import Production, TOOLS, clean_env, EXEC_KEYS

FORBIDDEN_ARGS = {'command_argv', 'java', 'classpath_file', 'viewer_dir', 'render_python', 'python_executable', 'executable'}


class Schemas(unittest.TestCase):
    def test_no_tool_lets_the_model_name_a_program_a_classpath_a_viewer_or_a_command(self):
        for name, (_d, props, _r, _m) in TOOLS.items():
            self.assertFalse(FORBIDDEN_ARGS & set(props), '%s accepts %s' % (name, FORBIDDEN_ARGS & set(props)))

    def test_every_tool_method_exists(self):
        for name, (_d, _p, _r, method) in TOOLS.items():
            self.assertTrue(callable(getattr(Production, method, None)), name)

    def test_begin_refuses_executable_resources(self):
        with tempfile.TemporaryDirectory() as d:
            app = Production(Path(d))
            for key in sorted(EXEC_KEYS):
                with self.assertRaisesRegex(ValueError, 'plugin settings'):
                    app.begin('x', 'a brief', {key: '/usr/bin/anything'})
            self.assertTrue(app.begin('x', 'a brief', {'style': 'flat colours'})['model_id'])


class OwnerSettings(unittest.TestCase):
    def project(self, d, settings=None):
        app = Production(Path(d), settings)
        return app, app.begin('Fixture', 'Synthetic')['model_id']

    def test_a_custom_rig_needs_the_owners_authoring_command_not_one_from_the_model(self):
        with tempfile.TemporaryDirectory() as d:
            app, mid = self.project(d)
            p, data = app.load(mid); data['rig_file'] = 'src/Rig.kt'; data['layers'] = []
            (p / 'model-project.json').write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'authoring_command'):
                app.build_configured(mid)

    def test_the_motion_command_comes_from_settings_only(self):
        with tempfile.TemporaryDirectory() as d:
            app, mid = self.project(d)
            with self.assertRaisesRegex(ValueError, 'motion_command'):
                app.motion_configured(mid)

    def test_argv_settings_must_be_json_arrays(self):
        with tempfile.TemporaryDirectory() as d:
            app = Production(Path(d), {'authoring_command': 'not json'})
            with self.assertRaisesRegex(ValueError, 'JSON array'):
                app._argv_setting('authoring_command')
            self.assertEqual(Production(Path(d), {'authoring_command': '["tool", "{project}", "{output}"]'})._argv_setting('authoring_command'), ['tool', '{project}', '{output}'])

    def test_umamo_paths_are_read_from_settings_and_checked(self):
        with tempfile.TemporaryDirectory() as d:
            java = Path(d) / 'java'; java.write_text('x'); lib = Path(d) / 'lib.jar'; lib.write_text('x')
            cp = Path(d) / 'cp.json'; cp.write_text(json.dumps({'compiler': [str(lib)], 'runtime': [str(lib)]}))
            app, mid = self.project(d, {'java': str(java), 'umamo_classpath_file': str(cp)})
            self.assertTrue(app.configure_umamo(mid)['configured'])
            res = app._toolchain_resources()
            self.assertEqual(res['java'], str(java)); self.assertEqual(res['umamo_compiler_classpath'], str(lib))
            bad = Path(d) / 'bad.json'; bad.write_text(json.dumps({'compiler': ['/nonexistent'], 'runtime': []}))
            with self.assertRaises(ValueError):
                Production(Path(d), {'umamo_classpath_file': str(bad)})._toolchain_resources()

    def test_the_renderer_reads_the_viewer_and_python_from_settings_not_arguments(self):
        with tempfile.TemporaryDirectory() as d:
            app, mid = self.project(d, {'viewer_dir': '/nonexistent', 'render_python': sys.executable})
            r = app.renderer({})
            self.assertFalse(r['ready']); self.assertTrue(any('viewer_dir' in m for m in r['missing']))


class CleanEnvironment(unittest.TestCase):
    def test_clean_env_drops_secrets(self):
        os.environ['OPENAI_API_KEY'] = 'sk-secret'; os.environ['GEMINI_API_KEY'] = 'g-secret'
        try:
            env = clean_env()
            self.assertNotIn('OPENAI_API_KEY', env); self.assertNotIn('GEMINI_API_KEY', env); self.assertIn('PATH', env)
        finally:
            del os.environ['OPENAI_API_KEY']; del os.environ['GEMINI_API_KEY']

    def test_every_subprocess_call_in_the_plugin_passes_an_env(self):
        missing = []
        for f in ROOT.glob('*.py'):
            tree = ast.parse(f.read_text())
            for n in ast.walk(tree):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == 'subprocess' and n.func.attr in ('run', 'Popen', 'check_output', 'check_call', 'call'):
                    if not any(k.arg == 'env' or k.arg is None for k in n.keywords):
                        missing.append('%s:%d' % (f.name, n.lineno))
        self.assertEqual(missing, [])


class ScriptsAreDefinedBeforeTheyRun(unittest.TestCase):
    def test_every_helper_in_a_script_started_by_the_plugin_is_defined_before_its_main_guard(self):
        """Found through Hermes: corebridge.py defined _clean_env after `if __name__ == '__main__': main()`, so every Core render died with a NameError."""
        for name in ('corebridge.py', 'umamo_adapter.py'):
            tree = ast.parse((ROOT / name).read_text())
            guard = [i for i, n in enumerate(tree.body) if isinstance(n, ast.If) and 'main' in ast.dump(n.test)]
            if not guard: continue
            late = [n.name for n in tree.body[guard[0] + 1:] if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
            self.assertEqual(late, [], name)


if __name__ == '__main__':
    unittest.main()
