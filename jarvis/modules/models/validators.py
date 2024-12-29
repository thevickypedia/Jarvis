import os
import warnings
from typing import List, NoReturn, Optional
from urllib.parse import urljoin

import cv2
import pvporcupine
import requests
from packaging.version import Version
from pyttsx3.voice import Voice

from jarvis.modules.camera import camera
from jarvis.modules.exceptions import (
    CameraError,
    DependencyError,
    EgressErrors,
    InvalidEnvVars,
)
from jarvis.modules.models.classes import EnvConfig


class Validator:
    """Object to run various startup validations.

    >>> Validator

    """

    def __init__(self, main: bool, env: EnvConfig):
        """Instantiates the validator object.

        Args:
            main: Boolean flag to indicate main method.
            env: Environment variables' configuration.
        """
        self.main = main
        self.env = env

    def validate_wake_words(
        self, detector_version: str, operating_system: str
    ) -> None | NoReturn:
        """Validate wake words and wake word detector installation.

        Args:
            detector_version: Dependent library version.
            operating_system: Operating system of the host machine.
        """
        try:
            # 3.0.2 is the last tested version on macOS - arm64 - 14.5
            assert detector_version == "1.9.5" or Version(detector_version) >= Version(
                "3.0.2"
            )
        except AssertionError:
            raise DependencyError(
                f"{operating_system} is only supported with porcupine versions 1.9.5 or 3.0.2 and above (requires key)"
            )

        for keyword in self.env.wake_words:
            if not pvporcupine.KEYWORD_PATHS.get(keyword) or not os.path.isfile(
                pvporcupine.KEYWORD_PATHS[keyword]
            ):
                raise InvalidEnvVars(
                    f"Detecting {keyword!r} is unsupported!\n"
                    f"Available keywords are: {', '.join(list(pvporcupine.KEYWORD_PATHS.keys()))}"
                )

    def validate_builtin_voices(self, voices: List[Voice]) -> Optional[bool] | NoReturn:
        """Validates the builtin voices.

        Args:
            voices: List of available voices.

        Returns:
            Optional[bool]:
            Returns an optional boolean flag to set the default voice.
        """
        if voice_names := [__voice.name for __voice in voices]:
            if not self.env.voice_name:
                return True
            if self.env.voice_name not in voice_names:
                if self.main:
                    raise InvalidEnvVars(
                        f"{self.env.voice_name!r} is not available.\n"
                        f"Available voices are: {', '.join(voice_names)}"
                    )
                else:
                    warnings.warn(
                        f"{self.env.voice_name!r} is not available. Defaulting to {self.env.voice_name!r}"
                    )
                    return True
        else:
            if self.env.speech_synthesis_api:
                warnings.warn(
                    "No system voices found! Solely relying on speech synthesis API"
                )
            else:
                if self.main:
                    raise DependencyError(
                        "No system voices found! Please use speech-synthesis API"
                    )
                else:
                    warnings.warn(
                        "No system voices found! Please use speech-synthesis API!!"
                    )

    def validate_camera_indices(self) -> Optional[int] | NoReturn:
        """Validate if the camera index is readable.

        Returns:
            Optional[int]:
            Returns the index of the camera.
        """
        try:
            if self.env.camera_index is None:
                cameras = []
            else:
                cameras = camera.Camera().list_cameras()
        except CameraError:
            cameras = []
        if cameras:
            if self.env.camera_index >= len(cameras):
                if self.main:
                    raise InvalidEnvVars(
                        f"Camera index # {self.env.camera_index} unavailable.\n"
                        "Camera index cannot exceed the number of available cameras.\n"
                        f"{len(cameras)} available cameras: {', '.join([f'{i}: {c}' for i, c in enumerate(cameras)])}"
                    )
                else:
                    warnings.warn(
                        f"Camera index # {self.env.camera_index} unavailable.\n"
                        "Camera index cannot exceed the number of available cameras.\n"
                        f"{len(cameras)} available cameras: {', '.join([f'{i}: {c}' for i, c in enumerate(cameras)])}"
                    )
                    return None
        else:
            return None

        if self.env.camera_index is None:
            return 0  # Set default but skip validation
        cam = cv2.VideoCapture(self.env.camera_index)
        if cam is None or not cam.isOpened() or cam.read() == (False, None):
            if self.main:
                raise CameraError(
                    f"Unable to read the camera - {cameras[self.env.camera_index]}"
                )
            else:
                warnings.warn(
                    f"Unable to read the camera - {cameras[self.env.camera_index]}"
                )
                return None
        cam.release()
        return self.env.camera_index

    def validate_speech_synthesis_voices(self) -> None | NoReturn:
        """Validate given voice for speech synthesis."""
        if not self.env.speech_synthesis_api:
            return
        try:
            url = urljoin(str(self.env.speech_synthesis_api), "/api/voices")
            # Set connect and read timeout explicitly
            response = requests.get(url=url, timeout=(3, 3))
            if response.ok:
                available_voices = [
                    value.get("id").replace("/", "_")
                    for key, value in response.json().items()
                ]
                if self.env.speech_synthesis_voice not in available_voices:
                    if self.main:
                        print_voices = "\n\t".join(available_voices).replace("/", "_")
                        raise InvalidEnvVars(
                            f"{self.env.speech_synthesis_voice!r} is not available.\n"
                            f"Available Voices for Speech Synthesis: \n\t{print_voices}"
                        )
                    else:
                        warnings.warn(
                            f"{self.env.speech_synthesis_voice!r} is not available.\n"
                            f"Available Voices for Speech Synthesis: {', '.join(available_voices).replace('/', '_')}"
                        )
        except EgressErrors:
            return
