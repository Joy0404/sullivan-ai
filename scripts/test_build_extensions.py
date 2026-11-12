"""Guard the role boundary in the actual distributable, including repeated builds."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import shutil
import subprocess

from build_extensions import build, STUDENT_MODULES, LEARNING_MODULES


class Packages(unittest.TestCase):
    def test_separate_packages_and_least_permissions(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            output = build(output=temp)
            build(output=temp)
            student = Path(output) / 'student'
            guardian = Path(output) / 'guardian'
            sm = json.loads((student / 'manifest.json').read_text())
            gm = json.loads((guardian / 'manifest.json').read_text())
            self.assertEqual(sm['permissions'], ['storage', 'identity', 'sidePanel', 'scripting', 'activeTab'])
            self.assertNotIn('<all_urls>', sm['host_permissions'])
            self.assertEqual(sm['optional_host_permissions'], ['https://*/*', 'http://*/*'])
            self.assertEqual(gm['permissions'], ['storage', 'identity'])
            self.assertNotIn('web_accessible_resources', sm)
            self.assertNotIn('content_scripts', sm)
            self.assertEqual(sm['host_permissions'], ['http://127.0.0.1/*'])
            self.assertNotIn('register-form', (student / 'index.html').read_text())
            self.assertNotIn('student-form', (student / 'index.html').read_text())
            self.assertNotIn('/local/students', (student / 'app.js').read_text())
            self.assertNotIn('보호자 계정을 만들었습니다', (student / 'ui.js').read_text())
            self.assertNotIn('progress-form', (guardian / 'index.html').read_text())
            self.assertEqual(len(list(student.iterdir())), 11 + len(STUDENT_MODULES) + len(LEARNING_MODULES))
            self.assertNotIn('media.js', {path.name for path in guardian.iterdir()})
            if shutil.which('node'):
                for source in Path(output).rglob('*.js'):
                    subprocess.run(['node','--check',str(source)],check=True,capture_output=True)
            # A stale opposite-role file must not silently enter a new package.
            (student / 'guardian-app.js').write_text('stale')
            with self.assertRaises(ValueError):
                build(output=temp)

    def test_ipv6_local_permission(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            output=build('http://[::1]:8770',temp)
            manifest=json.loads((Path(output)/'student/manifest.json').read_text())
            self.assertEqual(manifest['host_permissions'],['http://[::1]/*'])

    def test_reject_unsafe_server_addresses(self):
        for server in ('http://public.example', 'https://user:pass@example.com',
                       'https://example.com/extra', 'https://example.com?x=1', 'file:///tmp/server'):
            with self.subTest(server=server), self.assertRaises(ValueError):
                build(server)


if __name__ == '__main__':
    unittest.main()
