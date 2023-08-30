import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import pvporcupine
import pyaudio

sys.path.insert(0, os.path.abspath('..'))

from jarvis.main import Activator, models  # noqa: E402
from tests.constant import SAMPLE_PHRASE  # noqa: E402


class TestActivator(unittest.TestCase):
    """Test cases for the Activator class."""

    def setUp(self):
        """Set up the Activator instance for testing."""
        self.activator = Activator()

    @patch("pvporcupine.create")
    @patch("jarvis.main.audio_engine.open")
    def test_init_activator(self, mock_audio_open: MagicMock, mock_pvporcupine_create: MagicMock) -> None:
        """Test whether the Activator is initialized correctly.

        Mock the return values of the create function.

        Args:
            mock_audio_open: Patched audio_engine.open from jarvis.main.py.
            mock_pvporcupine_create: Patched pvporcupine.create from jarvis.main.py.
        """
        mock_pvporcupine_create.return_value = MagicMock()
        mock_audio_open.return_value = MagicMock()

        self.activator.__init__()  # Call the __init__() method explicitly

        # Assertions
        mock_pvporcupine_create.assert_called_once_with(
            library_path=pvporcupine.LIBRARY_PATH,
            sensitivities=models.env.sensitivity,
            model_path=pvporcupine.MODEL_PATH,
            keyword_paths=[pvporcupine.KEYWORD_PATHS[x] for x in models.env.wake_words]
        )
        mock_audio_open.assert_called_once_with(
            rate=mock_pvporcupine_create.return_value.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=mock_pvporcupine_create.return_value.frame_length,
            input_device_index=models.env.microphone_index
        )
        self.assertEqual(self.activator.detector, mock_pvporcupine_create.return_value)
        self.assertEqual(self.activator.audio_stream, mock_audio_open.return_value)

    @patch("jarvis.modules.audio.listener.listen")  # Patch the listener.listen from jarvis.modules.audio
    @patch("jarvis.executors.commander.initiator")  # Patch the commander.initiator from jarvis.executors
    @patch("jarvis.modules.audio.speaker.speak")  # Patch the speaker.speak from jarvis.modules.audio
    @patch("jarvis.main.audio_engine.close")  # Patch the audio_engine.close from jarvis.main
    def test_executor(self,
                      mock_audio_close: MagicMock,
                      mock_speak: MagicMock,
                      mock_initiator: MagicMock,
                      mock_listen: MagicMock) -> None:
        """Test the executor method of Activator.

        Mock return values of the listen function and set up necessary mocks.

        Args:
            mock_audio_close: Patched audio_engine.close from jarvis.main.py.
            mock_speak: Patched ``speaker.speak`` from jarvis.modules.audio.
            mock_initiator: Patched ``commander.initiator`` from jarvis.executors.
            mock_listen: Patched ``listener.listen`` from jarvis.modules.audio.
        """
        mock_listen.return_value = SAMPLE_PHRASE
        mock_initiator.return_value = None  # Not testing the behavior of initiator here

        self.activator.executor()

        # Assertions
        self.assertTrue(mock_audio_close.called)  # audio_engine.close should be called
        mock_listen.assert_called_once_with(sound=False)  # listener.listen should be called with sound=False
        mock_initiator.assert_called_once_with(
            phrase=SAMPLE_PHRASE
        )  # commander.initiator should be called with the correct phrase
        mock_speak.assert_called_once_with(run=True)  # speaker.speak should be called with run=True


if __name__ == "__main__":
    unittest.main()
