import unittest
from unittest.mock import MagicMock, patch

from jarvis.modules.audio import speaker
from jarvis.modules.models import models
from jarvis.modules.utils import shared
from tests.constant_test import SAMPLE_PHRASE


class TestSpeak(unittest.TestCase):
    """TestCase object for testing the speaker module.

    >>> TestSpeak

    """

    @patch("jarvis.modules.audio.speaker.speech_synthesizer", return_value=False)
    @patch("playsound.playsound")
    def test_speech_synthesis_usage(
        self, mock_playsound: MagicMock, mock_speech_synthesizer: MagicMock
    ) -> None:
        """Test speech synthesis usage.

        Args:
            mock_playsound: Mock object for playsound module.
            mock_speech_synthesizer: Mock object for speaker.speech_synthesizer function.
        """
        models.env.speech_synthesis_timeout = 3
        models.env.speech_synthesis_api = "mock-url"
        speaker.speak(text=SAMPLE_PHRASE, run=False, block=True)
        mock_speech_synthesizer.assert_called_once_with(text=SAMPLE_PHRASE)
        mock_playsound.assert_not_called()

    @patch("playsound.playsound")
    @patch("jarvis.modules.audio.speaker.speak", return_value=False)
    @patch("jarvis.modules.audio.speaker.speech_synthesizer", return_value=False)
    def test_audio_driver_usage(
        self,
        mock_playsound: MagicMock,
        mock_speaker: MagicMock,
        mock_speech_synthesizer: MagicMock,
    ) -> None:
        """Test audio driver usage.

        Args:
            mock_playsound: Mock object for playsound module.
            mock_speaker: Mock object for ``speaker.speak`` function.
            mock_speech_synthesizer: Mock object for speaker.speech_synthesizer function.
        """
        speaker.speak(text=SAMPLE_PHRASE, run=True)
        mock_speaker.assert_called_once_with(text=SAMPLE_PHRASE, run=True)
        mock_playsound.assert_not_called()
        mock_speech_synthesizer.assert_not_called()

    @patch("jarvis.modules.utils.support.write_screen")
    def test_no_text_input(self, mock_write_screen: MagicMock) -> None:
        """Test speak function with no text input.

        Args:
            mock_write_screen: Mock object for support.write_screen function.
        """
        speaker.speak(text=None, run=False, block=True)
        mock_write_screen.assert_not_called()

    @patch("jarvis.modules.utils.support.write_screen")
    def test_text_input_and_run(self, mock_write_screen: MagicMock) -> None:
        """Test speak function with text input and run flag.

        Args:
            mock_write_screen: Mock object for support.write_screen function.
        """
        speaker.speak(text=SAMPLE_PHRASE, run=True, block=True)
        mock_write_screen.assert_called_once_with(text=SAMPLE_PHRASE)

    @patch("jarvis.modules.audio.speaker.speech_synthesizer", return_value=False)
    @patch("playsound.playsound")
    def test_offline_mode(
        self, mock_playsound: MagicMock, mock_speech_synthesizer: MagicMock
    ) -> None:
        """Test speak function in offline mode.

        Args:
            mock_playsound: Mock object for playsound module.
            mock_speech_synthesizer: Mock object for speaker.speech_synthesizer function.
        """
        shared.called_by_offline = True
        speaker.speak(text=SAMPLE_PHRASE)
        mock_speech_synthesizer.assert_not_called()
        mock_playsound.assert_not_called()
        shared.called_by_offline = False


if __name__ == "__main__":
    unittest.main()
