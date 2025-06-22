# noinspection PyUnresolvedReferences
"""Module for TelegramAPI.

>>> Bot

"""

import json
import os
import random
import secrets
import sys
import time
import traceback
import warnings
from typing import Dict, List

import requests
from pydantic import FilePath

from jarvis.executors import commander, offline, restrictions, secure_send, word_match
from jarvis.modules.audio import tts_stt
from jarvis.modules.conditions import keywords
from jarvis.modules.exceptions import (
    BotInUse,
    BotWebhookConflict,
    EgressErrors,
    InvalidArgument,
)
from jarvis.modules.logger import logger
from jarvis.modules.models import enums, models
from jarvis.modules.telegram import audio_handler, file_handler, settings
from jarvis.modules.utils import support, util

USER_TITLE = {}
BASE_URL = f"https://api.telegram.org/bot{models.env.bot_token}"
FILE_CONTENT_URL = (
    f"https://api.telegram.org/file/bot{models.env.bot_token}/" + "{file_path}"
)


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
        ("Greetings", "Hello", "Welcome", "Bonjour", "Hey there", "Cheers")
    )


def get_title_by_name(name: str) -> str:
    """Predicts gender by name and returns a title accordingly.

    Args:
        name: Name for which gender has to be predicted.

    Returns:
        str:
        ``mam`` if predicted to be female, ``sir`` if gender is predicted to be male or unpredicted.
    """
    if name.lower() == models.env.name.lower():
        return models.env.title
    logger.info("Identifying gender for '%s'", name)
    try:
        response = requests.get(
            url=f"https://api.genderize.io/?name={name}", timeout=(3, 3)
        )
    except EgressErrors as error:
        logger.critical(error)
        return models.env.title
    if not response.ok:
        logger.critical("%d: %s", response.status_code, response.text)
        return models.env.title
    response_json = response.json()
    logger.info(response_json)
    if response_json.get("gender", "unidentified").lower() == "female":
        return "mam"
    return "sir"


def intro() -> str:
    """Returns a welcome message as a string.

    Returns:
        str:
    """
    return (
        "\nI am *Jarvis*, a pre-programmed virtual assistant designed by Mr. Rao\n"
        "You may start giving me commands to execute.\n\n"
        "*Examples*\n\n"
        "*Car Controls*\n"
        "start my car\n"
        "set my car to 66 degrees\n"
        "turn off my car\n"
        "lock my car\n"
        "unlock my car\n\n"
        "*Thermostat Controls*\n"
        "get me the status of my thermostat\n"
        "what's the indoor temperature\n"
        "set my thermostat to heat 70 degrees\n\n"
        "*TV*\n"
        "launch Netflix on my tv\n"
        "increase the volume on my tv\n"
        "what's currently playing on my tv\n"
        "turn off on my tv\n\n"
        "*Lights*\n"
        "turn on hallway lights\n"
        "set my hallway lights to warm\n"
        "set my bedroom lights to 5 percent\n"
        "turn off all my lights\n\n"
        "*Some more...*\n"
        "do I have any meetings today?\n"
        "where is my iPhone 12 Pro\n"
        "do I have any emails?\n"
        "what is the weather in Detroit?\n"
        "get me the local news\n"
        "what is the meaning of Legionnaire\n"
        "tell a joke\n"
        "flip a coin for me\n"
    )


def _get_file(data_class: settings.Voice | settings.Document) -> bytes | None:
    """Makes a request to get the file and file path.

    Args:
        data_class: Required section of the payload as Voice or Document object.

    Returns:
        bytes:
        Returns the file content as bytes.
    """
    response = _make_request(
        url=BASE_URL + "/getFile", payload={"file_id": data_class.file_id}
    )
    try:
        json_response = json.loads(response.content)
    except json.JSONDecodeError as error:
        logger.error(error)
        return
    if not response.ok or not json_response.get("ok"):
        logger.error(response.content)
        return
    response = requests.get(
        url=FILE_CONTENT_URL.format(file_path=json_response["result"]["file_path"])
    )
    if not response.ok:
        logger.error(response.content)
        return
    return response.content


def _make_request(url: str, payload: dict, files: dict = None) -> requests.Response:
    """Makes a post request with a ``connect timeout`` of 5 seconds and ``read timeout`` of 60.

    Args:
        url: URL to submit the request.
        payload: Payload received, to extract information from.
        files: Take filename as an optional argument.

    Returns:
        Response:
        Response class.
    """
    response = requests.post(url=url, data=payload, files=files, timeout=(5, 60))
    if not response.ok:
        logger.debug(payload)
        logger.debug(files)
        logger.warning("Called by: '%s'", sys._getframe(1).f_code.co_name)  # noqa
        logger.error(response.json())
    return response


def send_audio(
    chat_id: int, filename: str | FilePath, parse_mode: str = "HTML"
) -> requests.Response:
    """Sends an audio file to the user.

    Args:
        chat_id: Chat ID.
        filename: Name of the audio file that has to be sent.
        parse_mode: Parse mode. Defaults to ``HTML``

    Returns:
        Response:
        Response class.
    """
    with open(filename, "rb") as audio:
        files = {"audio": audio.read()}
    return _make_request(
        url=BASE_URL + "/sendAudio",
        files=files,
        payload={"chat_id": chat_id, "title": filename, "parse_mode": parse_mode},
    )


def send_document(
    chat_id: int, filename: str | FilePath, parse_mode: str = "HTML"
) -> requests.Response:
    """Sends a document to the user.

    Args:
        chat_id: Chat ID.
        filename: Name of the audio file that has to be sent.
        parse_mode: Parse mode. Defaults to ``HTML``

    Returns:
        Response:
        Response class.
    """
    files = {"document": open(filename, "rb")}
    return _make_request(
        url=BASE_URL + "/sendDocument",
        files=files,
        payload={
            "chat_id": chat_id,
            "caption": os.path.basename(filename),
            "parse_mode": parse_mode,
        },
    )


def send_photo(chat_id: int, filename: str | FilePath) -> requests.Response:
    """Sends an image file to the user.

    Args:
        chat_id: Chat ID.
        filename: Name of the image file that has to be sent.

    Returns:
        Response:
        Response class.
    """
    with open(filename, "rb") as image:
        files = {"photo": image.read()}
    return _make_request(
        url=BASE_URL + "/sendPhoto",
        files=files,
        payload={"chat_id": chat_id, "title": os.path.split(filename)[-1]},
    )


def reply_to(
    chat: settings.Chat,
    response: str,
    parse_mode: str | None = "markdown",
    retry: bool = False,
) -> requests.Response:
    """Generates a payload to reply to a message received.

    Args:
        chat: Required section of the payload as Chat object.
        response: Message to be sent to the user.
        parse_mode: Parse mode. Defaults to ``markdown``
        retry: Retry reply in case reply failed because of parsing.

    Returns:
        Response:
        Response class.
    """
    result = _make_request(
        url=BASE_URL + "/sendMessage",
        payload={
            "chat_id": chat.id,
            "reply_to_message_id": chat.message_id,
            "text": response,
            "parse_mode": parse_mode,
        },
    )
    # Retry with response as plain text
    if result.status_code == 400 and parse_mode and not retry:
        logger.warning("Retrying response as plain text with no parsing")
        reply_to(chat, response, None, True)
    return result


def send_message(
    chat_id: int,
    response: str,
    parse_mode: str | None = "markdown",
    retry: bool = False,
) -> requests.Response:
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
    result = _make_request(
        url=BASE_URL + "/sendMessage",
        payload={"chat_id": chat_id, "text": response, "parse_mode": parse_mode},
    )
    # Retry with response as plain text
    if result.status_code == 400 and parse_mode and not retry:
        logger.warning("Retrying response as plain text with no parsing")
        send_message(chat_id=chat_id, response=response, parse_mode=None, retry=True)
    return result


def poll_for_messages() -> None:
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
    logger.info("Polling for incoming messages..")
    while True:
        response = _make_request(
            url=BASE_URL + "/getUpdates", payload={"offset": offset, "timeout": 60}
        )
        if response.ok:
            response = response.json()
        else:
            if response.status_code == 409:
                err_desc = response.json().get("description")
                # If it has come to this, then webhook has already failed
                if err_desc == (
                    "Conflict: can't use getUpdates method while webhook is active; "
                    "use deleteWebhook to delete the webhook first"
                ):
                    raise BotWebhookConflict(err_desc)
                raise BotInUse(err_desc)
            raise ConnectionError(response.json())
        if not response.get("result"):
            continue
        for result in response["result"]:
            if payload := result.get("message"):
                process_request(payload)
            else:
                logger.error("Received empty payload!!")
            offset = result["update_id"] + 1


def process_request(payload: Dict[str, int | dict]) -> None:
    """Processes the request via Telegram messages.

    Args:
        payload: Payload as received.
    """
    logger.debug(payload)
    chat = settings.Chat(**{**payload, **payload["chat"], **payload["from"]})
    if not authenticate(chat):
        logger.warning(payload)
        return
    if not verify_timeout(chat):
        logger.warning(payload)
        return
    if payload.get("text"):
        chat.message_type = "text"
        process_text(chat, settings.Text(**payload))
    elif payload.get("voice"):
        chat.message_type = "voice"
        process_voice(chat, settings.Voice(**payload["voice"]))
    elif payload.get("document"):
        chat.message_type = "document"
        process_document(chat, settings.Document(**payload["document"]))
    elif payload.get("video"):
        chat.message_type = "video"
        process_video(chat, settings.Video(**payload["video"]))
    elif payload.get("audio"):
        chat.message_type = "audio"
        process_audio(chat, settings.Audio(**payload["audio"]))
    elif payload.get("photo"):
        # Matches for compressed images
        chat.message_type = "photo"
        process_photo(chat, [settings.PhotoFragment(**d) for d in payload["photo"]])
    else:
        reply_to(chat, "Payload type is not allowed.")


def authenticate(chat: settings.Chat) -> bool:
    """Authenticates the user with ``userId`` and ``userName``.

    Args:
        chat: Required section of the payload as Chat object.

    Returns:
        bool:
        Returns a boolean to indicate whether the user is authenticated.
    """
    if chat.is_bot:
        logger.error("Bot request from %s", chat.username)
        send_message(
            chat_id=chat.id,
            response=f"Sorry {chat.first_name}! I can't process requests from bots.",
        )
        return False
    if chat.id not in models.env.bot_chat_ids or not username_is_valid(
        username=chat.username
    ):
        logger.error(
            "Unauthorized chatID [%d] or userName [%s]", chat.id, chat["username"]
        )
        send_message(
            chat_id=chat.id, response=f"401 Unauthorized user: ({chat['username']})"
        )
        return False
    if not USER_TITLE.get(chat.username):
        USER_TITLE[chat.username] = get_title_by_name(name=chat.first_name)
    return True


def verify_timeout(chat: settings.Chat) -> bool:
    """Verifies whether the message was received in the past 60 seconds.

    Args:
        chat: Required section of the payload as Chat object.

    Returns:
        bool:
        True or False flag to indicate if the request timed out.
    """
    if int(time.time()) - chat.date < 60:
        return True
    request_time = time.strftime("%m-%d-%Y %H:%M:%S", time.localtime(chat.date))
    logger.warning("Request timed out [%s] for %s", request_time, chat.username)
    reply_to(
        chat,
        f"Request timed out\nRequested: {request_time}\n"
        f"Processed: {time.strftime('%m-%d-%Y %H:%M:%S', time.localtime(time.time()))}",
    )


def verify_stop(chat: settings.Chat, data_class: settings.Text) -> bool:
    """Stops Jarvis by setting stop flag in ``base_db`` if stop is requested by the user with an override flag.

    Args:
        chat: Required section of the payload as Chat object.
        data_class: Required section of the payload as Text object.

    Returns:
        bool:
        Boolean flag to indicate whether to proceed.
    """
    if not word_match.word_match(
        phrase=data_class.text, match_list=keywords.keywords["kill"]
    ):
        return True
    if "override" in data_class.text.lower():
        logger.info("%s requested a STOP override.", chat.username)
        reply_to(
            chat, f"Shutting down now {models.env.title}!\n{support.exit_message()}"
        )
        with models.db.connection as connection:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT or REPLACE INTO stopper (flag, caller) VALUES (?,?);",
                (True, "TelegramAPI"),
            )
            cursor.connection.commit()
    else:
        reply_to(
            chat,
            "Jarvis cannot be stopped via offline communication without the 'override' keyword.",
        )


def process_photo(
    chat: settings.Chat, data_class: List[settings.PhotoFragment]
) -> None:
    """Processes a photo input.

    Args:
        chat: Required section of the payload as Chat object.
        data_class: Required section of the payload as Voice object.
    """
    logger.info(data_class)
    reply_to(
        chat,
        "Image fragments are not supported. If you're sending a compressed image, "
        "please try sending it without compression.",
    )


def process_audio(chat: settings.Chat, data_class: settings.Audio) -> None:
    """Processes an audio input.

    Args:
        chat: Required section of the payload as Chat object.
        data_class: Required section of the payload as Voice object.
    """
    process_document(chat, data_class)


def process_video(chat: settings.Chat, data_class: settings.Video) -> None:
    """Processes a video input.

    Args:
        chat: Required section of the payload as Chat object.
        data_class: Required section of the payload as Voice object.
    """
    process_document(chat, data_class)


def process_voice(chat: settings.Chat, data_class: settings.Voice) -> None:
    """Processes the audio file in payload received after checking for authentication.

    Args:
        chat: Required section of the payload as Chat object.
        data_class: Required section of the payload as Voice object.
    """
    if bytes_obj := _get_file(data_class):
        if data_class.mime_type == "audio/ogg":
            filename = f"{data_class.file_unique_id}.ogg"
        else:
            logger.error("Unknown FileType received.")
            logger.error(data_class)
            reply_to(
                chat,
                "Your voice command was received as an unknown file type: "
                f"{data_class.mime_type}\nPlease try the command as a text.",
            )
            return
        with open(filename, "wb") as file:
            file.write(bytes_obj)
        converted = False
        if models.settings.os == enums.SupportedPlatforms.macOS:
            transcode = audio_handler.audio_converter_mac()
            if transcode and transcode(
                input_file_name=filename, output_audio_format="flac"
            ):
                converted = True
        elif models.settings.os == enums.SupportedPlatforms.windows:
            if audio_handler.audio_converter_win(
                input_filename=filename, output_audio_format="flac"
            ):
                converted = True
        if converted:
            os.remove(filename)
            filename = filename.replace(".ogg", ".flac")
            audio_to_text = tts_stt.audio_to_text(filename=filename)
            if audio_to_text:
                jarvis(audio_to_text, chat)
                return
        else:
            logger.error("Failed to transcode OPUS to Native FLAC")
    else:
        logger.error("Unable to get file for the file id in the payload received.")
        logger.error(data_class)
    # Catches both unconverted source ogg and unconverted audio to text
    title = USER_TITLE.get(chat.username, models.env.title)
    if filename := tts_stt.text_to_audio(
        text=f"I'm sorry {title}! I was unable to process your voice command. "
        "Please try again!"
    ):
        send_audio(filename=filename, chat_id=chat.id)
        os.remove(filename)
    else:
        reply_to(chat, "Failed to convert audio. Please try text input.")


def process_document(
    chat: settings.Chat, data_class: settings.Document | settings.Audio | settings.Video
) -> None:
    """Processes the document in payload received after checking for authentication.

    Args:
        chat: Required section of the payload as Chat object.
        data_class: Required section of the payload as Document object.
    """
    if bytes_obj := _get_file(data_class):
        response = file_handler.put_file(
            filename=data_class.file_name, file_content=bytes_obj
        )
        send_message(chat_id=chat.id, response=response, parse_mode=None)
    else:
        title = USER_TITLE.get(chat.username, models.env.title)
        reply_to(
            chat,
            f"I'm sorry {title}! I was unable to process your document. Please try again!",
            None,
        )


def process_text(chat: settings.Chat, data_class: settings.Text) -> None:
    """Processes the text in payload received after checking for authentication.

    Args:
        chat: Required section of the payload as Chat object.
        data_class: Required section of the payload as Text object.

    See Also:
        - | Requesting files and secrets are considered as special requests, so they cannot be combined with
          | other requests using 'and' or 'also'
    """
    if data_class.text:
        data_class.text = data_class.text.strip()
    else:
        send_message(chat_id=chat.id, response="Un-processable payload")
        return
    if not verify_stop(chat, data_class):
        return
    data_class.text = data_class.text.replace("override", "").replace("OVERRIDE", "")
    text_lower = data_class.text.lower()
    if match_word := word_match.word_match(
        phrase=text_lower,
        match_list=(
            "hey",
            "hola",
            "what's up",
            "ssup",
            "whats up",
            "hello",
            "hi",
            "howdy",
            "hey",
            "chao",
            "hiya",
            "aloha",
        ),
        strict=True,
    ):
        rest_of_msg = data_class.text.replace(match_word, "")
        if not rest_of_msg or "jarvis" in rest_of_msg.strip().lower():
            reply_to(
                chat,
                f"{greeting()} {chat.first_name}!\n"
                f"Good {util.part_of_day()}! How can I be of service today?",
            )
            return
    if data_class.text.startswith("/"):
        # Auto-complete can be setup using "/" commands so ignore if "_" is present
        if "_" not in data_class.text:
            reply_to(
                chat,
                "*Deprecation Notice*\n\nSlash commands ('/') have been deprecated. Please use "
                "commands directly instead.",
            )
        data_class.text = (
            data_class.text.lstrip("/").replace("jarvis", "").replace("_", " ").strip()
        )
    if text_lower == "start":
        send_message(chat.id, f"{greeting()} {chat.first_name}! {intro()}")
        return
    if text_lower == "help":
        send_message(
            chat_id=chat.id,
            response=f"{greeting()} {chat.first_name}!\n"
            f"Good {util.part_of_day()}! {intro()}\n\n"
            "Please reach out at https://vigneshrao.com/contact for more info.",
        )
        return
    if not data_class.text:
        return
    split_text = text_lower.split()
    if ("file" in split_text or "files" in split_text) and (
        "send" in split_text or "get" in split_text or "list" in split_text
    ):
        if "list" in split_text and ("files" in split_text or "file" in split_text):
            # Set parse_mode to an explicit None, so the API doesn't try to parse as HTML or Markdown
            # since the result has file names and paths
            send_message(
                chat_id=chat.id, response=file_handler.list_files(), parse_mode=None
            )
            return
        _, _, filename = data_class.text.partition(" file ")
        if filename:
            response = file_handler.get_file(filename=filename.strip())
            if response["ok"]:
                send_document(filename=response["msg"], chat_id=chat.id)
            else:
                reply_to(chat, response["msg"], None)
        else:
            reply_to(
                chat,
                "No filename was received. "
                "Please include only the filename after the keyword 'file'.",
            )
        return
    if word_match.word_match(
        phrase=data_class.text, match_list=keywords.keywords["restrictions"]
    ):
        try:
            response = restrictions.handle_restrictions(phrase=data_class.text)
        except InvalidArgument as error:
            response = error.__str__()
        send_message(chat_id=chat.id, response=response)
        return
    # this feature for telegram bot relies on Jarvis API to function
    if word_match.word_match(
        phrase=data_class.text, match_list=keywords.keywords["secrets"]
    ) and word_match.word_match(
        phrase=data_class.text, match_list=("list", "get", "send", "create", "share")
    ):
        secret = secure_send.secrets(phrase=data_class.text)
        if secret.token:
            res = (
                "The secret requested can be accessed from '_secure-send_' endpoint using the token below.\n\n"
                "*Note* that the secret cannot be retrieved again using the same token and the token will "
                f"expire in 5 minutes.\n\n{secret.token}"
            )
            send_message(chat_id=chat.id, response=res)
        elif secret.response:
            send_message(chat_id=chat.id, response=secret.response, parse_mode=None)
        else:
            warnings.warn(f"secret appears to be empty: {secret.model_dump()}")
            # SafetyNet: Should never reach this
            send_message(
                chat_id=chat.id,
                response="Something went wrong! Please check the logs for more information.",
                parse_mode=None,
            )
        return
    jarvis(command=data_class.text, chat=chat)


def jarvis(command: str, chat: settings.Chat) -> None:
    """Uses the table ``offline`` in the database to process a response.

    Args:
        command: Command to execute.
        chat: Required section of the payload as Chat object.
    """
    command_lower = command.lower()
    if "alarm" in command_lower or "remind" in command_lower:
        command = command_lower
    if command_lower == "test":
        send_message(chat.id, "Test message received.")
        return

    if " and " in command and not word_match.word_match(
        phrase=command, match_list=keywords.ignore_and
    ):
        and_phrases = command.split(" and ")
        logger.info("Looping through %s in iterations.", and_phrases)
        for each in and_phrases:
            executor(each, chat)
        return

    if " after " in command_lower and not word_match.word_match(
        phrase=command, match_list=keywords.ignore_after
    ):
        if delay_info := commander.timed_delay(phrase=command):
            logger.info("Request: %s", delay_info[0])
            process_response(
                "I will execute it after "
                f"{support.time_converter(second=delay_info[1])} {models.env.title}!",
                chat,
            )
            logger.info(
                "Response: Task will be executed after %d seconds", delay_info[1]
            )
            return
    executor(command, chat)


def executor(command: str, chat: settings.Chat) -> None:
    """Executes the command via offline communicator.

    Args:
        command: Command to be executed.
        chat: Required section of the payload as Chat object.
    """
    ollama_timeout_backed = models.env.ollama_timeout
    # Set to a max timeout of 1 minute to allow longer text conversations
    models.env.ollama_timeout = 60
    logger.info("Request: %s", command)
    try:
        response = offline.offline_communicator(command=command).replace(
            models.env.title, USER_TITLE.get(chat.username)
        )
    except Exception as error:
        logger.error(error)
        logger.error(traceback.format_exc())
        response = f"Jarvis failed to process the request.\n\n`{error}`"
    logger.info("Response: %s", response)
    models.env.ollama_timeout = ollama_timeout_backed
    process_response(response, chat)


def process_response(response: str, chat: settings.Chat) -> None:
    """Processes the response via Telegram API.

    Args:
        response: Response from Jarvis.
        chat: Required section of the payload as Chat object.
    """
    if os.path.isfile(response) and response.endswith("jpg"):
        send_photo(chat.id, response)
        os.remove(response)
        return
    if chat.message_type == "voice":
        filename = tts_stt.text_to_audio(text=response)
        send_audio(chat.id, filename)
        os.remove(filename)
        return
    send_message(chat.id, response, None)
