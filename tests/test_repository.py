import datetime,importlib.util,json,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class Repository(unittest.TestCase):
    def test_security_gate_unknown_expired_and_valid_exception(self):
        m=module('audit_dependencies');url='https://example.invalid/advisory/test'
        report={'vulnerabilities':{'image-size':{'severity':'high','via':[{'url':url}]}}}
        today=datetime.date(2026,9,14)
        self.assertFalse(m.evaluate(report,[],today)['passed'])
        version=json.loads((ROOT/'package-lock.json').read_text())['packages']['node_modules/image-size']['version']
        ex={'package':'image-size','url':url,'version':version,'scope':'synthetic-fixtures-only','approved':'2026-09-14','expires':'2026-10-14'}
        self.assertTrue(m.evaluate(report,[ex],today)['passed'])
        self.assertFalse(m.evaluate(report,[ex],datetime.date(2026,10,15))['passed'])
        self.assertFalse(m.evaluate(report,[{**ex,'version':'wrong'}],today)['passed'])
    def test_pr_gate_rejects_stale_or_wrong_commit(self):
        m=module('open_pr');r={'headBranch':'feat/demo','headSha':'abc','status':'completed','conclusion':'success'}
        m.validate_run([r],'feat/demo','abc')
        with self.assertRaises(ValueError):m.validate_run([r],'feat/demo','other')
        with self.assertRaises(ValueError):m.validate_run([{**r,'status':'in_progress'},r],'feat/demo','abc')
        with self.assertRaises(ValueError):m.validate_run([{**r,'conclusion':'failure'}],'feat/demo','abc')
    def test_source_hygiene(self):self.assertEqual(module('check_repo').check(),[])
    def test_package_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=module('package_skill').build(Path(tmp)/'a');b=module('package_skill').build(Path(tmp)/'b')
            self.assertEqual(a.read_bytes(),b.read_bytes())
            with zipfile.ZipFile(a) as z:
                self.assertIn('xiaoyu-ppt/SKILL.md',z.namelist())
                self.assertTrue(all('__pycache__' not in n for n in z.namelist()))
                manifest=json.loads((a.parent/'manifest.json').read_text())
                self.assertEqual(set(z.namelist()),set(manifest['files']))
    def test_package_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=module('package_skill');p=m.build(tmp);before=p.read_bytes()
            with self.assertRaises(FileExistsError):m.build(tmp)
            self.assertEqual(p.read_bytes(),before)
