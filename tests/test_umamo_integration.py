"""Optional real producer test: set LIVE2D_TEST_INTEGRATION=1 and toolchain env vars."""
import importlib.util, json, os, sys, tempfile, unittest
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('umamo_test_plugin',ROOT/'__init__.py',submodule_search_locations=[str(ROOT)])
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
from umamo_test_plugin.production import Production

@unittest.skipUnless(os.environ.get('LIVE2D_TEST_INTEGRATION')=='1','explicit configured Umamo integration test only')
class UmamoIntegration(unittest.TestCase):
    def test_synthetic_layers_compile_prototype(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);app=Production(root);ident=app.begin('Synthetic','Abstract shapes only')['model_id'];app.set_canvas(ident,128,128)
            for i,name in enumerate(('back_hair','face','body','eye_combined_left','eye_combined_right','mouth_inside')):
                im=Image.new('RGBA',(128,128));ImageDraw.Draw(im).ellipse((10+i,10,90+i,100),fill=(15,80+i*15,80,255));source=root/(name+'.png');im.save(source)
                app.layer(ident,name,name,str(source),'Synthetic fixture',x=0,y=0,complete_part=True)
            app.rig(ident,'prototype-roll');result=app.build(ident)
            model=Path(result['model_path']);settings=json.loads(model.read_text())
            self.assertEqual((model.parent/settings['FileReferences']['Moc']).read_bytes()[:4],b'MOC3')
            self.assertTrue((model.parent/settings['FileReferences']['Physics']).is_file())
            self.assertEqual(result['phase'],'compiled_needs_core_and_motion_review')
