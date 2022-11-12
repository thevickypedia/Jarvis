import json
from typing import Dict, Iterable

from pyaudio import PyAudio


def get_audio_devices() -> Iterable[Dict]:
    """Returns the index of audio devices available. This function can be called on demand to check the indices."""
    py_audio = PyAudio()
    for index in range(py_audio.get_device_count()):
        yield py_audio.get_device_info_by_index(index)
    py_audio.terminate()


if __name__ == '__main__':
    print(json.dumps(list(get_audio_devices()), indent=4))
