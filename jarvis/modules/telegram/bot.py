# noinspection PyUnresolvedReferences
"""Module for TelegramAPI.

>>> Bot

"""

import importlib
import json
import logging
import os
import random
import secrets
import string
import sys
import time
import traceback
from typing import NoReturn, Union

import requests
from pydantic import FilePath

from jarvis._preexec import keywords_handler  # noqa
from jarvis.executors import commander, offline, others, word_match
from jarvis.modules.audio import tts_stt
from jarvis.modules.conditions import keywords
from jarvis.modules.database import database
from jarvis.modules.exceptions import BotInUse, EgressErrors
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.offline import compatibles
from jarvis.modules.telegram import audio_handler, file_handler
from jarvis.modules.utils import support, util

importlib.reload(module=logging)

db = database.Database(database=models.fileio.base_db)

USER_TITLE = {}


def username_is_valid(username: str) -> bool:
    """Compares username and returns True if username is allowed."""
    for user in models.env.bot_users:
        if secrets.compare_digest(user, username):
            return True


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
    logger.info("Identifying gender for %s", name)
    try:
        response = requests.get(url=f"https://api.genderize.io/?name={name}", timeout=(3, 3))
    except EgressErrors as error:
        logger.critical(error)
        return models.env.title
    if not response.ok:
        return models.env.title
    if response.json().get('gender', 'Unidentified').lower() == 'female':
        logger.info("%s has been identified as female.", name)
        return 'mam'
    return 'sir'


def intro() -> str:
    """Returns a welcome message as a string.

    Returns:
        str:
    """
    return "\nI am *Jarvis*, a pre-programmed virtual assistant designed by Mr. Rao\n" \
           "You may start giving me commands to execute.\n\n" \
           "*Examples*\n\n" \
           "*Car Controls*\n" \
           "start my car\n" \
           "set my car to 66 degrees\n" \
           "turn off my car\n" \
           "lock my car\n" \
           "unlock my car\n\n" \
           "*Garage Controls*\n" \
           "get me the status of my garage\n" \
           "close my garage\n" \
           "open my garage\n" \
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
    FILE_CONTENT_URL = f'https://api.telegram.org/file/bot{models.env.bot_token}/' + '{file_path}'

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
        response = self._make_request(url=self.BASE_URL + models.env.bot_token + '/getFile',
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
        response = self.session.post(url=url, data=payload, files=files, timeout=(5, 60))
        if not response.ok:
            logger.debug(payload)
            logger.debug(files)
            logger.warning("Called by: '%s'", sys._getframe(1).f_code.co_name)  # noqa
            logger.error(response.json())
        return response

    def send_audio(self, chat_id: int, filename: Union[str, FilePath], parse_mode: str = 'HTML') -> requests.Response:
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
        return self._make_request(url=self.BASE_URL + models.env.bot_token + '/sendAudio', files=files,
                                  payload={'chat_id': chat_id, 'title': filename, 'parse_mode': parse_mode})

    def send_document(self, chat_id: int, filename: Union[str, FilePath], parse_mode: str = 'HTML') -> \
            requests.Response:
        """Sends a document to the user.

        Args:
            chat_id: Chat ID.
            filename: Name of the audio file that has to be sent.
            parse_mode: Parse mode. Defaults to ``HTML``

        Returns:
            Response:
            Response class.
        """
        files = {'document': open(filename, 'rb')}
        return self._make_request(url=self.BASE_URL + models.env.bot_token + '/sendDocument', files=files,
                                  payload={'chat_id': chat_id, 'caption': os.path.basename(filename),
                                           'parse_mode': parse_mode})

    def send_photo(self, chat_id: int, filename: Union[str, FilePath]) -> requests.Response:
        """Sends an image file to the user.

        Args:
            chat_id: Chat ID.
            filename: Name of the image file that has to be sent.

        Returns:
            Response:
            Response class.
        """
        with open(filename, 'rb') as image:
            files = {'photo': image.read()}
        return self._make_request(url=self.BASE_URL + models.env.bot_token + '/sendPhoto', files=files,
                                  payload={'chat_id': chat_id, 'title': os.path.split(filename)[-1]})

    def reply_to(self, payload: dict, response: str, parse_mode: Union[str, None] = 'markdown',
                 retry: bool = False) -> requests.Response:
        """Generates a payload to reply to a message received.

        Args:
            payload: Payload received, to extract information from.
            response: Message to be sent to the user.
            parse_mode: Parse mode. Defaults to ``markdown``
            retry: Retry reply in case reply failed because of parsing.

        Returns:
            Response:
            Response class.
        """
        result = self._make_request(url=self.BASE_URL + models.env.bot_token + '/sendMessage',
                                    payload={'chat_id': payload['from']['id'],
                                             'reply_to_message_id': payload['message_id'],
                                             'text': response, 'parse_mode': parse_mode})
        if result.status_code == 400 and parse_mode and not retry:  # Retry with response as plain text
            logger.warning("Retrying response as plain text with no parsing")
            self.reply_to(payload=payload, response=response, parse_mode=None, retry=True)
        return result

    def send_message(self, chat_id: int, response: str, parse_mode: Union[str, None] = 'markdown',
                     retry: bool = False) -> requests.Response:
        """Generates a payload to reply to a message received.

        Args:
            chat_id: Chat ID.
            response: Message to be sent to the user.
            parse_mode: Parse mode. Defaults to ``markdown``
            retry: Retry reply in case reply failed because of parsing.

        Returns:
            Response:
            Response class.
        """
        result = self._make_request(url=self.BASE_URL + models.env.bot_token + '/sendMessage',
                                    payload={'chat_id': chat_id, 'text': response, 'parse_mode': parse_mode})
        if result.status_code == 400 and parse_mode and not retry:  # Retry with response as plain text
            logger.warning("Retrying response as plain text with no parsing")
            self.send_message(chat_id=chat_id, response=response, parse_mode=None, retry=True)
        return result

    def poll_for_messages(self) -> NoReturn:
        """Polls ``api.telegram.org`` for new messages.

        Raises:
            BotInUse:
                - When a new polling is initiated using the same token.
            ConnectionError:
                - If unable to connect to the endpoint.

        See Also:
            Swaps ``offset`` value during every iteration to avoid reprocessing messages.
        """
        offset = 0
        logger.info(msg="Polling for incoming messages..")
        while True:
            response = self._make_request(url=self.BASE_URL + models.env.bot_token + '/getUpdates',
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
            keywords_handler.rewrite_keywords()
            if not response.get('result'):
                continue
            for result in response['result']:
                message = result.get('message', {})
                if message.get('text'):
                    self.process_text(payload=message)
                elif message.get('voice'):
                    self.process_voice(payload=message)
                elif message.get('document'):
                    self.process_document(payload=message)
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
            logger.error("Bot %s accessed %s", chat['username'], payload.get('text'))
            self.send_message(chat_id=chat['id'],
                              response=f"Sorry {chat['first_name']}! I can't process requests from bots.")
            return False
        if chat['id'] not in models.env.bot_chat_ids or not username_is_valid(username=chat['username']):
            logger.info("%s: %s", chat['username'], payload['text']) if payload.get('text') else None
            logger.error("Unauthorized chatID [%d] or userName [%s]", chat['id'], chat['username'])
            self.send_message(chat_id=chat['id'], response=f"401 Unauthorized user: ({chat['username']})")
            return False
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
        logger.warning("Request timed out when %s requested %s", payload['from']['username'], payload.get('text'))
        logger.warning("Request time: %s", request_time)
        if "override" in payload.get('text', '').lower() and not \
                word_match.word_match(phrase=payload.get('text', ''), match_list=keywords.keywords.kill):
            logger.info("%s requested a timeout override.", payload['from']['username'])
            return True
        else:
            self.reply_to(payload=payload,
                          response=f"Request timed out\nRequested: {request_time}\n"
                                   f"Processed: {time.strftime('%m-%d-%Y %H:%M:%S', time.localtime(time.time()))}")

    def verify_stop(self, payload: dict) -> bool:
        """Stops Jarvis by setting stop flag in ``base_db`` if stop is requested by the user with an override flag.

        Args:
            payload: Payload received, to extract information from.

        Returns:
            bool:
            Boolean flag to indicate whether to proceed.
        """
        if not word_match.word_match(phrase=payload.get('text', ''), match_list=keywords.keywords.kill):
            return True
        if "override" in payload.get('text', '').lower():
            logger.info("%s requested a STOP override.", payload['from']['username'])
            self.reply_to(payload=payload, response=f"Shutting down now {models.env.title}!\n{support.exit_message()}")
            with db.connection:
                cursor = db.connection.cursor()
                cursor.execute("INSERT or REPLACE INTO stopper (flag, caller) VALUES (?,?);", (True, 'TelegramAPI'))
                cursor.connection.commit()
        else:
            self.reply_to(payload=payload,
                          response="Jarvis cannot be stopped via offline communication without a 'override' flag.")

    def process_voice(self, payload: dict) -> None:
        """Processes the audio file in payload received after checking for authentication.

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
            if models.settings.os == models.supported_platforms.macOS:
                transcode = audio_handler.audio_converter_mac()
                if transcode and transcode(input_file_name=filename, output_audio_format="flac"):
                    converted = True
            elif models.settings.os == models.supported_platforms.windows:
                if audio_handler.audio_converter_win(input_filename=filename, output_audio_format="flac"):
                    converted = True
            if converted:
                os.remove(filename)
                filename = filename.replace(".ogg", ".flac")
                audio_to_text = tts_stt.audio_to_text(filename=filename)
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
        title = USER_TITLE.get(payload['from']['username'], models.env.title)
        if filename := tts_stt.text_to_audio(text=f"I'm sorry {title}! I was unable to process your voice command. "
                                                  "Please try again!"):
            self.send_audio(filename=filename, chat_id=payload['from']['id'])
            os.remove(filename)
        else:
            self.reply_to(payload=payload, response="Failed to convert audio. Please try text input.")

    def process_document(self, payload: dict) -> None:
        """Processes the document in payload received after checking for authentication.

        Args:
            payload: Payload received, to extract information from.
        """
        if not self.authenticate(payload=payload):
            return
        if not self.verify_timeout(payload=payload):
            return
        if bytes_obj := self._get_file(payload=payload['document']):
            filename = payload['document']['file_name']
            response = file_handler.put_file(filename=filename, file_content=bytes_obj)
            self.send_message(chat_id=payload['from']['id'], response=response, parse_mode=None)
        else:
            title = USER_TITLE.get(payload['from']['username'], models.env.title)
            self.reply_to(payload=payload, response=f"I'm sorry {title}! I was unable to process your document. "
                                                    "Please try again!", parse_mode=None)

    def process_text(self, payload: dict) -> None:
        """Processes the text in payload received after checking for authentication.

        Args:
            payload: Payload received, to extract information from.

        See Also:
            - | Requesting files and secrets are considered as special requests, so they cannot be combined with
              | other requests using 'and' or 'also'
        """
        if payload.get('text', '').lower() == 'help':
            self.send_message(chat_id=payload['from']['id'],
                              response=f"{greeting()} {payload['from']['first_name']}!\n"
                                       f"Good {util.part_of_day()}! {intro()}\n\n"
                                       "Please reach out at https://vigneshrao.com/contact for more info.")
            return
        if not self.authenticate(payload=payload):
            return
        if not self.verify_timeout(payload=payload):
            return
        if not self.verify_stop(payload=payload):
            return
        payload['text'] = payload.get('text', '').replace('override', '').replace('OVERRIDE', '')
        if word_match.word_match(phrase=payload.get('text').lower(),
                                 match_list=("hey", "hi", "hola", "what's up", "ssup", "whats up", "hello",
                                             "howdy", "hey", "chao", "hiya", "aloha"), strict=True):
            self.reply_to(payload=payload,
                          response=f"{greeting()} {payload['from']['first_name']}!\n"
                                   f"Good {util.part_of_day()}! How can I be of service today?")
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
        split_text = payload['text'].lower().split()
        if ('file' in split_text or 'files' in split_text) and \
                ('send' in split_text or 'get' in split_text or 'list' in split_text):
            if 'list' in split_text and ('files' in split_text or 'file' in split_text):
                # Set parse_mode to an explicit None, so the API doesn't try to parse as HTML or Markdown
                # since the result has file names and paths
                self.send_message(chat_id=payload['from']['id'], response=file_handler.list_files(), parse_mode=None)
                return
            _, _, filename = payload['text'].partition(' file ')
            if filename:
                response = file_handler.get_file(filename=filename.strip())
                if response['ok']:
                    self.send_document(filename=response['msg'], chat_id=payload['from']['id'])
                else:
                    self.reply_to(payload=payload, response=response['msg'], parse_mode=None)
            else:
                self.reply_to(payload=payload, response="No filename was received. "
                                                        "Please include only the filename after the keyword 'file'.")
            return
        # this feature for telegram bot relies on Jarvis API to function
        if word_match.word_match(phrase=payload['text'], match_list=keywords.keywords.secrets) and \
                word_match.word_match(phrase=payload['text'], match_list=('list', 'get')):
            res = others.secrets(phrase=payload['text'])
            if len(res.split()) == 1:
                res = "The secret requested can be accessed from '_secure-send_' endpoint using the token below.\n\n" \
                      "*Note* that the secret cannot be retrieved again using the same token and the token will " \
                      f"expire in 5 minutes.\n\n{res}"
                self.send_message(chat_id=payload['from']['id'], response=res)
            else:
                self.send_message(chat_id=payload['from']['id'], response=res, parse_mode=None)
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

        # Keywords for which the ' and ' split should not happen.
        ignore_and = keywords.keywords.send_notification + keywords.keywords.reminder + \
            keywords.keywords.distance + keywords.keywords.avoid
        if ' and ' in command and not word_match.word_match(phrase=command, match_list=ignore_and):
            for each in command.split(' and '):
                if not word_match.word_match(phrase=each, match_list=compatibles.offline_compatible()):
                    logger.warning("'%s' is not a part of offline communicator compatible request.", each)
                    self.send_message(chat_id=payload['from']['id'],
                                      response=f"{each!r} is not a part of offline communicator compatible request.")
                else:
                    self.executor(command=each, payload=payload)
            return

        if not word_match.word_match(phrase=command, match_list=compatibles.offline_compatible()):
            logger.warning("'%s' is not a part of offline communicator compatible request.", command)
            self.send_message(chat_id=payload['from']['id'],
                              response=f"{command!r} is not a part of offline communicator compatible request.")
            return

        # Keywords for which the ' after ' split should not happen.
        ignore_after = keywords.keywords.meetings + keywords.keywords.avoid
        if ' after ' in command_lower and not word_match.word_match(phrase=command, match_list=ignore_after):
            if delay_info := commander.timed_delay(phrase=command):
                logger.info("Request: %s", delay_info[0])
                self.process_response(payload=payload,
                                      response="I will execute it after "
                                               f"{support.time_converter(second=delay_info[1])} {models.env.title}!")
                logger.info("Response: Task will be executed after %d seconds", delay_info[1])
                return
        self.executor(command=command, payload=payload)

    def executor(self, command: str, payload: dict, respond: bool = True) -> NoReturn:
        """Executes the command via offline communicator.

        Args:
            command: Command to be executed.
            payload: Payload received, to extract information from.
            respond: Boolean flag to restrict the response after executing a command.
        """
        logger.info("Request: %s", command)
        try:
            response = offline.offline_communicator(command=command).replace(
                models.env.title, USER_TITLE.get(payload['from']['username'])
            )
        except Exception as error:
            logger.error(error)
            logger.error(traceback.format_exc())
            response = f"Jarvis failed to process the request.\n\n`{error}`"
        logger.info("Response: %s", response)
        self.process_response(payload=payload, response=response) if respond else None

    def process_response(self, response: str, payload: dict) -> NoReturn:
        """Processes the response via Telegram API.

        Args:
            response: Response from Jarvis.
            payload: Payload received, to extract information from.
        """
        if os.path.isfile(response) and response.endswith('jpg'):
            self.send_photo(chat_id=payload['from']['id'], filename=response)
            os.remove(response)
            return
        if payload.get('voice'):
            filename = tts_stt.text_to_audio(text=response)
            self.send_audio(chat_id=payload['from']['id'], filename=filename)
            os.remove(filename)
            return
        self.send_message(chat_id=payload['from']['id'], response=response)


if __name__ == '__main__':
    from jarvis.modules.exceptions import StopSignal

    logger = logging.getLogger(__name__)  # noqa: F811
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
