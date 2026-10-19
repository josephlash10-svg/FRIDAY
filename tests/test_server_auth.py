"""The local language server needs a per-session key: it allows any origin, so without one a web page
open in the browser could talk to it while Friday runs (llama-server's own startup warning, 2026-10-19)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import cpu_runtime as cpu


class Ok:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): pass


class ServerAuthTests(unittest.TestCase):
    def test_server_gets_a_fresh_key_through_the_environment_not_the_command_line(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            model, runtime = root / 'model.gguf', root / 'llama-server.exe'
            model.write_bytes(b''); runtime.write_bytes(b'')
            launched, health = [], []
            def popen(command, **kwargs):
                launched.append((command, kwargs))
                return SimpleNamespace(pid=1, poll=lambda: None)
            def urlopen(request, timeout=None):
                health.append(request)
                return Ok()
            with patch.object(cpu, 'ROOT', root), patch.object(cpu.subprocess, 'Popen', popen), \
                 patch.object(cpu, 'bind_child_to_this_process', lambda pid: None), \
                 patch.object(cpu, 'urlopen', urlopen), patch.object(cpu.atexit, 'register', lambda f: None):
                first = cpu.NativeLanguage(model=model, runtime=runtime)
                second = cpu.NativeLanguage(model=model, runtime=runtime)
            first.log.close(); second.log.close()
            command, kwargs = launched[0]
            self.assertGreaterEqual(len(first.api_key), 32)
            self.assertNotEqual(first.api_key, second.api_key)  # new key every start
            self.assertEqual(kwargs['env']['LLAMA_API_KEY'], first.api_key)
            self.assertFalse(any(first.api_key in part for part in command))
            self.assertEqual(health[0].get_header('Authorization'), 'Bearer ' + first.api_key)

    def test_every_request_carries_the_key(self):
        client = cpu.NativeLanguage.__new__(cpu.NativeLanguage)
        client.url = 'http://127.0.0.1:1'; client.api_key = 'session-key'
        sent = []
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, *args): return b'{}'
        def capture(request, timeout=None):
            sent.append(request)
            return Response()
        with patch.object(cpu, 'urlopen', capture):
            cpu.NativeLanguage.request(client, '/tokenize', {'content': 'hi'})
        self.assertEqual(sent[0].get_header('Authorization'), 'Bearer session-key')
        self.assertEqual(sent[0].get_header('Content-type'), 'application/json')

    def test_streamed_replies_carry_the_key(self):
        import test_cpu_runtime
        client, turn = test_cpu_runtime.CpuRuntimeTests().fixture()
        client.api_key = 'session-key'
        sent = []
        class Response:
            def __enter__(self): return iter([b'data: ' + json.dumps({'choices': [{'delta': {'content': 'Hi.'}}]}).encode() + b'\n', b'data: [DONE]\n'])
            def __exit__(self, *args): pass
        def capture(request, timeout=None):
            sent.append(request)
            return Response()
        with patch.object(cpu, 'urlopen', capture):
            client.respond(turn, 'ANSWER')
        self.assertEqual(sent[0].get_header('Authorization'), 'Bearer session-key')


if __name__ == '__main__':
    unittest.main()
