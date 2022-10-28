from typing import Any, Optional, Union

from pydantic import BaseModel, EmailStr


class OfflineCommunicatorModal(BaseModel):
    """BaseModel that handles input data for the API which is treated as members for the class ``OfflineCommunicatorModal``.

    >>> OfflineCommunicatorModal

    """

    command: str
    native_audio: Optional[bool] = False
    speech_timeout: Optional[Union[int, float]] = 0


class StockMonitorModal(BaseModel):
    """BaseModel that handles input data for the API which is treated as members for the class ``StockMonitorModal``.

    >>> StockMonitorModal

    """

    email: EmailStr
    token: Any
    request: Any


class CameraIndexModal(BaseModel):
    """BaseModel that handles input data for the API which is treated as members for the class ``CameraIndexModal``.

    >>> CameraIndexModal

    """

    index: Optional[Any] = None


class SpeechSynthesisModal(BaseModel):
    """BaseModel that handles input data for the API which is treated as members for the class ``SpeechSynthesisModal``.

    >>> SpeechSynthesisModal

    """

    text: str
    timeout: Optional[Union[int, float]] = None
    quality: Optional[str] = "high"
    voice: Optional[str] = "en-us_northern_english_male-glow_tts"
