import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
with patch.dict(os.environ, {}, clear=True):
    import app
    from odiseia import storage
    from odiseia.assistant_ai import AssistantAI


class Capture:
    def _send_json(self, payload, **kwargs):
        self.payload = payload


class CredentialBoundaryTests(unittest.TestCase):
    def test_backend_maps_key_is_not_a_browser_key(self):
        handler = Capture()
        with patch.dict(os.environ, {'GOOGLE_MAPS_API_KEY': 'BACKEND_ONLY_CANARY'}, clear=True):
            app.OdiseiaHandler._handle_api_get(handler, '/api/maps/config')
        self.assertFalse(handler.payload['enabled'])
        self.assertEqual(handler.payload['js_api_key'], '')

    def test_explicit_browser_maps_key_remains_supported(self):
        handler = Capture()
        with patch.dict(os.environ, {'GOOGLE_MAPS_API_KEY': 'BACKEND_ONLY_CANARY',
                                    'GOOGLE_MAPS_JS_API_KEY': 'BROWSER_CANARY'}, clear=True):
            app.OdiseiaHandler._handle_api_get(handler, '/api/maps/config')
        self.assertTrue(handler.payload['enabled'])
        self.assertEqual(handler.payload['js_api_key'], 'BROWSER_CANARY')

    def test_missing_runtime_data_is_created_without_existing_profiles(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'data'
            with patch.object(storage, 'DATA_DIR', folder), patch.object(storage, 'DATA_FILE', folder / 'state.json'):
                state = storage.load_state()
                self.assertTrue((folder / 'state.json').is_file())
                self.assertTrue(state['users'])
                self.assertTrue(all(not user['sessions'] for user in state['users'].values()))

    def test_chat_without_openai_uses_local_fallback(self):
        with patch.dict(os.environ, {}, clear=True):
            assistant = AssistantAI()
            response, metadata = assistant.reply('hola', {'name': 'Demo'}, 3, False)
        self.assertTrue(response)
        self.assertFalse(metadata['used_llm'])


if __name__ == '__main__':
    unittest.main()
