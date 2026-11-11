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
            app.layer(ident,'Backing','Complete original backing',str(image),'Synthetic fixture only',complete_part=True);app.rig(ident,'// fixture, not a working rig')
            with self.assertRaisesRegex(ValueError,'unique'):app.layer(ident,'Backing','dup',str(image),'x',complete_part=True)
            other=root/'small.png';Image.new('RGBA',(10,10),(1,2,3,200)).save(other)
            with self.assertRaisesRegex(ValueError,'share one canvas'):app.layer(ident,'Eye_L','eye',str(other),'x',complete_part=True)
            with self.assertRaisesRegex(ValueError,'both integer'):app.layer(ident,'Eye_L','eye',str(other),'x',complete_part=True,x=3)
            self.assertEqual(app.layer(ident,'Eye_L','eye',str(other),'x',complete_part=True,x=3,y=4)['offset'],[3,4])
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

class StaticAdapterTests(unittest.TestCase):
    def test_missing_toolchain_and_static_contract(self):
        from unittest.mock import patch
        from production_fixture.umamo_adapter import toolchain
        with patch.dict('os.environ', {'PATH': ''}, clear=True):
            with self.assertRaisesRegex(ValueError, 'LIVE2D_UMAMO_COMPILER_CLASSPATH'):
                toolchain()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); app=Production(root); ident=app.begin('Fixture','Synthetic shapes')['model_id']
            img=root/'shape.png'; Image.new('RGBA',(20,20),(2,3,4,128)).save(img)
            app.layer(ident,'Shape','synthetic',str(img),'Synthetic test',complete_part=True)
            result=app.rig(ident)
            self.assertEqual(result['phase'],'static_export_prepared')
            self.assertIn('no deformers',result['notice'])
            with patch.dict('os.environ', {'PATH':''}, clear=True):
                with self.assertRaisesRegex(ValueError, 'Umamo authoring is unavailable'):
                    app.build(ident)
            self.assertFalse(app.status(ident)['accepted'])

    def test_import_flat_key_and_trim(self):
        with tempfile.TemporaryDirectory() as tmp:
            from PIL import ImageDraw
            root=Path(tmp);app=Production(root);ident=app.begin('Fixture','Synthetic')['model_id']
            img=Image.new('RGB',(20,20),(255,0,255));ImageDraw.Draw(img).rectangle((5,6,14,15),fill=(10,80,50));src=root/'opaque.png';img.save(src)
            with self.assertRaisesRegex(ValueError,'Opaque part'):app.layer(ident,'Shape','test',str(src),'reviewed',complete_part=True)
            row=app.layer(ident,'Shape','test',str(src),'reviewed',complete_part=True,x=10,y=20,key_color=[],trim=True)
            self.assertEqual(row['offset'],[15,26]);self.assertEqual(row['dimensions'],(10,10));self.assertTrue(Path(row['cutout_preview']).is_file())
            with Image.open(src) as original:self.assertEqual(original.mode,'RGB')

    def test_arrange_requires_a_complete_permutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);app=Production(root);ident=app.begin('Fixture','Synthetic')['model_id'];image=root/'s.png';Image.new('RGBA',(10,10),(0,0,0,128)).save(image)
            for name in ('face','hair'):app.layer(ident,name,'fixture',str(image),'reviewed',complete_part=True)
            with self.assertRaisesRegex(ValueError,'exactly once'):app.arrange(ident,['face','face'])
            self.assertEqual(app.arrange(ident,['hair','face'])['back_to_front'],['hair','face'])
            self.assertEqual([x['name'] for x in app.status(ident)['layers']],['hair','face'])

    def test_placement_keeps_art_and_marks_build_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);app=Production(root);ident=app.begin('Fixture','Synthetic')['model_id'];image=root/'s.png';Image.new('RGBA',(20,20),(0,0,0,128)).save(image)
            row=app.layer(ident,'face','fixture',str(image),'reviewed',complete_part=True);p,data=app.load(ident);data['model_path']='built.model3.json'
            from production_fixture.production import save
            save(p/'model-project.json',data)
            with self.assertRaisesRegex(ValueError,'fit'):app.place_layer(ident,'face',19,19,1)
            app.place_layer(ident,'face',3,3,.5)
            self.assertTrue(app.status(ident)['build_stale'])
            self.assertEqual(app.status(ident)['layers'][0]['sha256'],row['sha256'])
            with self.assertRaisesRegex(ValueError,'rebuild'):app.motion(ident,['producer','{project}','{output}'])

    def test_canvas_expansion_preserves_parts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);app=Production(root);ident=app.begin('Fixture','Synthetic')['model_id'];image=root/'s.png';Image.new('RGBA',(20,20),(0,0,0,128)).save(image)
            app.layer(ident,'face','fixture',str(image),'reviewed',complete_part=True)
            with self.assertRaisesRegex(ValueError,'fit'):app.set_canvas(ident,10,10)
            app.set_canvas(ident,20,30)
            self.assertEqual(app.status(ident)['canvas'],[20,30])

    def test_roll_prototype_requires_face_and_discloses_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);app=Production(root);ident=app.begin('Fixture','Synthetic')['model_id'];image=root/'s.png';Image.new('RGBA',(20,20),(0,0,0,128)).save(image)
            app.layer(ident,'hair','hair',str(image),'reviewed',complete_part=True)
            with self.assertRaisesRegex(ValueError,'face layer'):app.rig(ident,'prototype-roll')
            app.layer(ident,'face','face',str(image),'reviewed',complete_part=True)
            result=app.rig(ident,'prototype-roll')
            self.assertEqual(result['phase'],'prototype_roll_prepared')
            self.assertIn('no XY turns',result['notice'])

    def test_experimental_hair_physics_sidecar(self):
        from production_fixture.umamo_adapter import add_hair_physics
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'prototype-has-hair.txt').write_text('true');(root/'Model.model3.json').write_text(json.dumps({'FileReferences':{'Moc':'Model.moc3'}}))
            add_hair_physics(root)
            model=json.loads((root/'Model.model3.json').read_text());doc=json.loads((root/model['FileReferences']['Physics']).read_text())
            setting=doc['PhysicsSettings'][0]
            self.assertEqual(setting['Input'][0]['Source']['Id'],'ParamAngleZ')
            self.assertEqual(setting['Output'][0]['Destination']['Id'],'ParamHairBack')
            self.assertFalse((root/'prototype-has-hair.txt').exists())

    def test_complete_part_attestation_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);app=Production(root);ident=app.begin('Fixture','Synthetic')['model_id'];image=root/'s.png';Image.new('RGBA',(10,10),(0,0,0,128)).save(image)
            with self.assertRaisesRegex(ValueError,'flat portrait slice'):
                app.layer(ident,'face','face',str(image),'not verified')

    def test_default_layout_is_reviewable_before_applying(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);app=Production(root);ident=app.begin('Fixture','Synthetic')['model_id'];image=root/'s.png'
            Image.new('RGBA',(100,150),(0,0,0,0)).save(image)
            from PIL import ImageDraw
            with Image.open(image) as im:
                im=im.copy();ImageDraw.Draw(im).rectangle((35,15,65,45),fill=(20,80,60,255));im.save(image)
            app.layer(ident,'face','face',str(image),'reviewed',complete_part=True)
            app.layer(ident,'dress','dress',str(image),'reviewed',complete_part=True)
            before=app.status(ident)['layers'][1].get('placement')
            result=app.default_layout(ident)
            self.assertFalse(result['applied']);self.assertEqual(result['proposals'][0]['name'],'dress')
            self.assertEqual(app.status(ident)['layers'][1].get('placement'),before)

    def test_import_auto_layout_and_aligned_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            from PIL import ImageDraw
            root=Path(tmp);app=Production(root);ident=app.begin('Fixture','Synthetic')['model_id']
            base=root/'face.png';im=Image.new('RGBA',(200,300));ImageDraw.Draw(im).ellipse((70,20,130,80),fill=(20,70,90,255));im.save(base)
            app.layer(ident,'face','face',str(base),'reviewed',complete_part=True)
            small=root/'hair.png';im=Image.new('RGBA',(100,80));ImageDraw.Draw(im).rectangle((10,10,90,70),fill=(30,90,70,255));im.save(small)
            row=app.layer(ident,'back_hair','hair',str(small),'reviewed',complete_part=True)
            self.assertEqual(row['placement_source'],'role_default')
            self.assertIn('placement',row)
            row=app.layer(ident,'aligned','fixture',str(base),'reviewed',complete_part=True,aligned_to_reference=True)
            self.assertTrue(row['aligned_to_reference']);self.assertNotIn('placement',row)

    def test_registration_only_applies_above_threshold(self):
        from unittest.mock import patch
        import production_fixture.registration as registration
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);app=Production(root);ident=app.begin('Fixture','Synthetic')['model_id'];image=root/'s.png';Image.new('RGBA',(20,20),(10,20,30,128)).save(image)
            app.layer(ident,'face','face',str(image),'reviewed',complete_part=True)
            match={'score':.5,'threshold':.9,'accepted':False,'x':1,'y':2,'scale':.8,'visible_box':[1,2,17,18],'notice':'test'}
            with patch.object(registration,'register',return_value=match.copy()):self.assertFalse(app.register_layer(ident,'face',str(image))['applied'])
            self.assertNotIn('placement',app.status(ident)['layers'][0])
            match.update(score=.95,accepted=True)
            with patch.object(registration,'register',return_value=match.copy()):self.assertTrue(app.register_layer(ident,'face',str(image))['applied'])
            self.assertEqual(app.status(ident)['layers'][0]['placement']['x'],1)

    def test_same_canvas_edit_runs_registration_without_default_layout(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);app=Production(root);ident=app.begin('Fixture','Synthetic')['model_id'];app.set_canvas(ident,20,20)
            image=root/'s.png';Image.new('RGBA',(20,20),(10,20,30,128)).save(image)
            with patch.object(app,'register_layer',return_value={'accepted':False,'applied':False}) as check:
                row=app.layer(ident,'face','face',str(image),'reviewed',complete_part=True,same_canvas_edit=True,reference_path=str(image))
            check.assert_called_once();self.assertFalse(row['registration_result']['applied']);self.assertNotIn('placement',row)

    def test_rebuild_prototype_requires_builtin_recipe(self):
        with tempfile.TemporaryDirectory() as tmp:
            app=Production(Path(tmp));ident=app.begin('Fixture','Synthetic')['model_id']
            with self.assertRaisesRegex(ValueError,'built-in experimental prototype'):app.rebuild_prototype(ident)

    def test_clone_is_a_separate_working_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);app=Production(root);ident=app.begin('Fixture','Synthetic')['model_id'];image=root/'s.png';Image.new('RGBA',(20,20),(10,20,30,128)).save(image)
            app.layer(ident,'face','face',str(image),'reviewed',complete_part=True)
            copy=app.clone(ident,'Fixture copy')['model_id'];app.place_layer(copy,'face',2,2,.5)
            self.assertNotIn('placement',app.status(ident)['layers'][0]);self.assertEqual(app.status(copy)['cloned_from'],ident)

    def test_remove_layer_preserves_source_and_marks_build_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);app=Production(root);ident=app.begin('Fixture','Synthetic')['model_id'];image=root/'s.png';Image.new('RGBA',(20,20),(10,20,30,128)).save(image)
            row=app.layer(ident,'face','face',str(image),'reviewed',complete_part=True);p,data=app.load(ident);data['model_path']='built.model3.json'
            from production_fixture.production import save
            save(p/'model-project.json',data);app.remove_layer(ident,'face')
            self.assertTrue((p/row['path']).is_file());self.assertTrue(app.status(ident)['build_stale']);self.assertEqual(app.status(ident)['layers'],[])
