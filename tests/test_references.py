import importlib.util,io,json,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('ref_fixture',ROOT/'__init__.py',submodule_search_locations=[str(ROOT)])
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
from ref_fixture.references import References,BASE,CATALOG

def sample_zip(extra=None):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w')as z:
        z.writestr('s/s.model3.json',json.dumps({'Version':3,'FileReferences':{'Moc':'s.moc3','Textures':['t.png'],'Physics':'s.physics3.json','DisplayInfo':'s.cdi3.json','Expressions':[{'Name':'a','File':'a.exp3.json'}],'Motions':{'Idle':[{'File':'m.motion3.json'}]}}}))
        for n,c in{'s.moc3':b'MOC3','t.png':b'x','a.exp3.json':'{}','m.motion3.json':'{}'}.items():z.writestr('s/'+n,c)
        z.writestr('s/s.cdi3.json',json.dumps({'Parameters':[{'Id':'ParamAngleX','GroupId':'G','Name':'Angle X'}],'ParameterGroups':[{'Name':'Face'}],'Parts':[{'Id':'PartHead','Name':'Head'}]}))
        z.writestr('s/s.physics3.json',json.dumps({'PhysicsSettings':[{'Id':'P1','Input':[{'Source':{'Id':'ParamAngleX'}}],'Output':[{'Destination':{'Id':'ParamHairFront'}}],'Vertices':[{},{}]}]}))
        for n,c in(extra or{}).items():z.writestr(n,c)
    return b.getvalue()

class ReferenceTests(unittest.TestCase):
    def test_licence_gate_fetch_reuse_and_summary(self):
        calls=[]
        def fake(url):calls.append(url);return sample_zip()
        with tempfile.TemporaryDirectory()as tmp:
            r=References(tmp,fake)
            self.assertFalse(any(s['present']for s in r.list()['samples']))
            with self.assertRaisesRegex(ValueError,'licence'):r.fetch('hiyori',False)
            self.assertEqual(calls,[])
            self.assertEqual(r.fetch('hiyori',True)['status'],'fetched');self.assertTrue(calls[0].startswith(BASE))
            self.assertEqual(r.fetch('hiyori',True)['status'],'already_present');self.assertEqual(len(calls),1)
            s=r.summarize('hiyori')
            self.assertEqual(s['display_info']['parameters'][0]['id'],'ParamAngleX');self.assertEqual(s['physics']['settings'][0]['particles'],2)
            self.assertEqual(s['motion_groups'],{'Idle':1});self.assertEqual(s['resource_check']['issues'],[])
            self.assertTrue(next(x for x in r.list()['samples']if x['sample_id']=='hiyori')['present'])
    def test_rejects_unknown_unsafe_and_non_model_archives(self):
        with tempfile.TemporaryDirectory()as tmp:
            with self.assertRaisesRegex(ValueError,'Unknown'):References(tmp,lambda u:b'').fetch('evil',True)
            with self.assertRaisesRegex(ValueError,'Unsafe path'):References(tmp,lambda u:sample_zip({'../escape.txt':'x'})).fetch('mark',True)
            b=io.BytesIO()
            with zipfile.ZipFile(b,'w')as z:z.writestr('a.txt','x')
            with self.assertRaisesRegex(ValueError,'no model3'):References(tmp,lambda u:b.getvalue()).fetch('ren',True)
            self.assertFalse((Path(tmp)/'reference-samples'/'mark').exists());self.assertEqual(list((Path(tmp)/'reference-samples').glob('*.tmp')),[])
            with self.assertRaisesRegex(ValueError,'not present'):References(tmp).summarize('haru')
    def test_catalog_urls_are_official_host_only(self):
        for name,page,z in CATALOG.values():self.assertTrue((BASE+z).startswith('https://cubism.live2d.com/sample-data/bin/'))
if __name__=='__main__':unittest.main()
