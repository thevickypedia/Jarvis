import json
import os
import random
import re
import string
import subprocess
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Tuple

from blockstdout import BlockPrint
from googlehomepush import GoogleHome
from googlehomepush.http_server import serve_file
from holidays import country_holidays
from holidays.registry import COUNTRIES
from newsapi import NewsApiClient, newsapi_exception
from packaging.version import Version
from playsound import playsound
from pychromecast.error import ChromecastConnectionError

from jarvis import version as module_version
from jarvis.executors import (
    communicator,
    date_time,
    files,
    internet,
    robinhood,
    todo_list,
    weather,
    word_match,
)
from jarvis.modules.audio import listener, speaker
from jarvis.modules.conditions import keywords
from jarvis.modules.dictionary import dictionary
from jarvis.modules.exceptions import CameraError
from jarvis.modules.facenet import face
from jarvis.modules.logger import logger
from jarvis.modules.models import enums, models
from jarvis.modules.utils import shared, support, util


def repeat(phrase: str) -> None:
    """Repeats whatever is heard or what was said earlier.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if "i" in phrase.lower().split():
        speaker.speak(text="Please tell me what to repeat.", run=True)
        if keyword := listener.listen():
            if "exit" in keyword or "quit" in keyword or "Xzibit" in keyword:
                pass
            else:
                speaker.speak(text=f"I heard {keyword}")
    else:
        if text := shared.text_spoken:
            if text.startswith(f"Sure {models.env.title}, "):
                speaker.speak(text)
            else:
                speaker.speak(f"Sure {models.env.title}, {text}")
        else:
            repeat("i")


def apps(phrase: str) -> None:
    """Launches the requested application and if Jarvis is unable to find the app, asks for the app name from the user.

    Args:
        phrase: Takes the phrase spoken as an argument.

    Warnings:
        macOS ventura does not display built-in applications for the ls command.
    """
    if models.settings.os == enums.SupportedPlatforms.linux:
        support.unsupported_features()
        return

    keyword = phrase.split()[-1] if phrase else None
    ignore = ["app", "application"]
    if not keyword or keyword in ignore:
        if shared.called_by_offline:
            speaker.speak(text=f"I need an app name to open {models.env.title}!")
            return
        speaker.speak(text=f"Which app shall I open {models.env.title}?", run=True)
        if keyword := listener.listen():
            if "exit" in keyword or "quit" in keyword or "Xzibit" in keyword:
                return
        else:
            speaker.speak(text="I didn't quite get that. Try again.")
            return

    if models.settings.os == enums.SupportedPlatforms.windows:
        status = os.system(f"start {keyword}")
        if status == 0:
            speaker.speak(text=f"I have opened {keyword}")
        else:
            speaker.speak(text=f"I did not find the app {keyword}. Try again.")
        return

    all_apps = subprocess.check_output("ls /Applications/", shell=True)
    apps_ = all_apps.decode("utf-8").split("\n")

    app_check = False
    for app in apps_:
        if re.search(keyword, app, flags=re.IGNORECASE) is not None:
            keyword = app
            app_check = True
            break

    if not app_check:
        speaker.speak(text=f"I did not find the app {keyword}. Try again.")
        return
    app_status = os.system(f"open /Applications/{keyword!r} > /dev/null 2>&1")
    keyword = keyword.replace(".app", "")
    if app_status == 256:
        speaker.speak(
            text=f"I'm sorry {models.env.title}! I wasn't able to launch {keyword}. "
            "You might need to check its permissions."
        )
    else:
        speaker.speak(text=f"I have opened {keyword}")


def music(phrase: str = None) -> None:
    """Scans music directory in the user profile for ``.mp3`` files and plays using default player.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    get_all_files = (
        os.path.join(root, f)
        for root, _, file in os.walk(os.path.join(models.env.home, "Music"))
        for f in file
    )
    if music_files := [
        file for file in get_all_files if os.path.splitext(file)[1] == ".mp3"
    ]:
        chosen = random.choice(music_files)
        if phrase and "speaker" in phrase:
            google_home(device=phrase, file=chosen)
        else:
            if models.settings.os == enums.SupportedPlatforms.windows:
                os.system(f'start wmplayer "{chosen}"')
            else:
                subprocess.call(["open", chosen])
            support.flush_screen()
            speaker.speak(text=f"Enjoy your music {models.env.title}!")
    else:
        speaker.speak(text=f"No music files were found {models.env.title}!")


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

        >>> except IOError as error:
        >>>     import errno
        >>>     if error.errno != errno.EPIPE:
        >>>         support.write_screen(error)

    Args:
        device: Name of the Google home device on which the music has to be played.
        file: Scanned audio file to be played.
    """
    if not (network_id := internet.vpn_checker()):
        return

    if not shared.called_by_offline:
        speaker.speak(
            text=f"Scanning your IP range for Google Home devices {models.env.title}!",
            run=True,
        )
    network_id = ".".join(network_id.split(".")[:3])

    def ip_scan(host_id: int) -> Tuple[str, str] | None:
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
        # scans host IDs 1 to 255 (eg: 192.168.1.1 to 192.168.1.255)
        for info in executor.map(ip_scan, range(1, 101)):
            # this includes all the NoneType values returned by unassigned host IDs
            devices.append(info)
    # removes None values and converts list to dictionary of name and ip pair
    devices = dict([i for i in devices if i])

    if not device or not file:
        support.flush_screen()
        speaker.speak(
            text=f"You have {len(devices)} devices in your IP range {models.env.title}! "
            f"{util.comma_separator(list(devices.keys()))}. You can choose one and ask me to play "
            f"some music on any of these."
        )
        return
    else:
        chosen = [
            value for key, value in devices.items() if key.lower() in device.lower()
        ]
        if not chosen:
            speaker.speak(
                text=f"I don't see any matching devices {models.env.title}!. Let me help you. "
                f"You have {len(devices)} devices in your IP range {models.env.title}! "
                f"{util.comma_separator(list(devices.keys()))}."
            )
            return
        for target in chosen:
            # serves the file on local host and generates the play url
            file_url = serve_file(file, "audio/mp3")
            support.flush_screen()
            with BlockPrint():
                GoogleHome(host=target).play(file_url, "audio/mp3")
        if len(chosen) > 1:
            speaker.speak(
                text=f"That's interesting, you've asked me to play on {len(chosen)} devices at a time. "
                f"I hope you'll enjoy this {models.env.title}.",
                run=True,
            )
        else:
            speaker.speak(text=f"Enjoy your music {models.env.title}!", run=True)


def flip_a_coin(*args) -> None:
    """Says ``heads`` or ``tails`` from a random choice."""
    playsound(
        sound=models.indicators.coin, block=True
    ) if not shared.called_by_offline else None
    speaker.speak(
        text=f"""{random.choice(['You got', 'It landed on',
                                 "It's"])} {random.choice(['heads', 'tails'])} {models.env.title}"""
    )


def meaning(phrase: str) -> None:
    """Gets meaning for a word skimmed from the user statement.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    keyword = phrase.split()[-1] if phrase else None
    if not keyword or keyword == "word":
        speaker.speak(text="Please tell a keyword.", run=True)
        response = listener.listen()
        if not response or word_match.word_match(
            phrase=response, match_list=keywords.keywords["exit_"]
        ):
            return
        meaning(phrase=response)
    else:
        if definition := dictionary.meaning(term=keyword):
            n = 0
            vowel = ["A", "E", "I", "O", "U"]
            for key, value in definition.items():
                insert = "an" if key[0] in vowel else "a"
                repeated = " also " if n != 0 else " "
                n += 1
                mean = ", ".join(value[:2])
                speaker.speak(
                    text=f"{keyword} is{repeated}{insert} {key}, which means {mean}."
                )
            if shared.called_by_offline:
                return
            speaker.speak(text=f"Do you wanna know how {keyword} is spelled?", run=True)
            response = listener.listen()
            if word_match.word_match(
                phrase=response, match_list=keywords.keywords["ok"]
            ):
                for letter in list(keyword.lower()):
                    speaker.speak(text=letter)
                speaker.speak(run=True)
        else:
            speaker.speak(
                text=f"I'm sorry {models.env.title}! I was unable to get meaning for the word: {keyword}"
            )


def notes(*args) -> None:
    """Listens to the user and saves it as a text file."""
    if (
        (converted := listener.listen())
        or "exit" in converted
        or "quit" in converted
        or "Xzibit" in converted
    ):
        return
    with open(models.fileio.notes, "a") as writer:
        writer.write(
            f"{datetime.now().strftime('%A, %B %d, %Y')}\n{datetime.now().strftime('%I:%M %p')}\n"
            f"{converted}\n"
        )


def news(news_source: str = "fox") -> None:
    """Says news around the user's location.

    Args:
        news_source: Source from where the news has to be fetched. Defaults to ``fox``.
    """
    if not models.env.news_apikey:
        logger.warning("News apikey not found.")
        support.no_env_vars()
        return

    news_client = NewsApiClient(api_key=models.env.news_apikey)
    try:
        all_articles = news_client.get_top_headlines(sources=f"{news_source}-news")
    except newsapi_exception.NewsAPIException as error:
        logger.error(error)
        speaker.speak(
            text=f"I'm sorry {models.env.title}! I wasn't able to get the news {models.env.title}!"
        )
        return
    if all_articles.get("status", "fail") != "ok":
        logger.warning(all_articles)
        speaker.speak(
            text=f"I'm sorry {models.env.title}! I wasn't able to get the news {models.env.title}!"
        )
        return
    if (
        all_articles.get("totalResults", 0) == 0
        or all_articles.get("articles", []) == []
    ):
        logger.warning(all_articles)
        speaker.speak(
            text=f"I wasn't able to find any news around you {models.env.title}!"
        )
        return
    speaker.speak(text="News around you!")
    speaker.speak(
        text=" ".join([article["title"] for article in all_articles["articles"]])
    )
    if shared.called_by_offline:
        return

    if shared.called["report"]:
        speaker.speak(run=True)


def report(*args) -> None:
    """Initiates a list of functions, that I tend to check first thing in the morning."""
    support.write_screen(text="Starting today's report")
    shared.called["report"] = True
    date_time.current_date()
    date_time.current_time()
    weather.weather()
    todo_list.get_todo()
    communicator.read_gmail()
    robinhood.robinhood()
    news()
    shared.called["report"] = False


def celebrate(phrase: str = None) -> str | None:
    """Function to look if the current date is a holiday or a birthday.

    Args:
        phrase: Takes the phrase spoken as an argument.

    Returns:
        str:
        A string of the event observed today.
    """
    countryname = None
    if phrase:
        date, day, tense = support.extract_humanized_date(phrase)
        logger.info(f"Extracted humanized date: {date}")
    else:
        date, day, tense = datetime.today().date(), "today", "is"
    if phrase:
        phrase = phrase.strip()
        countries = {
            country[1]: [" ".join(re.findall("[A-Z][^A-Z]*", country[0])), country[2]]
            for country in COUNTRIES.values()
        }
        for code, names in countries.items():
            # If country code is used, then it should be a precise match, otherwise just regex it
            if code in phrase.split() or any(name in phrase for name in names):
                countryname = names[0]
                countrycode = code
                logger.info("%s: %s", countrycode, countryname)
                break
    else:
        location = files.get_location()
        # get country code from location.yaml
        if not (countrycode := location.get("address", {}).get("country_code")):
            # get timezone from location.yaml
            if idna_timezone := location.get("timezone"):
                # get country code using timezone map
                countrycode = support.country_timezone().get(str(idna_timezone))
    if not countrycode:
        countrycode = "US"
        countryname = "USA"
    if current_holiday := country_holidays(countrycode.upper()).get(date):
        if phrase:
            speaker.speak(
                text=f"{string.capwords(day)} {tense} {current_holiday!r} in {countryname}"
            )
        else:
            return current_holiday
    elif models.env.birthday == date.strftime("%d-%B"):
        if phrase:
            speaker.speak(
                text=f"{string.capwords(day)} {tense} your birthday {models.env.title}!"
            )
        else:
            return "Birthday"
    elif phrase:
        speaker.speak(text=f"There are no events to celebrate {day}, in {countryname}")


def abusive(phrase: str) -> None:
    """Response for abusive phrases.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    logger.warning(phrase)
    speaker.speak(
        text="I don't respond to abusive words. Ask me nicely, you might get a response."
    )


def photo(*args) -> str:
    """Captures a picture of the ambience using the connected camera.

    Returns:
        str:
        Filename.
    """
    # Ret value will be used only by offline communicator
    filename = os.path.join(
        models.fileio.root, f"{datetime.now().strftime('%B_%d_%Y_%I_%M_%p')}.jpg"
    )
    try:
        facenet = face.FaceNet()
    except CameraError as error:
        logger.error(error)
        return f"I'm sorry {models.env.title}! I wasn't able to take a picture."
    facenet.capture_image(filename=filename)
    if os.path.isfile(filename):
        # don't show preview on screen if requested via offline
        if not shared.called_by_offline:
            if models.settings.os != enums.SupportedPlatforms.windows:
                subprocess.call(["open", filename])
            else:
                os.system(f"start {filename}")
        speaker.speak(text=f"A photo has been captured {models.env.title}!")
        return filename
    else:
        speaker.speak(
            text=f"I'm sorry {models.env.title}! I wasn't able to take a picture."
        )
        return f"I'm sorry {models.env.title}! I wasn't able to take a picture."


def pypi_versions(package_name: str) -> List[str] | None:
    """Get all available versions from pypi.

    Args:
        package_name: Package for which the versions are needed.

    Returns:
        List[str]:
        List of version numbers.
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        data = json.load(urllib.request.urlopen(urllib.request.Request(url=url)))
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        urllib.error.ContentTooShortError,
    ) as error:
        logger.error(error)
    else:
        pypi = list(data.get("releases", {}).keys())
        pypi.sort(key=Version)
        return pypi


def version(*args) -> None:
    """Speaks the version information along with the current version on GitHub."""
    text = f"I'm currently running on version {module_version}"
    if versions := pypi_versions(package_name="jarvis-ironman"):
        pkg_version = versions[-1]
        if module_version == pkg_version or pkg_version == f"{module_version}0":
            text += ", I'm up to date."
        else:
            text += f", but the latest released version is {pkg_version}"
    speaker.speak(text=text)
