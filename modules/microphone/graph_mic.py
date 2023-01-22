"""Source: https://python-sounddevice.readthedocs.io/en/0.3.14/examples.html#plot-microphone-signal-s-in-real-time."""

import os
import queue
from struct import Struct
from typing import List, NoReturn, Union

import matplotlib.pyplot
import numpy
import sounddevice
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D
from sounddevice import CallbackFlags

from modules.logger import config
from modules.logger.custom_logger import logger

FEEDER = {}
QUEUE = queue.Queue()


def list_devices() -> sounddevice.DeviceList:
    """List audion devices."""
    return sounddevice.query_devices()


# noinspection PyUnusedLocal
def audio_callback(indata: numpy.ndarray, frames: int, time: Struct, status: CallbackFlags) -> NoReturn:
    """This is called (from a separate thread) for each audio block."""
    if status:
        logger.info(status)
    # Fancy indexing with mapping creates a (necessary!) copy:
    QUEUE.put(indata[::FEEDER['downsample'], FEEDER['mapping']])


# noinspection PyUnusedLocal
def update_plot(frame: int) -> List[Line2D]:
    """This is called by matplotlib for each plot update.

    - | Typically, audio callbacks happen more frequently than plot updates,
      | therefore the queue tends to contain multiple blocks of audio data.

    """
    while True:
        try:
            data = QUEUE.get_nowait()
        except queue.Empty:
            break
        shift = len(data)
        FEEDER['plotdata'] = numpy.roll(FEEDER['plotdata'], -shift, axis=0)
        FEEDER['plotdata'][-shift:, :] = data
    for column, line in enumerate(FEEDER['lines']):
        line.set_ydata(FEEDER['plotdata'][:, column])
    return FEEDER['lines']


def plot_mic(channels: List[int] = None, device: Union[str, int] = None, window: int = 200,
             interval: int = 30, samplerate: float = None, downsample: int = 10) -> NoReturn:
    """Loads all the arguments into a dict and kicks off the mapping.

    Args:
        channels: Input channels to plot (default: the first [1])
        device: Input device (numeric ID or substring)
        window: Visible time slot (default: 200 ms)
        interval: Minimum time between plot updates (default: 30 ms)
        samplerate: Sampling rate of audio device.
        downsample: Display every Nth sample (default: 10)
    """
    config.multiprocessing_logger(filename=os.path.join('logs', 'mic_plotter_%d-%m-%Y.log'))
    logger.info("Feeding all arguments into dict.")
    if not channels:
        channels = [1]
    if not samplerate:
        device_info = sounddevice.query_devices(device, 'input')
        samplerate = device_info['default_samplerate']
    FEEDER['channels'] = channels
    FEEDER['device'] = device
    FEEDER['window'] = window
    FEEDER['interval'] = interval
    FEEDER['samplerate'] = samplerate
    FEEDER['downsample'] = downsample
    FEEDER['mapping'] = [c - 1 for c in FEEDER['channels']]  # Channel numbers start with 1
    logger.info(FEEDER)
    _kick_off()


def _kick_off() -> NoReturn:
    """Plots the live microphone signal(s) with matplotlib."""
    logger.info("Initiating microphone plotter")
    try:
        if FEEDER['samplerate'] is None:
            device_info = sounddevice.query_devices(FEEDER['device'], 'input')
            FEEDER['samplerate'] = device_info['default_samplerate']

        length = int(FEEDER['window'] * FEEDER['samplerate'] / (1000 * FEEDER['downsample']))
        FEEDER['plotdata'] = numpy.zeros((length, len(FEEDER['channels'])))

        fig, ax = matplotlib.pyplot.subplots()
        FEEDER['lines'] = ax.plot(FEEDER['plotdata'])
        if len(FEEDER['channels']) > 1:
            ax.legend([f'channel {c}' for c in FEEDER['channels']],
                      loc='lower left', ncol=len(FEEDER['channels']))
        ax.axis((0, len(FEEDER['plotdata']), -1, 1))
        ax.set_yticks([0])
        ax.yaxis.grid(True)
        ax.tick_params(bottom=False, top=False, labelbottom=False,
                       right=False, left=False, labelleft=False)
        fig.tight_layout(pad=0)

        stream = sounddevice.InputStream(
            device=FEEDER['device'], channels=max(FEEDER['channels']),
            samplerate=FEEDER['samplerate'], callback=audio_callback
        )
        ani = FuncAnimation(fig, update_plot, interval=FEEDER['interval'], blit=True)  # noqa
        with stream:
            matplotlib.pyplot.show()
    except Exception as error:
        logger.error(type(error).__name__ + ': ' + error.__str__())


if __name__ == '__main__':
    plot_mic()
