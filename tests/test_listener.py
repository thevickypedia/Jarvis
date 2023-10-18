import unittest
from unittest.mock import MagicMock, patch

from jarvis.main import listener
from tests.constant import SAMPLE_PHRASE


class TestListener(unittest.TestCase):
    """TestCase object for testing listener module.

    >>> TestListener

    """

    # noinspection PyUnusedLocal
    @patch("jarvis.modules.audio.listener.microphone")
    @patch("jarvis.modules.audio.listener.recognizer")
    @patch("jarvis.modules.audio.listener.playsound")
    @patch("jarvis.modules.audio.listener.support")
    def test_listen(self,
                    mock_support: MagicMock,
                    mock_playsound: MagicMock,
                    mock_recognizer: MagicMock,
                    mock_microphone: MagicMock):
        """Test the listen function.

        Mock the return values and set up necessary mocks to simulate the behavior of the listen function.
        Ensure that the listen function is called with the correct arguments.
        Ensure that the playsound function is not called when sound=False is passed.

        Args:
            mock_support: Mocked support module.
            mock_playsound: Mocked playsound function.
            mock_recognizer: Mocked recognizer module.
            mock_microphone: Mocked microphone module.
        """
        # Mock the return values and setup necessary mocks
        mock_listened = MagicMock()
        mock_recognizer.listen.return_value = mock_listened
        mock_recognizer.recognize_google.return_value = (SAMPLE_PHRASE, "some_confidence")

        result = listener.listen(sound=False, timeout=5, phrase_time_limit=10, no_conf=True)

        # Assertions
        self.assertEqual(result, SAMPLE_PHRASE)
        mock_recognizer.listen.assert_called_once_with(source=mock_microphone.__enter__(),
                                                       timeout=5, phrase_time_limit=10)
        mock_recognizer.recognize_google.assert_called_once_with(audio_data=mock_listened, with_confidence=True)

        # Check that playsound function was not called
        mock_playsound.assert_not_called()
