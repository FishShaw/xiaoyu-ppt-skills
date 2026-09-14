"""Adversarial CLI tests. Synthetic packages test audit logic, not Office validity."""
import os
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from xml.etree import ElementTree as ET

SKILL = Path(os.environ.get('XIAOYU_TEST_SKILL', str(Path(__file__).resolve().parents[1] / 'skills' / 'xiaoyu-ppt')))
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def shape(n, label, x, y=2, w=1, h=1, preset='rect', arrow=False, rot=0):
    return f'''<p:sp><p:nvSpPr><p:cNvPr id="{n}" name="item{n}"/></p:nvSpPr><p:spPr>
    <a:xfrm rot="{rot}"><a:off x="{round(x*914400)}" y="{round(y*914400)}"/>
    <a:ext cx="{round(w*914400)}" cy="{round(h*914400)}"/></a:xfrm>
    <a:prstGeom prst="{preset}"/><a:ln>{'<a:tailEnd type="triangle"/>' if arrow else ''}</a:ln></p:spPr>
    <p:txBody><a:p><a:r><a:rPr typeface="Arial"/><a:t>{label}</a:t></a:r></a:p></p:txBody></p:sp>'''


def slide(order=('A','B','C'), obstacle=False, rotation=0, bent=False, duplicate=False, grouped=False, arrows=True):
    content = ''.join(shape(i+1, label, 1+i*2, rot=rotation if i==0 else 0) for i,label in enumerate(order))
    content += shape(10,'',2,2.5,1,0,'bentConnector3' if bent else 'line',arrows)
    content += shape(11,'',4,2.5,1,0,'line',arrows)
    if obstacle:
        content += shape(12,'obstacle',2.2,2.3,.6,.4)
    if duplicate:
        content += shape(13,'A',1,4)
    if grouped:
        content = '<p:grpSp>' + content + '</p:grpSp>'
    return f'<p:sld xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree>{content}</p:spTree></p:cSld></p:sld>'.encode()


def package(path, slides=None, order=None, extra=None, width=13.333333, height=7.5):
    slides = slides or [slide()]
    order = order or list(range(1,len(slides)+1))
    pres = f'<p:presentation xmlns:p="{P}" xmlns:r="{R}"><p:sldIdLst>'
    pres += ''.join(f'<p:sldId id="{255+i}" r:id="rId{i}"/>' for i in order)
    pres += f'</p:sldIdLst><p:sldSz cx="{round(width*914400)}" cy="{round(height*914400)}"/></p:presentation>'
    rels = '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    rels += ''.join(f'<Relationship Id="rId{i}" Type="{R}/slide" Target="slides/slide{i}.xml"/>' for i in range(1,len(slides)+1))
    rels += '</Relationships>'
    parts = {'ppt/presentation.xml':pres.encode(), 'ppt/_rels/presentation.xml.rels':rels.encode()}
    parts.update({f'ppt/slides/slide{i+1}.xml':s for i,s in enumerate(slides)})
    parts.update(extra or {})
    with zipfile.ZipFile(path,'w') as z:
        for name,data in parts.items():
            z.writestr(name,data)


class Regression(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)
        self.deck = self.dir/'deck.pptx'
        package(self.deck)

    def tearDown(self):
        self.temp.cleanup()

    def run_tool(self, script, *args):
        return subprocess.run([sys.executable,str(SKILL/'scripts'/script),*map(str,args)],capture_output=True,text=True)

    def audit(self,*args):
        r = self.run_tool('audit_presentation.py',self.deck,*args)
        return r, json.loads(r.stdout) if r.stdout.strip().startswith('{') else {}

    def test_valid_chain(self):
        r,_=self.audit('--chain','A|B|C'); self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_reversed_semantic_order_rejected(self):
        package(self.deck,[slide(('C','B','A'))])
        r,_=self.audit('--chain','A|B|C'); self.assertNotEqual(r.returncode,0)

    def test_duplicate_label_rejected(self):
        package(self.deck,[slide(duplicate=True)])
        r,_=self.audit('--chain','A|B|C'); self.assertNotEqual(r.returncode,0)

    def test_text_obstacle_rejected(self):
        package(self.deck,[slide(obstacle=True)])
        r,_=self.audit('--chain','A|B|C'); self.assertNotEqual(r.returncode,0)

    def test_rotation_not_silently_passed(self):
        package(self.deck,[slide(rotation=60000)])
        r,_=self.audit('--chain','A|B|C'); self.assertNotEqual(r.returncode,0)

    def test_group_not_silently_passed(self):
        package(self.deck,[slide(grouped=True)])
        r,_=self.audit('--chain','A|B|C'); self.assertNotEqual(r.returncode,0)

    def test_missing_arrow_rejected(self):
        package(self.deck,[slide(arrows=False)])
        r,_=self.audit('--chain','A|B|C'); self.assertNotEqual(r.returncode,0)

    def test_bent_connector_not_silently_passed(self):
        data=slide(bent=True).replace(b'<p:sp>',b'<p:cxnSp>').replace(b'</p:sp>',b'</p:cxnSp>')
        package(self.deck,[data]); r,_=self.audit('--chain','A|B|C'); self.assertNotEqual(r.returncode,0)

    def test_four_three_allowed(self):
        package(self.deck,width=10,height=7.5)
        r,_=self.audit(); self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_wrong_requested_aspect_rejected(self):
        r,_=self.audit('--aspect','4:3'); self.assertNotEqual(r.returncode,0)

    def test_empty_chain_rejected(self):
        r,_=self.audit('--chain','A'); self.assertNotEqual(r.returncode,0)

    def test_infinite_tolerance_rejected(self):
        r,_=self.audit('--chain','A|B|C','--tolerance','inf'); self.assertNotEqual(r.returncode,0)

    def test_xml_reorder_uses_display_order(self):
        package(self.deck,[slide(),slide(('D','E','F'))],order=[2,1])
        r,data=self.audit('--chain','A|B|C'); self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(data['checks']['geometry_chain']['slide'],2)

    def test_master_and_media_mutations_detected(self):
        canonical=self.dir/'canonical.pptx'
        package(canonical,extra={'ppt/theme/theme1.xml':b'<theme/>','ppt/media/image1.png':b'original'})
        package(self.deck,extra={'ppt/theme/theme1.xml':b'<changed/>','ppt/media/image1.png':b'changed'})
        r,_=self.audit('--canonical',canonical,'--changed-slide',1); self.assertNotEqual(r.returncode,0)

    def test_authorized_slide_only_passes(self):
        canonical=self.dir/'canonical.pptx'; package(canonical,[slide(),slide()])
        package(self.deck,[slide(('D','E','F')),slide()])
        r,_=self.audit('--canonical',canonical,'--changed-slide',1); self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_report_cannot_clobber_source(self):
        before=self.deck.read_bytes()
        r,_=self.audit('--output',self.deck)
        self.assertNotEqual(r.returncode,0); self.assertEqual(self.deck.read_bytes(),before)

    def test_output_file_not_overwritten(self):
        target=self.dir/'existing.pptx'; target.write_bytes(b'KEEP')
        r=self.run_tool('make_render_safe_copy.py',self.deck,target,'--font','Arial')
        self.assertNotEqual(r.returncode,0); self.assertEqual(target.read_bytes(),b'KEEP')

    def test_font_quotes_are_xml_safe(self):
        target=self.dir/'render.pptx'; before=self.deck.read_bytes()
        font='Example & "Quoted" Font'
        r=self.run_tool('make_render_safe_copy.py',self.deck,target,'--font',font)
        self.assertEqual(r.returncode,0,r.stderr)
        with zipfile.ZipFile(target) as z:
            root=ET.fromstring(z.read('ppt/slides/slide1.xml'))
            self.assertEqual(root.find('.//{'+A+'}rPr').get('typeface'),font)
        self.assertEqual(self.deck.read_bytes(),before)

    def test_malformed_xml_leaves_no_output(self):
        package(self.deck,[b'<broken>'])
        target=self.dir/'render.pptx'
        r=self.run_tool('make_render_safe_copy.py',self.deck,target,'--font','Arial')
        self.assertNotEqual(r.returncode,0); self.assertFalse(target.exists())

    def test_zip_traversal_rejected(self):
        package(self.deck,extra={'../escape':b'bad'})
        r,_=self.audit(); self.assertNotEqual(r.returncode,0)

    def test_vertical_chain_passes(self):
        content=''.join(shape(i+1,t,2,1+i*2) for i,t in enumerate(('A','B','C')))
        content+=shape(10,'',2.5,2,0,1,'line',True)+shape(11,'',2.5,4,0,1,'line',True)
        data=f'<p:sld xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree>{content}</p:spTree></p:cSld></p:sld>'.encode()
        package(self.deck,[data]); r,_=self.audit('--chain','A|B|C','--orientation','vertical')
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_id_selection_disambiguates(self):
        package(self.deck,[slide(duplicate=True)])
        r,_=self.audit('--slide',1,'--chain','id:1|id:2|id:3')
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_dtd_is_rejected(self):
        package(self.deck,[b'<!DOCTYPE s [<!ENTITY x "A">]>'+slide()])
        r,_=self.audit(); self.assertNotEqual(r.returncode,0)

    def test_duplicate_zip_member_rejected(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with zipfile.ZipFile(self.deck,'a') as z:
                z.writestr('ppt/slides/slide1.xml',slide())
        r,_=self.audit(); self.assertNotEqual(r.returncode,0)

    def test_numerically_reversed_labels_not_resorted(self):
        # Explicit selection order has to remain authoritative.
        r,_=self.audit('--chain','C|B|A'); self.assertNotEqual(r.returncode,0)


if __name__=='__main__':
    unittest.main(verbosity=2)
