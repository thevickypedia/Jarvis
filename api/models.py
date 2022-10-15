from typing import Any, Union

from pydantic import BaseModel


class GetData(BaseModel):
    """BaseModel that handles input data for the API which is treated as members for the class ``GetData``.

    >>> GetData

    See Also:
        - ``command``: Offline command sent via API which ``Jarvis`` has to perform.
    """

    command: str
    native_audio: bool = False
    speech_timeout: Union[int, float] = 0


class GetIndex(BaseModel):
    """BaseModel that handles input data for the API which is treated as members for the class ``GetData``.

    >>> GetData

    See Also:
        - ``command``: Offline command sent via API which ``Jarvis`` has to perform.
    """

    index: Any = None


class GetText(BaseModel):
    """BaseModel that handles input data for the API which is treated as members for the class ``GetText``.

    >>> GetText

    See Also:
        - ``text``: Text to be processed with speech synthesis.
        - ``timeout``: Timeout for speech-synthesis API call.
        - ``quality``: Quality of speech synthesis.
        - ``voice``: Voice module to be used.
    """

    text: str
    timeout: Union[int, float] = None
    quality: str = "high"
    voice: str = "en-us_northern_english_male-glow_tts"
