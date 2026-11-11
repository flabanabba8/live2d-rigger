import hashlib,importlib.util,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('existing_fixture',ROOT/'__init__.py',submodule_search_locations=[str(ROOT)])
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
from existing_fixture.production import Production,TOOLS
from existing_fixture import corebridge

def make_model(folder):
    folder.mkdir();Image.new('RGBA',(8,8),(1,2,3,255)).save(folder/'t.png');(folder/'M.moc3').write_bytes(b'MOC3'+bytes(60))
    physics={'PhysicsSettings':[{'Id':'HairL','Input':[{'Source':{'Target':'Parameter','Id':'ParamAngleX'},'Weight':40}],'Output':[{'Destination':{'Target':'Parameter','Id':'ParamHairL1'},'Scale':2.0}],'Vertices':[{'Acceleration':1,'Mobility':1},{'Acceleration':1,'Mobility':.8}]},
                                 {'Id':'Skirt','Input':[{'Source':{'Target':'Parameter','Id':'ParamAngleX'},'Weight':10}],'Output':[{'Destination':{'Target':'Parameter','Id':'ParamSkirt'},'Scale':1.0}],'Vertices':[{'Acceleration':1,'Mobility':1},{'Acceleration':1,'Mobility':.8}]}]}
    (folder/'M.physics3.json').write_text(json.dumps(physics));(folder/'M.cdi3.json').write_text(json.dumps({'Parameters':[{'Id':'ParamAngleX'},{'Id':'ParamHairL1'}],'Parts':[]}))
    (folder/'M.model3.json').write_text(json.dumps({'Version':3,'FileReferences':{'Moc':'M.moc3','Textures':['t.png'],'Physics':'M.physics3.json','DisplayInfo':'M.cdi3.json'},'Groups':[{'Name':'EyeBlink','Ids':['ParamEyeLOpen']}]}))
    return folder/'M.model3.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class ExistingModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.model=make_model(self.root/'user-model');self.app=Production(self.root/'data')
        for k in('LIVE2D_SDK_VIEWER','LIVE2D_RENDER_PYTHON'):os.environ.pop(k,None)
    def tearDown(self):self.tmp.cleanup()
    def test_open_copies_and_never_touches_original(self):
        before={p.name:sha(p) for p in self.model.parent.iterdir()}
        r=self.app.open_existing('Test idol',str(self.model))
        self.assertEqual(r['phase'],'opened_existing');self.assertFalse(r['renderer']['ready']);self.assertEqual(self.app.status(r['model_id'])['moc_sha256'],before['M.moc3'])
        p,data=self.app.load(r['model_id']);(p/data['model_path']).parent.joinpath('M.physics3.json').write_text('{}')
        self.assertEqual(before,{q.name:sha(q) for q in self.model.parent.iterdir()})
    def test_open_accepts_the_folder(self):
        self.assertEqual(self.app.open_existing('x',str(self.model.parent))['phase'],'opened_existing')
    def test_open_relative_name_error_tells_the_agent_what_to_do(self):
        with self.assertRaisesRegex(ValueError,'FULL path'):self.app.open_existing('x','no-such-folder')
    def test_open_refuses_bad_input(self):
        with self.assertRaisesRegex(ValueError,'model3.json'):self.app.open_existing('x',str(self.root/'nope.txt'))
        (self.model.parent/'t.png').unlink()
        with self.assertRaisesRegex(ValueError,'missing or unsafe'):self.app.open_existing('x',str(self.model))
    def test_open_refuses_links(self):
        os.symlink(self.model.parent/'t.png',self.model.parent/'link.png')
        with self.assertRaisesRegex(ValueError,'links'):self.app.open_existing('x',str(self.model))
    def test_inspect_plain_and_core_unavailable(self):
        i=self.app.open_existing('Test idol',str(self.model))['model_id'];r=self.app.inspect_model(i)
        self.assertEqual([g['group'] for g in r['physics']],['HairL','Skirt']);self.assertEqual(r['physics'][0]['moves'][0]['strength'],2.0);self.assertIn('unavailable',r['core']);self.assertEqual(r['textures'],1)
    def test_adjust_physics_is_not_compounded_and_restorable(self):
        i=self.app.open_existing('Test idol',str(self.model))['model_id']
        r=self.app.adjust_physics(i,output_scale=2,follow_through=1.5,groups=['hair'],note='hair barely moves');r=self.app.adjust_physics(i,output_scale=2,follow_through=1.5,groups=['hair'])
        p,data=self.app.load(i);doc=json.loads((p/data['model_path']).parent.joinpath('M.physics3.json').read_text())
        self.assertEqual(r['changed_groups'],['HairL']);self.assertEqual(doc['PhysicsSettings'][0]['Output'][0]['Scale'],4.0);self.assertEqual(doc['PhysicsSettings'][0]['Vertices'][1]['Acceleration'],1.5);self.assertEqual(doc['PhysicsSettings'][1]['Output'][0]['Scale'],1.0)
        with self.assertRaisesRegex(ValueError,'between'):self.app.adjust_physics(i,output_scale=50)
        with self.assertRaisesRegex(ValueError,'matched'):self.app.adjust_physics(i,groups=['wing'])
        self.app.adjust_physics(i,restore_original=True);self.assertEqual(sha((p/data['model_path']).parent/'M.physics3.json'),sha(self.model.parent/'M.physics3.json'))
    def test_adjust_requires_existing_model(self):
        i=self.app.begin('New','brief')['model_id']
        with self.assertRaisesRegex(ValueError,'existing model'):self.app.adjust_physics(i)
    def test_render_clip_requires_ready_renderer_then_records_real_video(self):
        i=self.app.open_existing('Test idol',str(self.model))['model_id']
        with self.assertRaisesRegex(ValueError,'not ready'):self.app.render_clip(i,'before')
        def fake(p,argv,out,timeout):
            self.assertIn('corebridge.py',argv[1]);self.assertEqual(argv[2],'render');self.assertTrue(argv[3].startswith('{project}/'));self.assertTrue((p/argv[3][len('{project}/'):]).is_file());subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=black:s=64x64:d=1:r=10','-pix_fmt','yuv420p',str(out/'motion.mp4')],check=True);(out/'report.json').write_text(json.dumps({'measured':{'eye_close_parameter_crossings':2}}))
        ready={'ready':True,'missing':[],'viewer_dir':'/v','python':sys.executable}
        with patch.object(self.app,'renderer',return_value=ready),patch.object(self.app,'command',side_effect=fake):
            r=self.app.render_clip(i,'before');self.app.adjust_physics(i,output_scale=2);r2=self.app.render_clip(i,'after')
        clips=self.app.status(i)['clips'];self.assertEqual([c['label'] for c in clips],['before','after']);self.assertNotEqual(clips[0]['physics_sha256'],clips[1]['physics_sha256']);self.assertTrue(r['videos']);self.assertEqual(r['measured_movement'],{'eye_close_parameter_crossings':2});self.assertIn('not proof of visible motion',r['measurement_notice']);self.assertIn('inspect the frames',r['measurement_notice'])
    def test_measure_reports_real_movement(self):
        frames=[{'ParamAngleX':a,'ParamEyeLOpen':o,'ParamEyeROpen':o,'ParamHairL1':h}for a,o,h in((0,1,0),(10,1,.2),(-12,0,-.5),(0,1,0),(5,0,.1),(0,1,0))]
        m=corebridge.measure(frames,30);self.assertEqual(m['head_turn_left_right_degrees'],[-12,10]);self.assertEqual(m['eye_close_parameter_crossings'],2);self.assertEqual(m['hair_swing_strength_0_to_1'],.5);self.assertNotIn('skirt_swing_0_to_1',m);self.assertNotIn('eye_close_parameter_crossings',corebridge.measure([{'ParamAngleX':0}],30))
    def test_tools_registered(self):
        for n in('live2d_open_model','live2d_inspect_model','live2d_adjust_physics','live2d_render_clip'):self.assertIn(n,TOOLS)
    def test_standard_pose_loops_and_is_deterministic(self):
        a=corebridge.standard_pose(0,8);b=corebridge.standard_pose(8-1e-9,8);self.assertAlmostEqual(a['ParamAngleX'],b['ParamAngleX'],places=3);self.assertEqual(corebridge.standard_pose(2.2,8),corebridge.standard_pose(2.2,8))
        self.assertLessEqual(max(abs(corebridge.standard_pose(t/10,8)['ParamAngleX']) for t in range(80)),26.01)
class MotionTests(unittest.TestCase):
    setUp=ExistingModelTests.setUp;tearDown=ExistingModelTests.tearDown
    def test_write_motion_validates_clamps_registers_and_checks(self):
        i=self.app.open_existing('Test idol',str(self.model))['model_id']
        tracks=[{'parameter':'ParamAngleX','wave':'sine','center':0,'amplitude':18,'cycles':2},{'parameter':'ParamHairL1','wave':'blink','at':[1,3]}]
        with self.assertRaisesRegex(ValueError,'Unknown parameter'):self.app.write_motion(i,'alive',[{'parameter':'ParamNope','wave':'sine','center':0,'amplitude':1,'cycles':1}])
        with self.assertRaisesRegex(ValueError,'whole number'):self.app.write_motion(i,'alive',[{'parameter':'ParamAngleX','wave':'sine','center':0,'amplitude':1,'cycles':1.5}])
        with patch.object(self.app,'_core_ranges',return_value={'ParamAngleX':(-30,30),'ParamHairL1':(-1,1)}):
            r=self.app.write_motion(i,'alive',[{'parameter':'ParamAngleX','wave':'sine','center':0,'amplitude':45,'cycles':2},{'parameter':'ParamHairL1','wave':'blink','at':[1,3]}],seconds=4,fps=15)
        self.assertEqual(r['values_limited_to_range'],[{'parameter':'ParamAngleX','range':[-30,30]}]);self.assertEqual(r['check']['errors'],[]);self.assertEqual(r['check']['curves'],2)
        p,data=self.app.load(i);folder=(p/data['model_path']).parent;doc=json.loads((folder/'motions/alive.motion3.json').read_text())
        self.assertEqual(doc['Meta']['CurveCount'],2);self.assertTrue(doc['Meta']['Loop']);self.assertEqual(json.loads((folder/'M.model3.json').read_text())['FileReferences']['Motions']['Idle'],[{'File':'motions/alive.motion3.json'}])
        self.assertAlmostEqual(corebridge.motion_pose(doc,0)['ParamAngleX'],corebridge.motion_pose(doc,4)['ParamAngleX'],places=3);self.assertAlmostEqual(max(abs(corebridge.motion_pose(doc,t/10)['ParamAngleX'])for t in range(40)),30,places=1)
        self.assertLess(corebridge.motion_pose(doc,1)['ParamHairL1'],0.01)
        self.app.write_motion(i,'alive',tracks[:1],seconds=4)
        (folder/'motions/orig.motion3.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'already exists'):self.app.write_motion(i,'orig',tracks[:1],seconds=4)
    def test_motion_names_resolve_for_rendering(self):
        i=self.app.open_existing('Test idol',str(self.model))['model_id'];p,data=self.app.load(i);model=p/data['model_path']
        self.assertEqual(self.app._motion_arg(model.parent,json.loads(model.read_text()),None),'standard');self.assertEqual(self.app._motion_arg(model.parent,json.loads(model.read_text()),'rest'),'rest')
        s=json.loads(model.read_text());s['FileReferences']['Motions']={'Idle':[{'File':'motions/i.motion3.json'}]};(model.parent/'motions').mkdir(exist_ok=True);(model.parent/'motions/i.motion3.json').write_text('{}')
        self.assertTrue(self.app._motion_arg(model.parent,s,None).endswith('i.motion3.json'))
        with self.assertRaisesRegex(ValueError,'No motion called'):self.app._motion_arg(model.parent,json.loads(model.read_text()),'../x')
if __name__=='__main__':unittest.main()

class DomainCheckTests(unittest.TestCase):
    def test_domain_check_detects_nonfinite_geometry(self):
        from unittest.mock import patch
        class Page:
            def evaluate(self,script,arg=None):
                if script=='rig.parameters':return [{'id':'ParamA','min':-1,'default':0,'max':1}]
                if arg and arg.get('ParamA')==1:return [{'positions':[float('nan')],'opacity':1}]
                return [{'positions':[0.0],'opacity':1}]
        class Session:
            page=Page();moc_sha256='fixture'
            def __init__(self,*args):pass
            def close(self):pass
        with patch.object(corebridge,'Session',Session):
            with self.assertRaisesRegex(RuntimeError,'Non-finite'):corebridge.domains('unused','unused')

class BuiltMotionTests(unittest.TestCase):
    setUp=ExistingModelTests.setUp
    tearDown=ExistingModelTests.tearDown
    def test_newly_built_project_can_write_motion(self):
        from existing_fixture.production import save
        i=self.app.open_existing('Test idol',str(self.model))['model_id'];p,data=self.app.load(i);data['origin']='created';save(p/'model-project.json',data)
        result=self.app.write_motion(i,'TestBuilt',[{'parameter':'ParamAngleX','wave':'sine','center':0,'amplitude':5,'cycles':1}])
        self.assertEqual(result['motion'],'TestBuilt')
