import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('production_fixture',ROOT/'__init__.py',submodule_search_locations=[str(ROOT)])
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
from production_fixture.production import Production
class ProductionTests(unittest.TestCase):
    def test_actual_layer_rig_and_failed_native_outputs(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);app=Production(root);ident=app.begin('Original character','Complete editable character')['model_id'];image=root/'part.png';Image.new('RGBA',(20,20),(0,80,100,128)).save(image)
            app.layer(ident,'Backing','Complete original backing',str(image),'Synthetic fixture only');app.rig(ident,'// fixture, not a working rig')
            with self.assertRaisesRegex(ValueError,'unique'):app.layer(ident,'Backing','dup',str(image),'x')
            other=root/'small.png';Image.new('RGBA',(10,10),(1,2,3,200)).save(other)
            with self.assertRaisesRegex(ValueError,'share one canvas'):app.layer(ident,'Eye_L','eye',str(other),'x')
            with self.assertRaisesRegex(ValueError,'both integer'):app.layer(ident,'Eye_L','eye',str(other),'x',x=3)
            self.assertEqual(app.layer(ident,'Eye_L','eye',str(other),'x',x=3,y=4)['offset'],[3,4])
            with self.assertRaisesRegex(ValueError,'another agent'):app.build(ident,['codex','{project}','{output}'])
            def unsafe(p,argv,out,timeout):
                (out/'bad.model3.json').write_text(json.dumps({'FileReferences':{'Moc':'../escape.moc3','Textures':['missing.png']}}))
            with patch.object(app,'command',side_effect=unsafe):
                with self.assertRaisesRegex(ValueError,'unsafe or missing'):app.build(ident,['native','{project}','{output}'])
            p,data=app.load(ident);data['model_path']='fixture.model3.json'
            from production_fixture.production import save
            save(p/'model-project.json',data)
            def fake_video(p,argv,out,timeout):(out/'placeholder.mp4').write_bytes(b'not video')
            with patch.object(app,'command',side_effect=fake_video):
                with self.assertRaisesRegex(ValueError,'measured motion'):app.motion(ident,['native','{project}','{output}'])
            self.assertFalse(app.status(ident)['accepted']);self.assertNotEqual(app.status(ident)['phase'],'motion_review_pending')
if __name__=='__main__':unittest.main()
