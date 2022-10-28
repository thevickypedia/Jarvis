from typing import Any, Union

from pydantic import BaseModel, EmailStr


class OfflineCommunicatorModal(BaseModel):
    """BaseModel that handles input data for the API which is treated as members for the class ``OfflineCommunicatorModal``.

    >>> OfflineCommunicatorModal

    """

    command: str
    native_audio: bool = False
    speech_timeout: Union[int, float] = 0


class StockMonitorModal(BaseModel):
    """BaseModel that handles input data for the API which is treated as members for the class ``StockMonitorModal``.

    >>> StockMonitorModal

    """

    email: EmailStr
    token: Any


class CameraIndexModal(BaseModel):
    """BaseModel that handles input data for the API which is treated as members for the class ``CameraIndexModal``.

    >>> CameraIndexModal

    """

    index: Any = None


class SpeechSynthesisModal(BaseModel):
    """BaseModel that handles input data for the API which is treated as members for the class ``SpeechSynthesisModal``.

    >>> SpeechSynthesisModal

    """

    text: str
    timeout: Union[int, float] = None
    quality: str = "high"
    voice: str = "en-us_northern_english_male-glow_tts"
