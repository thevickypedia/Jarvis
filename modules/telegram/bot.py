import importlib
import logging
import random
import string
import time
from logging.config import dictConfig

import requests

from api.controller import offline_compatible
from modules.database import database
from modules.models import config, models
from modules.utils import support

importlib.reload(module=logging)
dictConfig(config.BotConfig().dict())
logger = logging.getLogger('telegram')

env = models.env
offline_compatible = offline_compatible()
db = database.Database(table_name='offline', columns=['key', 'value'])

USER_TITLE = {}
FAILED_CONNECTIONS = {'calls': 0}


def greeting() -> str:
    """Returns a random greeting message.

    Returns:
        str:
        Random greeting.
    """
    return random.choice(
        ["Greetings", "Hello", "Welcome", "Bonjour", "Hey there", "What's up", "Yo", "Ssup", "Cheers", "Ciao"]
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
    else:
        return 'sir'


def intro() -> str:
    """Returns a welcome message as a string.

    Returns:
        str:
    """
    return "\nI am Jarvis, a pre-programmed virtual assistant designed by Mr. Rao\n" \
           "You may start a conversation anytime using /jarvis\n\n" \
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

    def __init__(self):
        """Initiates a session."""
        self.session = requests.Session()

    def _make_request(self, url: str, payload: dict) -> requests.Response:
        """Makes a post request with a ``connect timeout`` of 3 seconds and ``read timeout`` of 60.

        Args:
            url: URL to submit the request.
            payload: Payload to send as data.

        Returns:
            Response:
            Response class.
        """
        response = self.session.post(url=url, data=payload, timeout=(3, 60))
        if not response.ok:
            logger.error(response.json())
        return response

    def reply_to(self, payload: dict, response: str, parse_mode: str = 'markdown') -> requests.Response:
        """Generates a payload to reply to a message received.

        Args:
            payload: Payload to send as data.
            response: Message to be sent to the user.
            parse_mode: Parse mode. Defaults to ``markdown``

        Returns:
            Response:
            Response class.
        """
        post_data = {'chat_id': payload['from']['id'], 'reply_to_message_id': payload['message_id'], 'text': response,
                     'parse_mode': parse_mode}
        return self._make_request(url=self.BASE_URL + env.bot_token + '/sendMessage', payload=post_data)

    def send_message(self, chat_id, response: str, parse_mode: str = 'markdown') -> requests.Response:
        """Generates a payload to reply to a message received.

        Args:
            chat_id: Chat ID.
            response: Message to be sent to the user.
            parse_mode: Parse mode. Defaults to ``markdown``

        Returns:
            Response:
            Response class.
        """
        post_data = {'chat_id': chat_id, 'text': response, 'parse_mode': parse_mode}
        return self._make_request(url=self.BASE_URL + env.bot_token + '/sendMessage', payload=post_data)

    def poll_for_messages(self) -> None:
        """Polls ``api.telegram.org`` for new messages.

        Raises:
            - OverflowError: When a new polling is initiated using the same token.
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
                    raise OverflowError(
                        response.json().get('description')
                    )
                raise ConnectionError(
                    response.json()
                )
            if not response.get('result'):
                continue
            for result in response['result']:
                message = result.get('message', {})
                if message.get('text') and message.get('from', {}).get('id'):
                    self.process_payload(payload=message)
                offset = result['update_id'] + 1

    def authenticate(self, payload: dict) -> bool:
        """Authenticates the user with ``userId`` and ``userName``.

        Args:
            payload: Payload to extract the user information.

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
        logger.info(f"{chat['username']}: {payload.get('text')}")
        return True

    def process_payload(self, payload: dict) -> None:
        """Processes the payload received after checking for authentication.

        Args:
            payload: Payload to extract information from.
        """
        if not self.authenticate(payload=payload):
            return
        if payload.get('text') in ['hello', 'hi', 'heya', 'hey']:
            self.reply_to(payload=payload,
                          response=f"{greeting()} {payload['from']['first_name']}!\n"
                                   f"Good {support.part_of_day()}! How may I be of service today?")
            return
        if payload['text'] == '/start':
            self.send_message(chat_id=payload['from']['id'],
                              response=f"{greeting()} {payload['from']['first_name']}!{intro()}")
            return
        if not USER_TITLE.get(payload['from']['username']):
            USER_TITLE[payload['from']['username']] = get_title_by_name(payload['from']['first_name'])
        self.jarvis(payload=payload)

    def jarvis(self, payload: dict) -> None:
        """Uses the table ``offline`` in the database to process a response.

        Args:
            payload: Payload to extract information from.
        """
        command = payload['text']
        command = command.translate(str.maketrans('', '', string.punctuation))  # Remove punctuations from string
        if command.lower() == 'test':
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

        if not any(word in command.lower() for word in offline_compatible):
            self.send_message(chat_id=payload['from']['id'],
                              response=f"'{command}' is not a part of offline communicator compatible request.\n"
                                       "Using Telegram I'm limited to perform tasks that do not require an interaction")
            return

        logger.info(f'Request: {command}')

        if existing := db.cursor.execute("SELECT value from offline WHERE key=?", ('request',)).fetchone():
            self.reply_to(payload=payload,
                          response=f"Processing another offline request: '{existing[0]}'.\nPlease try again.")
            return

        db.cursor.execute(f"INSERT OR REPLACE INTO offline (key, value) VALUES {('request', command)}")
        db.connection.commit()

        while True:
            if response := db.cursor.execute("SELECT value from offline WHERE key=?", ('response',)).fetchone():
                if response[0]:
                    text = response[0].replace(env.title, USER_TITLE.get(payload['from']['username']))
                else:
                    text = f"I'm sorry {env.title}! I wasn't able to process {payload.get('text')}"
                self.send_message(chat_id=payload['from']['id'], response=text)
                db.cursor.execute("DELETE FROM offline WHERE key=:key OR value=:value ",
                                  {'key': 'response', 'value': response[0]})
                db.connection.commit()
                logger.info(f'Response: {response[0]}')
                return


def handler():
    """Initiates polling for new messages.

    Handles:
        - OverflowError: Restarts polling to take control over.
        - ConnectionError: Initiates after 10, 20 or 30 seconds. Depends on retry count. Shuts off after 3 attempts.
    """
    try:
        TelegramBot().poll_for_messages()
    except OverflowError as error:
        logger.error(error)
        logger.info("Restarting message poll to take over..")
        handler()
    except (requests.exceptions.ReadTimeout, ConnectionError) as error:
        FAILED_CONNECTIONS['calls'] += 1
        logger.critical(error)
        logger.info("Restarting after 10 seconds..")
        time.sleep(FAILED_CONNECTIONS['calls'] * 10)
        if FAILED_CONNECTIONS['calls'] > 3:
            logger.fatal("Couldn't recover from connection error.")
        else:
            handler()
    # Expected exceptions
    # except socket.timeout as error:
    #     logger.fatal(error)
    # except urllib3.exceptions.ConnectTimeoutError as error:
    #     logger.fatal(error)
    # except urllib3.exceptions.MaxRetryError as error:
    #     logger.fatal(error)
    # except requests.exceptions.ConnectTimeout as error:
    #     logger.fatal(error)


if __name__ == '__main__':
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
    except KeyboardInterrupt:
        logger.info("Terminated")
