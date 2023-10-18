import unittest
from unittest.mock import MagicMock, patch

from jarvis.modules.audio import speaker
from jarvis.modules.exceptions import EgressErrors
from tests.constant_test import SAMPLE_PHRASE


# noinspection PyUnusedLocal
class TestSpeechSynthesizer(unittest.TestCase):
    """TestSpeechSynthesizer object for testing speech synthesis module.

    >>> TestSpeechSynthesizer

    """

    @patch('requests.post')
    def test_successful_synthesis(self, mock_post: MagicMock) -> None:
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
    def test_unsuccessful_synthesis(self, mock_post: MagicMock) -> None:
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
    def test_unicode_error_handling(self, mock_post: MagicMock) -> None:
        """Test UnicodeError handling in speech synthesis.

        This method tests the handling of UnicodeError within the speech_synthesizer function.

        Args:
            mock_post: Mock of the ``requests.post`` function with side effect.
        """
        result = speaker.speech_synthesizer(SAMPLE_PHRASE)

        self.assertFalse(result)

    @patch('requests.post', side_effect=EgressErrors)
    def test_egress_error_handling(self, mock_post: MagicMock) -> None:
        """Test EgressErrors handling in speech synthesis.

        This method tests the handling of EgressErrors within the speech_synthesizer function.

        Args:
            mock_post: Mock of the ``requests.post`` function with side effect.
        """
        result = speaker.speech_synthesizer(SAMPLE_PHRASE)

        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
