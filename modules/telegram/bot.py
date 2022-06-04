import importlib
import json
import logging
import os
import random
import string
import time
from logging.config import dictConfig
from typing import NoReturn, Union

import requests

from executors.offline import offline_communicator
from modules.database import database
from modules.exceptions import BotInUse
from modules.models import config, models
from modules.offline import compatibles
from modules.telegram import audio_handler
from modules.utils import support

env = models.env
fileio = models.FileIO()
db = database.Database(database=fileio.base_db)
db.create_table(table_name="stopper", columns=["flag", "caller"])

importlib.reload(module=logging) if env.macos else None
dictConfig(config.BotConfig().dict())
logger = logging.getLogger('telegram')

offline_compatible = compatibles.offline_compatible()

USER_TITLE = {}


def greeting() -> str:
    """Returns a random greeting message.

    Returns:
        str:
        Random greeting.
    """
    return random.choice(
        ["Greetings", "Hello", "Welcome", "Bonjour", "Hey there", "What's up", "Yo", "Cheers"]
    )


def get_title_by_name(name: str) -> str:
    """Predicts gender by name and returns a title accordingly.

    Args:
        name: Name for which gender has to be predicted.

    Returns:
        str:
        ``mam`` if predicted to be female, ``sir`` if gender is predicted to be male or unpredicted.
    """
    logger.info(f"Identifying gender for {name}")
    response = requests.get(url=f"https://api.genderize.io/?name={name}")
    if not response.ok:
        return 'sir'
    if response.json().get('gender', 'Unidentified').lower() == 'female':
        logger.info(f"{name} has been identified as female.")
        return 'mam'
    return 'sir'


def intro() -> str:
    """Returns a welcome message as a string.

    Returns:
        str:
    """
    return "\nI am Jarvis, a pre-programmed virtual assistant designed by Mr. Rao\n" \
           "You may start giving me commands to execute.\n\n" \
           "*Examples*\n\n" \
           "*Car Controls*\n" \
           "start my car\n" \
           "set my car to 66 degrees\n" \
           "turn off my car\n" \
           "lock my car\n" \
           "unlock my car\n\n" \
           "*TV*\n" \
           "launch Netflix on my tv\n" \
           "increase the volume on my tv\n" \
           "what's currently playing on my tv\n" \
           "turn off on my tv\n\n" \
           "*Lights*\n" \
           "turn on hallway lights\n" \
           "set my hallway lights to warm\n" \
           "set my bedroom lights to 5 percent\n" \
           "turn off all my lights\n\n" \
           "*Some more...*\n" \
           "do I have any meetings today?\n" \
           "where is my iPhone 12 Pro\n" \
           "do I have any emails?\n" \
           "what is the weather in Detroit?\n" \
           "get me the local news\n" \
           "what is the meaning of Legionnaire\n" \
           "tell a joke\n" \
           "flip a coin for me\n"


class TelegramBot:
    """Initiates a ``requests`` session to interact with Telegram API.

    >>> TelegramBot

    """

    BASE_URL = 'https://api.telegram.org/bot'
    FILE_CONTENT_URL = f'https://api.telegram.org/file/bot{env.bot_token}/' + '{file_path}'

    # TODO: Integrate feature to save document, photo and audio on server.
    # SUPPORTED_TYPES = ['text', 'audio', 'document', 'photo', 'voice']

    def __init__(self):
        """Initiates a session."""
        self.session = requests.Session()
        self.session.verify = True

    def _get_file(self, payload: dict) -> Union[bytes, None]:
        """Makes a request to get the file and file path.

        Args:
            payload: Payload received, to extract information from.

        Returns:
            bytes:
            Returns the file content as bytes.
        """
        response = self._make_request(url=self.BASE_URL + env.bot_token + '/getFile',
                                      payload={'file_id': payload['file_id']})
        try:
            json_response = json.loads(response.content)
        except json.JSONDecodeError as error:
            logger.error(error)
            return
        if not response.ok or not json_response.get('ok'):
            logger.error(response.content)
            return
        response = self.session.get(url=self.FILE_CONTENT_URL.format(file_path=json_response['result']['file_path']))
        if not response.ok:
            logger.error(response.content)
            return
        return response.content

    def _make_request(self, url: str, payload: dict, files: dict = None) -> requests.Response:
        """Makes a post request with a ``connect timeout`` of 5 seconds and ``read timeout`` of 60.

        Args:
            url: URL to submit the request.
            payload: Payload received, to extract information from.
            files: Take filename as an optional argument.

        Returns:
            Response:
            Response class.
        """
        if files:
            response = self.session.post(url=url, data=payload, files=files, timeout=(5, 60))
        else:
            response = self.session.post(url=url, data=payload, timeout=(5, 60))
        if not response.ok:
            logger.error(response.json())
        return response

    def send_audio(self, chat_id: int, filename: str, parse_mode: str = 'HTML') -> requests.Response:
        """Sends an audio file to the user.

        Args:
            chat_id: Chat ID.
            filename: Name of the audio file that has to be sent.
            parse_mode: Parse mode. Defaults to ``HTML``

        Returns:
            Response:
            Response class.
        """
        with open(filename, 'rb') as audio:
            files = {'audio': audio.read()}
        return self._make_request(url=self.BASE_URL + env.bot_token + '/sendAudio', files=files,
                                  payload={'chat_id': chat_id, 'title': filename, 'parse_mode': parse_mode})

    def reply_to(self, payload: dict, response: str, parse_mode: str = 'markdown') -> requests.Response:
        """Generates a payload to reply to a message received.

        Args:
            payload: Payload received, to extract information from.
            response: Message to be sent to the user.
            parse_mode: Parse mode. Defaults to ``markdown``

        Returns:
            Response:
            Response class.
        """
        return self._make_request(url=self.BASE_URL + env.bot_token + '/sendMessage',
                                  payload={'chat_id': payload['from']['id'],
                                           'reply_to_message_id': payload['message_id'],
                                           'text': response, 'parse_mode': parse_mode})

    def send_message(self, chat_id: int, response: str, parse_mode: str = 'markdown') -> requests.Response:
        """Generates a payload to reply to a message received.

        Args:
            chat_id: Chat ID.
            response: Message to be sent to the user.
            parse_mode: Parse mode. Defaults to ``markdown``

        Returns:
            Response:
            Response class.
        """
        return self._make_request(url=self.BASE_URL + env.bot_token + '/sendMessage',
                                  payload={'chat_id': chat_id, 'text': response, 'parse_mode': parse_mode})

    def poll_for_messages(self) -> NoReturn:
        """Polls ``api.telegram.org`` for new messages.

        Raises:
            - BotInUse: When a new polling is initiated using the same token.
            - ConnectionError: If unable to connect to the endpoint.

        See Also:
            Swaps ``offset`` value during every iteration to avoid hanging new messages.
        """
        offset = 0
        logger.info(msg="Polling for incoming messages..")
        while True:
            response = self._make_request(url=self.BASE_URL + env.bot_token + '/getUpdates',
                                          payload={'offset': offset, 'timeout': 60})
            if response.ok:
                response = response.json()
            else:
                if response.status_code == 409:
                    raise BotInUse(
                        response.json().get('description')
                    )
                raise ConnectionError(
                    response.json()
                )
            if not response.get('result'):
                continue
            for result in response['result']:
                message = result.get('message', {})
                if message.get('text'):
                    self.process_text(payload=message)
                elif message.get('voice'):
                    self.process_voice(payload=message)
                offset = result['update_id'] + 1

    def authenticate(self, payload: dict) -> bool:
        """Authenticates the user with ``userId`` and ``userName``.

        Args:
            payload: Payload received, to extract information from.

        Returns:
            bool:
            Returns a boolean to indicate whether the user is authenticated.
        """
        chat = payload['from']
        if chat['is_bot']:
            logger.error(f"Bot {chat['username']} accessed {payload.get('text')}")
            self.send_message(chat_id=chat['id'],
                              response=f"Sorry {chat['first_name']}! I can't process requests from bots.")
            return False
        if chat['id'] not in env.bot_chat_ids or chat['username'] not in env.bot_users:
            logger.error(f"Unauthorized chatID ({chat['id']}) or userName ({chat['username']})")
            self.send_message(chat_id=chat['id'], response=f"401 {chat['username']} UNAUTHORIZED")
            return False
        logger.info(f"{chat['username']}: {payload['text']}") if payload.get('text') else None
        if not USER_TITLE.get(payload['from']['username']):
            USER_TITLE[payload['from']['username']] = get_title_by_name(name=payload['from']['first_name'])
        return True

    def verify_timeout(self, payload: dict) -> bool:
        """Verifies whether the message was received in the past 60 seconds.

        Args:
            payload: Payload received, to extract information from.

        Returns:
            bool:
            True or False flag to indicate if the request timed out.
        """
        if int(time.time()) - payload['date'] < 60:
            return True
        request_time = time.strftime('%m-%d-%Y %H:%M:%S', time.localtime(payload['date']))
        logger.warning(f"Request timed out when {payload['from']['username']} requested {payload.get('text')}")
        logger.warning(f"Request time: {request_time}")
        if "bypass" in payload.get('text', '').lower():
            logger.info(f"{payload['from']['username']} requested a timeout bypass.")
            return True
        else:
            self.reply_to(payload=payload,
                          response=f"Request timed out\nRequested: {request_time}\n"
                                   f"Processed: {time.strftime('%m-%d-%Y %H:%M:%S', time.localtime(time.time()))}")

    def verify_stop(self, payload: dict) -> bool:
        """Stops Jarvis by setting stop flag in ``fileio.base_db`` if stop is requested by the user with a bypass flag.

        Args:
            payload: Payload received, to extract information from.

        Returns:
            bool:
            Boolean flag to indicate whether to proceed.
        """
        if "stop" not in payload.get('text', '').lower():
            return True
        if "bypass" in payload.get('text', '').lower():
            logger.info(f"{payload['from']['username']} requested a STOP bypass.")
            self.reply_to(payload=payload, response=f"Shutting down now {env.title}!\n{support.exit_message()}")
            with db.connection:
                cursor = db.connection.cursor()
                cursor.execute("INSERT INTO stopper (flag, caller) VALUES (?,?);", (True, 'TelegramAPI'))
                cursor.connection.commit()
        else:
            self.reply_to(payload=payload,
                          response="Jarvis cannot be stopped via offline communication without a 'bypass' flag.")

    def process_voice(self, payload: dict) -> None:
        """Processes the payload received after checking for authentication.

        Args:
            payload: Payload received, to extract information from.
        """
        if not self.authenticate(payload=payload):
            return
        if not self.verify_timeout(payload=payload):
            return
        if bytes_obj := self._get_file(payload=payload['voice']):
            if payload['voice']['mime_type'] == 'audio/ogg':
                filename = f"{payload['voice']['file_unique_id']}.ogg"
            else:
                logger.error("Unknown FileType received.")
                logger.error(payload)
                self.reply_to(payload=payload,
                              response=f"Your voice command was received as an unknown file type: "
                                       f"{payload['voice']['mime_type']}\nPlease try the command as a text.")
                return
            with open(filename, 'wb') as file:
                file.write(bytes_obj)
            converted = False
            if env.macos:
                transcode = audio_handler.audio_converter_mac()
                if transcode and transcode(input_file_name=filename, output_audio_format="flac"):
                    converted = True
            else:
                if audio_handler.audio_converter_win(input_filename=filename, output_audio_format="flac"):
                    converted = True
            if converted:
                os.remove(filename)
                filename = filename.replace(".ogg", ".flac")
                audio_to_text = audio_handler.audio_to_text(filename=filename)
                if audio_to_text:
                    payload['text'] = audio_to_text
                    self.jarvis(payload=payload)
                    return
            else:
                logger.error("Failed to transcode OPUS to Native FLAC")
        else:
            logger.error("Unable to get file for the file id in the payload received.")
            logger.error(payload)
        # Catches both unconverted source ogg and unconverted audio to text
        title = USER_TITLE.get(payload['from']['username'], env.title)
        if filename := audio_handler.text_to_audio(text=f"I'm sorry {title}! I was unable to process your "
                                                        "voice command. Please try again!"):
            self.send_audio(filename=filename, chat_id=payload['from']['id'])
            os.remove(filename)
        else:
            self.reply_to(payload=payload,
                          response=f"I'm sorry {title}! I was neither able to process your voice command, "
                                   "nor respond to you with one. Please try using text commands.")

    def process_text(self, payload: dict) -> None:
        """Processes the payload received after checking for authentication.

        Args:
            payload: Payload received, to extract information from.
        """
        if not self.authenticate(payload=payload):
            return
        if not self.verify_timeout(payload=payload):
            return
        if not self.verify_stop(payload=payload):
            return
        payload['text'] = payload.get('text', '').replace('bypass', '').replace('BYPASS', '')
        if any(word in payload.get('text') for word in ["hey", "hi", "hola", "what's up", "ssup", "whats up",
                                                        "hello", "howdy", "hey", "chao", "hiya", "aloha"]):
            self.reply_to(payload=payload,
                          response=f"{greeting()} {payload['from']['first_name']}!\n"
                                   f"Good {support.part_of_day()}! How can I be of service today?")
            return
        if payload['text'] == '/start':
            self.send_message(chat_id=payload['from']['id'],
                              response=f"{greeting()} {payload['from']['first_name']}! {intro()}")
            return
        if payload['text'].startswith('/'):
            if '_' not in payload['text']:  # Auto-complete can be setup using "/" commands so ignore if "_" is present
                self.reply_to(payload=payload,
                              response="*Deprecation Notice*\n\nSlash commands ('/') have been deprecated. Please use "
                                       "commands directly instead.")
            payload['text'] = payload['text'].lstrip('/').replace('jarvis', '').replace('_', ' ').strip()
        if not payload['text']:
            return
        self.jarvis(payload=payload)

    def jarvis(self, payload: dict) -> None:
        """Uses the table ``offline`` in the database to process a response.

        Args:
            payload: Payload received, to extract information from.
        """
        command = payload['text']
        command_lower = command.lower()
        if 'alarm' in command_lower or 'remind' in command_lower:
            command = command_lower
        else:
            command = command.translate(str.maketrans('', '', string.punctuation))  # Remove punctuations from string
        if command_lower == 'test':
            self.send_message(chat_id=payload['from']['id'], response="Test message received.")
            return

        if 'and' in command.split() or 'also' in command.split():
            self.send_message(chat_id=payload['from']['id'],
                              response="Jarvis can only process one command at a time via offline communicator.")
            return

        if 'after' in command.split():
            self.send_message(chat_id=payload['from']['id'],
                              response="Jarvis cannot perform tasks at a later time using offline communicator.")
            return

        if not any(word in command_lower for word in offline_compatible):
            self.send_message(chat_id=payload['from']['id'],
                              response=f"'{command}' is not a part of offline communicator compatible request.\n"
                                       "Using Telegram I'm limited to perform tasks that do not require an interaction")
            return

        logger.info(f'Request: {command}')
        response = offline_communicator(command=command).replace(env.title, USER_TITLE.get(payload['from']['username']))
        logger.info(f'Response: {response}')
        if payload.get('voice'):
            if filename := audio_handler.text_to_audio(text=response):
                self.send_audio(chat_id=payload['from']['id'], filename=filename)
                os.remove(filename)
                return
        self.send_message(chat_id=payload['from']['id'], response=response)


if __name__ == '__main__':
    from modules.exceptions import StopSignal

    logger = logging.getLogger(__name__)
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(fmt=logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s",
        datefmt="%b %d, %Y %H:%M:%S"
    ))
    logger.addHandler(hdlr=log_handler)
    logger.setLevel(level=logging.DEBUG)
    try:
        TelegramBot().poll_for_messages()
    except StopSignal:
        logger.info("Terminated")
