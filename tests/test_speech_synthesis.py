import os
import sys
import unittest
from typing import NoReturn
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath('..'))

from jarvis.modules.audio import speaker  # noqa: E402
from jarvis.modules.exceptions import EgressErrors  # noqa: E402
from tests.constant import SAMPLE_PHRASE  # noqa: E402


# noinspection PyUnusedLocal
class TestSpeechSynthesizer(unittest.TestCase):
    """TestSpeechSynthesizer object for testing speech synthesis module.

    >>> TestSpeechSynthesizer

    """

    @patch('requests.post')
    def test_successful_synthesis(self, mock_post: MagicMock) -> NoReturn:
        """Test successful speech synthesis.

        This method tests the behavior of the speech_synthesizer function when a successful
        response is mocked from the post request call.

        Args:
            mock_post: Mock of the ``requests.post`` function.
        """
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = SAMPLE_PHRASE.encode(encoding='UTF-8')
        mock_post.return_value = mock_response

        result = speaker.speech_synthesizer(SAMPLE_PHRASE)

        self.assertTrue(result)

    @patch('requests.post')
    def test_unsuccessful_synthesis(self, mock_post: MagicMock) -> NoReturn:
        """Test unsuccessful speech synthesis.

        This method tests the behavior of the speech_synthesizer function when an unsuccessful
        response is mocked from the post request call.

        Args:
            mock_post: Mock of the ``requests.post`` function.
        """
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        result = speaker.speech_synthesizer(SAMPLE_PHRASE)

        self.assertFalse(result)

    @patch('requests.post', side_effect=UnicodeError("Test UnicodeError"))
    def test_unicode_error_handling(self, mock_post: MagicMock) -> NoReturn:
        """Test UnicodeError handling in speech synthesis.

        This method tests the handling of UnicodeError within the speech_synthesizer function.

        Args:
            mock_post: Mock of the ``requests.post`` function with side effect.
        """
        result = speaker.speech_synthesizer(SAMPLE_PHRASE)

        self.assertFalse(result)

    @patch('requests.post', side_effect=EgressErrors)
    def test_egress_error_handling(self, mock_post: MagicMock) -> NoReturn:
        """Test EgressErrors handling in speech synthesis.

        This method tests the handling of EgressErrors within the speech_synthesizer function.

        Args:
            mock_post: Mock of the ``requests.post`` function with side effect.
        """
        result = speaker.speech_synthesizer(SAMPLE_PHRASE)

        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
