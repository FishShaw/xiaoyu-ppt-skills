"""Real PPT generation, source preservation, portable package checks and render smoke tests.
No claim of complete OOXML XSD validation or subjective visual approval.
"""
import hashlib,json,os,re,shutil,struct,subprocess,sys,tempfile,xml.etree.ElementTree as ET,zipfile,zlib
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.environ.get('XIAOYU_INTEGRATION_OUT',str(ROOT/'artifacts/integration')))
OUT.mkdir(parents=True,exist_ok=True)
NS={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','c':'http://schemas.openxmlformats.org/drawingml/2006/chart'}
AUDIT=ROOT/'skills/xiaoyu-ppt/scripts/audit_presentation.py'
results={}
def run(args):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180)
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    return r.stdout
def png():
    def chunk(t,d):return struct.pack('!I',len(d))+t+d+struct.pack('!I',zlib.crc32(t+d)&0xffffffff)
    rows=b''.join(b'\x00'+b''.join(bytes((8,127,140) if (x//20+y//15)%2 else (233,245,246)) for x in range(160)) for y in range(90))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',160,90,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')
def structural(f):
    with zipfile.ZipFile(f) as z:
        names=z.namelist();assert len(set(names))==len(names)
        for n in names:
            if n.endswith(('.xml','.rels')):ET.fromstring(z.read(n))
            if n.endswith('.rels'):
                rels=ET.fromstring(z.read(n));base=PurePosixPath(n).parent.parent if n!='_rels/.rels' else PurePosixPath('.')
                for rel in rels:
                    assert rel.get('TargetMode')!='External','External relationship in synthetic fixture'
                    target=os.path.normpath(str(base/rel.get('Target'))).replace('\\','/').lstrip('/')
                    assert target in names,(n,target)
        media=[n for n in names if n.startswith('ppt/media/') and not n.endswith('/')]
        assert any(z.read(n)==png() for n in media),'Raw synthetic image was altered'
        slides=[n for n in names if re.fullmatch(r'ppt/slides/slide\d+.xml',n)]
        notes=[n for n in names if re.fullmatch(r'ppt/notesSlides/notesSlide\d+.xml',n)]
        assert len(slides)==len(notes)==3
        pres=ET.fromstring(z.read('ppt/presentation.xml'));sz=pres.find('p:sldSz',NS);w,h=int(sz.get('cx')),int(sz.get('cy'))
        for n in slides:
            rt=ET.fromstring(z.read(n))
            for tag in ('a:xfrm','p:xfrm'):
                for tr in rt.findall('.//'+tag,NS):
                    o,e=tr.find('a:off',NS),tr.find('a:ext',NS)
                    if o is not None and e is not None:
                        x,y,cx,cy=[int(v) for v in (o.get('x'),o.get('y'),e.get('cx'),e.get('cy'))]
                        assert x>=0 and y>=0 and x+cx<=w+20 and y+cy<=h+20,(n,x,y,cx,cy)
        charts=[n for n in names if re.fullmatch(r'ppt/charts/chart\d+.xml',n)];assert len(charts)==1
        chart=ET.fromstring(z.read(charts[0]));vals=chart.findall('.//c:val/c:numRef/c:numCache/c:pt/c:v',NS)
        assert [v.text for v in vals]==['6','8']
        assert any(n.endswith('.xlsx') for n in names)
    return {'pages':3,'native_chart_values':[6,8],'image_bytes_preserved':True,'bounds':'pass','relationships':'pass'}
def render(f):
    folder=OUT/f.stem;folder.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='xiaoyu-lo-') as profile:
        run(['soffice','-env:UserInstallation='+Path(profile).as_uri(),'--headless','--convert-to','pdf','--outdir',folder,f])
    pdf=folder/(f.stem+'.pdf');assert pdf.exists()
    run(['pdftoppm','-png','-scale-to','1200',pdf,folder/'slide'])
    text=run(['pdftotext',pdf,'-']);(folder/'rendered.txt').write_text(text,encoding='utf-8')
    assert all(word in text for word in ['输入','处理','结果','模拟','R05']),text
    images=sorted(folder.glob('slide-*.png'));assert len(images)==3
    return images
def main():
    for binary in ['node','soffice','pdftoppm','pdftotext']:
        if not shutil.which(binary):raise RuntimeError('Missing '+binary)
    (OUT/'synthetic.png').write_bytes(png())
    run(['node',ROOT/'tests/build_fixtures.js',OUT])
    for name,ratio in [('wide','16:9'),('standard','4:3'),('portrait',None)]:
        f=OUT/(name+'.pptx');r=structural(f)
        cmd=[sys.executable,AUDIT,f,'--expected-slides','3','--slide','1','--chain','输入|处理|结果']
        if ratio:cmd+=['--aspect',ratio]
        r['geometry']=json.loads(run(cmd))['passed'];r['rendered_pages']=len(render(f));r['sha256']=hashlib.sha256(f.read_bytes()).hexdigest();results[name]=r
    src=OUT/'wide.pptx';edited=OUT/'wide-edited.pptx'
    with zipfile.ZipFile(src) as z,zipfile.ZipFile(edited,'w',zipfile.ZIP_DEFLATED) as o:
        for info in z.infolist():
            data=z.read(info.filename)
            if info.filename=='ppt/slides/slide3.xml':
                assert data.count('建议先验证，再推广'.encode())==1
                data=data.replace('建议先验证，再推广'.encode(),'先复核证据，再决定范围'.encode())
            o.writestr(info,data)
    edited_render=render(edited)
    same=[a.read_bytes()==b.read_bytes() for a,b in zip(sorted((OUT/'wide').glob('slide-*.png')),edited_render)]
    assert same==[True,True,False],same
    result=json.loads(run([sys.executable,AUDIT,edited,'--canonical',src,'--changed-slide','3']))
    assert result['passed'];results['canonical']={'pass':True,'same_rendered_pages':same}
    (OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
