import tempfile
import unittest
from pathlib import Path
from incidentlab_install import install

class InstallTests(unittest.TestCase):
    def test_hosts_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            for host in ['hermes','openclaw']:
                root=Path(d)/host
                p=install(host,root)
                self.assertTrue(p.is_file())
                text=p.read_text()
                self.assertIn('name: incidentlab',text)
                self.assertIn('attestation',text)
                self.assertEqual(install(host,root),p)
                p.write_text('user content')
                with self.assertRaises(FileExistsError): install(host,root)
                self.assertEqual(p.read_text(),'user content')
    def test_invalid_host(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): install('unknown',Path(d))
