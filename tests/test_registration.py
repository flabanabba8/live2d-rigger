import importlib.util,unittest
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('registration_fixture',ROOT/'registration.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class RegistrationTests(unittest.TestCase):
    def test_textured_part_is_registered_and_absent_part_rejected(self):
        try:import numpy
        except ImportError:self.skipTest('NumPy unavailable')
        ref=Image.new('RGB',(120,100),(240,230,220));d=ImageDraw.Draw(ref)
        d.rectangle((43,38,66,56),fill=(30,90,150));d.ellipse((47,41,61,53),fill=(240,180,40));d.line((43,38,66,56),fill=(10,20,30),width=2)
        part=Image.new('RGBA',(32,27));part.paste(ref.crop((43,38,67,57)).convert('RGBA'),(4,3))
        result=module.register(ref,part)
        self.assertTrue(result['accepted'],result)
        self.assertAlmostEqual(result['x'],39,delta=2);self.assertAlmostEqual(result['y'],35,delta=2);self.assertAlmostEqual(result['scale'],1,delta=.08)
        missing=Image.new('RGBA',(24,19),(230,20,200,255));result=module.register(ref,missing,threshold=.8)
        self.assertFalse(result['accepted'],result)

    def test_scaled_synthetic_part(self):
        try:import numpy
        except ImportError:self.skipTest('NumPy unavailable')
        part=Image.new('RGBA',(20,16));d=ImageDraw.Draw(part);d.rectangle((2,2,17,13),fill=(20,100,190,255));d.ellipse((5,4,13,10),fill=(230,160,40,255));d.line((2,2,17,13),fill=(15,30,35,255),width=2)
        ref=Image.new('RGBA',(100,80),(240,230,220,255));scaled=part.resize((26,21),Image.Resampling.LANCZOS);ref.alpha_composite(scaled,(38,24))
        result=module.register(ref.convert('RGB'),part,threshold=.8)
        self.assertTrue(result['accepted'],result)
        self.assertAlmostEqual(result['x'],38,delta=2);self.assertAlmostEqual(result['y'],24,delta=2);self.assertAlmostEqual(result['scale'],1.3,delta=.1)
