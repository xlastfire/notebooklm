import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from client_wrapper import NotebookAgent

class TestNotebookAgentLanguage(unittest.IsolatedAsyncioTestCase):
    @patch('client_wrapper.NotebookLMClient.from_storage')
    async def test_connect_sets_language(self, mock_from_storage):
        # Setup mocks
        mock_client = AsyncMock()
        mock_client.settings = AsyncMock()
        mock_client.settings.set_output_language = AsyncMock()

        mock_from_storage.return_value = mock_client

        agent = NotebookAgent()

        # Test connect
        success = await agent.connect("dummy_path")

        self.assertTrue(success)
        mock_client.__aenter__.assert_called_once()
        mock_client.settings.set_output_language.assert_called_once_with("si")

    async def test_generate_artifact_defaults_to_sinhala(self):
        agent = NotebookAgent()
        agent.client = AsyncMock()
        agent.current_nb_id = "nb123"

        # We don't need to call the actual method if we just want to check the signature's default
        import inspect
        sig = inspect.signature(agent.generate_artifact)
        self.assertEqual(sig.parameters['language'].default, "Sinhala")

    async def test_generate_artifact_bg_defaults_to_sinhala(self):
        agent = NotebookAgent()
        sig = inspect.signature(agent.generate_artifact_bg)
        self.assertEqual(sig.parameters['language'].default, "Sinhala")

    async def test_auto_pilot_bg_defaults_to_sinhala(self):
        agent = NotebookAgent()
        sig = inspect.signature(agent.auto_pilot_bg)
        self.assertEqual(sig.parameters['language'].default, "Sinhala")

if __name__ == '__main__':
    import inspect # Ensure it's available for the tests
    unittest.main()
