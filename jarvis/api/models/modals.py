from typing import Any, Optional, Union

from pydantic import BaseModel, EmailStr

from jarvis.modules.models import models


class OfflineCommunicatorModal(BaseModel):
    """BaseModel that handles input data for ``OfflineCommunicatorModal``.

    >>> OfflineCommunicatorModal

    """

    command: str
    native_audio: Optional[bool] = False
    speech_timeout: Optional[Union[int, float]] = 0


class StockMonitorModal(BaseModel):
    """BaseModel that handles input data for ``StockMonitorModal``.

    >>> StockMonitorModal

    """

    email: EmailStr
    token: Any
    request: Any
    plaintext: bool = False


class CameraIndexModal(BaseModel):
    """BaseModel that handles input data for ``CameraIndexModal``.

    >>> CameraIndexModal

    """

    index: Optional[Any] = None


class SpeechSynthesisModal(BaseModel):
    """BaseModel that handles input data for ``SpeechSynthesisModal``.

    >>> SpeechSynthesisModal

    """

    text: str
    timeout: Optional[Union[int, float]] = None
    quality: Optional[str] = models.env.speech_synthesis_quality
    voice: Optional[str] = models.env.speech_synthesis_voice
