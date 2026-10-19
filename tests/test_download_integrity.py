"""llama.cpp holds the programs Friday runs, so its download must match the pinned release digest (2026-10-19)."""
import hashlib
import importlib.util
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import cpu_runtime  # noqa: F401  (download_models imports native_arch from it)

spec = importlib.util.spec_from_file_location('download_models', ROOT / 'scripts' / 'download_models.py')
dm = importlib.util.module_from_spec(spec); spec.loader.exec_module(dm)


def fake_release():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('build/bin/llama-server.exe', b'not really a server')
    return buffer.getvalue()


class Download:
    def __init__(self, data): self.data = data
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return self.data


@unittest.skipUnless(sys.platform == 'win32', 'the downloader only fetches the Windows builds')
class LlamaDownloadIntegrityTests(unittest.TestCase):
    def run_download(self, data, pinned):
        folder = tempfile.TemporaryDirectory(); self.addCleanup(folder.cleanup)
        root = Path(folder.name)
        with patch.object(dm, 'ROOT', root), patch.object(dm.urllib.request, 'urlopen', lambda url, timeout=None: Download(data)), \
             patch.object(cpu_runtime, 'native_arch', lambda: 'arm64'), patch.dict(dm.LLAMA_SHA256, {'arm64': pinned}), \
             patch('builtins.print'):
            try:
                dm.llama(); error = None
            except SystemExit as stop:
                error = stop
        return root, error

    def test_a_tampered_download_is_never_installed(self):
        data = fake_release()
        root, error = self.run_download(data, pinned='0' * 64)
        self.assertIsNotNone(error)
        self.assertIn('checksum mismatch', str(error))
        self.assertFalse((root / 'runtime').exists())

    def test_a_matching_download_is_installed(self):
        data = fake_release()
        root, error = self.run_download(data, pinned=hashlib.sha256(data).hexdigest())
        self.assertIsNone(error)
        self.assertTrue((root / 'runtime' / 'llama-arm64' / 'llama-server.exe').is_file())

    def test_both_published_builds_are_pinned(self):
        self.assertEqual(set(dm.LLAMA_SHA256), {'arm64', 'x64'})
        self.assertTrue(all(len(v) == 64 for v in dm.LLAMA_SHA256.values()))


if __name__ == '__main__':
    unittest.main()
