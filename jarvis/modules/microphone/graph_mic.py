# noinspection PyUnresolvedReferences
# This doc string has URL split into multiple lines
"""Module to plot realtime microphone spectrum using matplotlib.

>>> GraphMic

References:
    `sound device readthedocs <https://python-sounddevice.readthedocs.io/en/0.3.14/examples.html#plot
    -microphone-signal-s-in-real-time>`__
"""

import os
import queue
from struct import Struct
from typing import List, NoReturn, Optional, Tuple, Union, cast

import matplotlib.pyplot
import numpy
import sounddevice
import yaml
from matplotlib.animation import FuncAnimation
from matplotlib.axes import Subplot
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

QUEUE = queue.Queue()


class Settings:
    """Wraps all the required options in an object.

    >>> Settings

    """

    # User config
    channels: Optional[List[int]]
    device: Optional[Union[str, int]]
    window: Optional[int]
    interval: Optional[int]
    samplerate: Optional[float]
    down_sample: Optional[int]
    window_size: Optional[Tuple[int, int]]
    rate: Optional[int]
    dark_mode: Optional[bool]

    # System config
    mapping: Optional[List[int]]
    lines: Optional[List[Line2D]]
    plot_data: Optional[numpy.ndarray]


settings = Settings()


def list_devices() -> sounddevice.DeviceList:
    """List audion devices."""
    return sounddevice.query_devices()


# noinspection PyUnusedLocal
def audio_callback(indata: numpy.ndarray, frames: int, time: Struct, status: sounddevice.CallbackFlags) -> NoReturn:
    """This is called (from a separate thread) for each audio block."""
    if status:
        logger.info(status)
    # Fancy indexing with mapping creates a (necessary!) copy:
    QUEUE.put(indata[::settings.down_sample, settings.mapping])


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
        settings.plot_data = numpy.roll(settings.plot_data, -shift, axis=0)
        settings.plot_data[-shift:, :] = data
    for column, line in enumerate(settings.lines):
        line.set_ydata(settings.plot_data[:, column])
    return settings.lines


def plot_mic(channels: List[int] = None, device: Union[str, int] = None, window: int = 200,
             interval: int = 30, samplerate: float = None, down_sample: int = 10,
             window_size: Tuple[int, int] = (5, 3), rate: int = 40, dark_mode: bool = True) -> NoReturn:
    """Loads all the arguments into a dict and kicks off the mapping.

    Args:
        channels: Input channels to plot (default: the first [1])
        device: Input device (numeric ID or substring)
        window: Visible time slot (default: 200 ms)
        interval: Minimum time between plot updates (default: 30 ms)
        samplerate: Sampling rate of audio device
        down_sample: Display every Nth sample (default: 10)
        window_size: Size of the spectrum window (default: 7 inches in width, 5 inches in height)
        rate: How quick the graph should be moving on screen (lower is slower, 1000 is pretty quick)
        dark_mode: Sets graph background to almost black
    """
    config.multiprocessing_logger(filename=os.path.join('logs', 'mic_plotter_%d-%m-%Y.log'))
    subprocess_id = os.getpid()
    logger.info("Updating process ID [%d] in [plot_mic] children table.", subprocess_id)
    db = database.Database(database=models.fileio.base_db)
    with db.connection:
        cursor = db.connection.cursor()
        cursor.execute("UPDATE children SET plot_mic=null")
        cursor.execute("INSERT or REPLACE INTO children (plot_mic) VALUES (?);", (subprocess_id,))
        db.connection.commit()
    logger.info("Updating process ID [%d] in [plot_mic] processes mapping.", subprocess_id)
    if os.path.isfile(models.fileio.processes):
        with open(models.fileio.processes) as file:
            dump = yaml.load(stream=file, Loader=yaml.FullLoader) or {}
        if not dump.get(plot_mic.__name__):
            logger.critical("ATTENTION::Missing %s's process ID in '%s'" %
                            (plot_mic.__name__, models.fileio.processes))
        # WATCH OUT: for changes in docstring in "processor.py -> create_process_mapping() -> Handles -> plot_mic"
        dump[plot_mic.__name__] = [subprocess_id, "Plot microphone usage in real time"]
        with open(models.fileio.processes, 'w') as file:
            yaml.dump(data=dump, stream=file)
    else:
        logger.critical("ATTENTION::Missing '%s'", models.fileio.processes)
    logger.info("Feeding all arguments into dict.")
    if not channels:
        channels = [1]
    if not samplerate:
        device_info = sounddevice.query_devices(device, 'input')
        samplerate = device_info['default_samplerate']
    settings.channels = channels
    settings.device = device
    settings.window = window
    settings.interval = interval
    settings.samplerate = samplerate
    settings.down_sample = down_sample
    settings.window_size = window_size
    settings.rate = rate
    settings.dark_mode = dark_mode
    settings.mapping = [c - 1 for c in channels]  # Channel numbers start with 1
    logger.info(settings.__dict__)
    try:
        _kick_off()
    except Exception as error:
        logger.error(type(error).__name__ + ': ' + error.__str__())


def _kick_off() -> NoReturn:
    """Plots the live microphone signal(s) with matplotlib."""
    logger.info("Initiating microphone plotter")
    if settings.samplerate is None:
        device_info = sounddevice.query_devices(settings.device, 'input')
        settings.samplerate = device_info['default_samplerate']

    length = int(settings.window * settings.samplerate / (settings.rate * settings.down_sample))
    settings.plot_data = numpy.zeros((length, len(settings.channels)))

    # Add type hint when unpacking a tuple (lazy way to avoid variables)
    fig, ax = cast(Tuple[Figure, Subplot], matplotlib.pyplot.subplots())
    fig.set_size_inches(settings.window_size)
    settings.lines = ax.plot(settings.plot_data)
    if len(settings.channels) > 1:
        ax.legend([f'channel {c}' for c in settings.channels],
                  loc='lower left', ncol=len(settings.channels))
    ax.axis((0, len(settings.plot_data), -1, 1))
    ax.set_yticks([0])
    ax.yaxis.grid(True)
    ax.tick_params(bottom=False, top=False, labelbottom=False,
                   right=False, left=False, labelleft=False)
    # Labels are not set, but if it is to be set, then set padding at least to 2
    # ax.set_xlabel('Time')
    # ax.set_ylabel('Frequency')
    fig.tight_layout(pad=0)  # no padding
    matplotlib.pyplot.legend(["Microphone Amplitude"])
    fig.canvas.manager.set_window_title("Realtime Spectrum Display")
    if settings.dark_mode:
        ax.set_facecolor('xkcd:almost black')  # https://xkcd.com/color/rgb/
        # Takes RGB or RGBA values as arguments
        # ax.set_facecolor((0.1, 0.1, 0.1))  # https://matplotlib.org/stable/api/colors_api.html

    stream = sounddevice.InputStream(
        device=settings.device, channels=max(settings.channels),
        samplerate=settings.samplerate, callback=audio_callback
    )
    ani = FuncAnimation(fig=fig, func=update_plot, interval=settings.interval, blit=True, cache_frame_data=False)  # noqa
    with stream:
        matplotlib.pyplot.show()


if __name__ == '__main__':
    from jarvis.modules.database import database
    from jarvis.modules.logger import config
    from jarvis.modules.logger.custom_logger import logger
    from jarvis.modules.models import models

    plot_mic()
