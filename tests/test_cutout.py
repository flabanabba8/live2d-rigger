import importlib.util, sys, unittest
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('cutout_fixture',ROOT/'cutout.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class CutoutTests(unittest.TestCase):
    def test_flat_key_and_edge_despill(self):
        im=Image.new('RGB',(20,20),(255,0,255));d=ImageDraw.Draw(im)
        d.rectangle((5,5,14,14),fill=(100,80,40));im.putpixel((4,8),(230,35,200))
        out,box,key=module.cutout(im,(255,0,255),18,80)
        self.assertEqual(out.getpixel((0,0))[3],0)
        self.assertEqual(out.getpixel((8,8)),(100,80,40,255))
        r,g,b,a=out.getpixel((4,8));self.assertTrue(0<a<255);self.assertLess(b,200)
        self.assertEqual(key,(255,0,255));self.assertEqual(box,(4,5,15,15))
    def test_checkerboard_refused_and_enclosed_hole_retained(self):
        im=Image.new('RGB',(20,20),(255,0,255));im.putpixel((0,0),(80,80,80))
        with self.assertRaisesRegex(ValueError,'not a flat'):module.cutout(im,(255,0,255))
        im=Image.new('RGB',(30,30),(255,0,255));d=ImageDraw.Draw(im);d.ellipse((3,3,26,26),fill=(20,60,100));d.ellipse((10,10,19,19),fill=(255,0,255))
        out,_,_=module.cutout(im,(255,0,255))
        self.assertEqual(out.getpixel((15,15))[3],0)
        self.assertEqual(out.info['cutout_holes'].getpixel((15,15)),255)
        self.assertIn((255,100,20), set(module.preview(im,out).getdata()))
    def test_colour_too_close_to_key_is_refused(self):
        im=Image.new('RGB',(30,30),(255,0,255));ImageDraw.Draw(im).rectangle((5,5,24,24),fill=(220,0,220))
        with self.assertRaisesRegex(ValueError,'Ambiguous key-colour band.*other key colour'):
            module.cutout(im,(255,0,255))

    def test_dark_key_colour_noise_is_removed_without_losing_part(self):
        im=Image.new('RGB',(50,50),(255,0,255));d=ImageDraw.Draw(im);d.rectangle((15,15,35,35),fill=(180,150,100));d.rectangle((2,2,6,6),fill=(150,20,150))
        out,_,_=module.cutout(im,(255,0,255))
        self.assertEqual(out.getpixel((4,4))[3],0)
        self.assertEqual(out.getpixel((25,25)),(180,150,100,255))
