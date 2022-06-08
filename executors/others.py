import os
import random
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from threading import Thread
from typing import NoReturn, Tuple

import requests
from bs4 import BeautifulSoup
from googlehomepush import GoogleHome
from googlehomepush.http_server import serve_file
from joke.jokes import chucknorris, geek, icanhazdad, icndb
from newsapi import NewsApiClient, newsapi_exception
from playsound import playsound
from pychromecast.error import ChromecastConnectionError
from randfacts import get_fact

from executors.communicator import read_gmail
from executors.date_time import current_date, current_time
from executors.internet import vpn_checker
from executors.logger import logger
from executors.robinhood import robinhood
from executors.todo_list import todo
from executors.weather import weather
from modules.audio import listener, speaker
from modules.audio.listener import listen
from modules.conditions import keywords
from modules.database import database
from modules.dictionary import dictionary
from modules.models import models
from modules.utils import shared, support

env = models.env
fileio = models.FileIO()
indicators = models.Indicators()
db = database.Database(database=fileio.base_db)


def repeat() -> NoReturn:
    """Repeats whatever is heard."""
    speaker.speak(text="Please tell me what to repeat.", run=True)
    if keyword := listener.listen(timeout=3, phrase_limit=10):
        if 'exit' in keyword or 'quit' in keyword or 'Xzibit' in keyword:
            pass
        else:
            speaker.speak(text=f"I heard {keyword}")


def apps(phrase: str) -> None:
    """Launches the requested application and if Jarvis is unable to find the app, asks for the app name from the user.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    keyword = phrase.split()[-1] if phrase else None
    ignore = ['app', 'application']
    if not keyword or keyword in ignore:
        if shared.called_by_offline:
            speaker.speak(text=f'I need an app name to open {env.title}!')
            return
        speaker.speak(text=f"Which app shall I open {env.title}?", run=True)
        if keyword := listener.listen(timeout=3, phrase_limit=4):
            if 'exit' in keyword or 'quit' in keyword or 'Xzibit' in keyword:
                return
        else:
            speaker.speak(text="I didn't quite get that. Try again.")
            return

    if not env.macos:
        status = os.system(f'start {keyword}')
        if status == 0:
            speaker.speak(text=f'I have opened {keyword}')
        else:
            speaker.speak(text=f"I did not find the app {keyword}. Try again.")
        return

    all_apps = subprocess.check_output("ls /Applications/", shell=True)
    apps_ = all_apps.decode('utf-8').split('\n')

    app_check = False
    for app in apps_:
        if re.search(keyword, app, flags=re.IGNORECASE) is not None:
            keyword = app
            app_check = True
            break

    if not app_check:
        speaker.speak(text=f"I did not find the app {keyword}. Try again.")
        Thread(target=support.unrecognized_dumper, args=[{'APPLICATIONS': keyword}]).start()
        return
    app_status = os.system(f"open /Applications/'{keyword}' > /dev/null 2>&1")
    keyword = keyword.replace('.app', '')
    if app_status == 256:
        speaker.speak(text=f"I'm sorry {env.title}! I wasn't able to launch {keyword}. "
                           "You might need to check its permissions.")
    else:
        speaker.speak(text=f"I have opened {keyword}")


def music(phrase: str = None) -> NoReturn:
    """Scans music directory in the user profile for ``.mp3`` files and plays using default player.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    sys.stdout.write("\rScanning music files...")
    get_all_files = (os.path.join(root, f) for root, _, files in os.walk(os.path.join(env.home, "Music")) for f in
                     files)
    if music_files := [file for file in get_all_files if os.path.splitext(file)[1] == '.mp3']:
        chosen = random.choice(music_files)
        if phrase and 'speaker' in phrase:
            google_home(device=phrase, file=chosen)
        else:
            if env.macos:
                subprocess.call(["open", chosen])
            else:
                os.system(f'start wmplayer "{chosen}"')
            support.flush_screen()
            speaker.speak(text=f"Enjoy your music {env.title}!")
    else:
        speaker.speak(text=f'No music files were found {env.title}!')


def google_home(device: str = None, file: str = None) -> None:
    """Uses ``socket lib`` to extract ip address and scan ip range for Google home devices.

    Notes:
        - Can also play music on multiple devices at once.

    See Also:
        - https://github.com/deblockt/google-home-push/pull/7
        - | When music is played and immediately stopped/tasked the Google home device, it is most likely to except
          | ``BrokenPipeError``
        - This usually happens when a socket is written after it is fully closed.
        - This error occurs when one end of the connection tries sending data while the other has closed the connection.
        - This can simply be ignored or handled adding the code below in socket module (NOT PREFERRED).

        .. code-block:: python

            except IOError as error:
                import errno
                if error.errno != errno.EPIPE:
                    sys.stdout.write(error)

    Args:
        device: Name of the Google home device on which the music has to be played.
        file: Scanned audio file to be played.
    """
    if not (network_id := vpn_checker()):
        return

    if not shared.called_by_offline:
        speaker.speak(text=f'Scanning your IP range for Google Home devices {env.title}!', run=True)
        sys.stdout.write('\rScanning your IP range for Google Home devices..')
    network_id = '.'.join(network_id.split('.')[0:3])

    def ip_scan(host_id: int) -> Tuple[str, str]:
        """Scans the IP range using the received args as host id in an IP address.

        Args:
            host_id: Host ID passed in a multithreaded fashion to scan for Google home devices in IP range.

        Returns:
            Tuple(str, str):
            Device name, and it's IP address.
        """
        try:
            device_info = GoogleHome(host=f"{network_id}.{host_id}").cc
            device_info = str(device_info)
            device_name = device_info.split("'")[3]
            device_ip = device_info.split("'")[1]
            # port = sample.split("'")[2].split()[1].replace(',', '')
            return device_name, device_ip
        except ChromecastConnectionError:
            pass

    devices = []
    with ThreadPoolExecutor(max_workers=100) as executor:
        for info in executor.map(ip_scan, range(1, 101)):  # scans host IDs 1 to 255 (eg: 192.168.1.1 to 192.168.1.255)
            devices.append(info)  # this includes all the NoneType values returned by unassigned host IDs
    devices = dict([i for i in devices if i])  # removes None values and converts list to dictionary of name and ip pair

    if not device or not file:
        support.flush_screen()
        speaker.speak(text=f"You have {len(devices)} devices in your IP range {env.title}! "
                           f"{support.comma_separator(list(devices.keys()))}. You can choose one and ask me to play "
                           f"some music on any of these.")
        return
    else:
        chosen = [value for key, value in devices.items() if key.lower() in device.lower()]
        if not chosen:
            speaker.speak(text=f"I don't see any matching devices {env.title}!. Let me help you. "
                               f"You have {len(devices)} devices in your IP range {env.title}! "
                               f"{support.comma_separator(list(devices.keys()))}.")
            return
        for target in chosen:
            file_url = serve_file(file, "audio/mp3")  # serves the file on local host and generates the play url
            support.flush_screen()
            support.block_print()
            GoogleHome(host=target).play(file_url, "audio/mp3")
            support.release_print()
        if len(chosen) > 1:
            speaker.speak(text=f"That's interesting, you've asked me to play on {len(chosen)} devices at a time. "
                               f"I hope you'll enjoy this {env.title}.", run=True)
        else:
            speaker.speak(text=f"Enjoy your music {env.title}!", run=True)


def jokes() -> NoReturn:
    """Uses jokes lib to say chucknorris jokes."""
    speaker.speak(text=random.choice([geek, icanhazdad, chucknorris, icndb])())


def flip_a_coin() -> NoReturn:
    """Says ``heads`` or ``tails`` from a random choice."""
    playsound(sound=indicators.coin, block=True) if not shared.called_by_offline else None
    speaker.speak(
        text=f"""{random.choice(['You got', 'It landed on', "It's"])} {random.choice(['heads', 'tails'])} {env.title}"""
    )


def facts() -> NoReturn:
    """Tells a random fact."""
    speaker.speak(text=get_fact(filter_enabled=False))


def meaning(phrase: str) -> None:
    """Gets meaning for a word skimmed from the user statement.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    keyword = phrase.split()[-1] if phrase else None
    if not keyword or keyword == 'word':
        speaker.speak(text="Please tell a keyword.", run=True)
        response = listener.listen(timeout=3, phrase_limit=3)
        if not response or any(word in response.lower() for word in keywords.exit_):
            return
        meaning(phrase=response)
    else:
        if definition := dictionary.meaning(term=keyword):
            n = 0
            vowel = ['A', 'E', 'I', 'O', 'U']
            for key, value in definition.items():
                insert = 'an' if key[0] in vowel else 'a'
                repeated = 'also' if n != 0 else ''
                n += 1
                mean = ', '.join(value[0:2])
                speaker.speak(text=f'{keyword} is {repeated} {insert} {key}, which means {mean}.')
            if shared.called_by_offline:
                return
            speaker.speak(text=f'Do you wanna know how {keyword} is spelled?', run=True)
            response = listener.listen(timeout=3, phrase_limit=3)
            if any(word in response.lower() for word in keywords.ok):
                for letter in list(keyword.lower()):
                    speaker.speak(text=letter)
                speaker.speak(run=True)
        else:
            speaker.speak(text=f"I'm sorry {env.title}! I was unable to get meaning for the word: {keyword}")


def notes() -> None:
    """Listens to the user and saves it as a text file."""
    if (converted := listener.listen(timeout=5, phrase_limit=10)) or 'exit' in converted or 'quit' in converted or \
            'Xzibit' in converted:
        return
    with open(fileio.notes, 'a') as writer:
        writer.write(f"{datetime.now().strftime('%A, %B %d, %Y')}\n{datetime.now().strftime('%I:%M %p')}\n"
                     f"{converted}\n")


def news(news_source: str = 'fox') -> None:
    """Says news around the user's location.

    Args:
        news_source: Source from where the news has to be fetched. Defaults to ``fox``.
    """
    if not env.news_api:
        logger.warning("News apikey not found.")
        support.no_env_vars()
        return

    sys.stdout.write(f'\rGetting news from {news_source} news.')
    news_client = NewsApiClient(api_key=env.news_api)
    try:
        all_articles = news_client.get_top_headlines(sources=f'{news_source}-news')
    except newsapi_exception.NewsAPIException:
        speaker.speak(text=f"I wasn't able to get the news {env.title}! "
                           "I think the News API broke, you may try after sometime.")
        return

    speaker.speak(text="News around you!")
    speaker.speak(text=' '.join([article['title'] for article in all_articles['articles']]))
    if shared.called_by_offline:
        return

    if shared.called['report'] or shared.called['time_travel']:
        speaker.speak(run=True)


def report() -> NoReturn:
    """Initiates a list of functions, that I tend to check first thing in the morning."""
    sys.stdout.write("\rStarting today's report")
    shared.called['report'] = True
    current_date()
    current_time()
    weather()
    todo()
    read_gmail()
    robinhood()
    news()
    shared.called['report'] = False


def time_travel() -> None:
    """Triggered only from ``initiator()`` to give a quick update on the user's daily routine."""
    part_day = support.part_of_day()
    speaker.speak(text=f"Good {part_day} {env.name}!")
    if part_day == 'Night':
        if event := support.celebrate():
            speaker.speak(text=f'Happy {event}!')
        return
    current_date()
    current_time()
    weather()
    speaker.speak(run=True)
    with db.connection:
        cursor = db.connection.cursor()
        meeting_status = cursor.execute("SELECT info, date FROM ics").fetchone()
    if meeting_status and meeting_status[0].startswith('You') and \
            meeting_status[1] == datetime.now().strftime('%Y_%m_%d'):
        speaker.speak(text=meeting_status[0])
    with db.connection:
        cursor = db.connection.cursor()
        event_status = cursor.execute(f"SELECT info FROM {env.event_app}").fetchone()
    if event_status and event_status[0].startswith('You'):
        speaker.speak(text=event_status[0])
    todo()
    read_gmail()
    speaker.speak(text='Would you like to hear the latest news?', run=True)
    phrase = listen(timeout=3, phrase_limit=3)
    if any(word in phrase.lower() for word in keywords.ok):
        news()


def sprint_name() -> NoReturn:
    """Generates a random sprint name."""
    response = requests.get(url="https://sprint-name-gen.herokuapp.com/")
    if not response.ok:
        speaker.speak(text="I wasn't able to get a sprint name sir! Why not name it, Jarvis failed?")
        return
    soup = BeautifulSoup(response.content, 'html.parser')
    name = soup.find('span', {'class': 'sprint-name'}).text
    speaker.speak(text=name)
