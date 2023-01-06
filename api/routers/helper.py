from typing import Dict, List

from fastapi import APIRouter

from api.modals.authenticator import OFFLINE_PROTECTOR
from modules.conditions import conversation as conversation_mod
from modules.conditions import keywords as keywords_mod
from modules.offline import compatibles

router = APIRouter()


@router.get(path="/keywords", dependencies=OFFLINE_PROTECTOR)
async def keywords() -> Dict[str, List[str]]:
    """Converts the keywords.py file into a dictionary of key-value pairs.

    Returns:

        dict:
        Key-value pairs of the keywords file.
    """
    return {k: v for k, v in keywords_mod.keywords.__dict__.items() if isinstance(v, list)}


@router.get(path="/conversation", dependencies=OFFLINE_PROTECTOR)
async def conversations() -> Dict[str, List[str]]:
    """Converts the conversation.py file into a dictionary of key-value pairs.

    Returns:

        dict:
        Key-value pairs of the conversation file.
    """
    return {k: v for k, v in conversation_mod.__dict__.items() if isinstance(v, list)}


@router.get(path="/api-compatible", dependencies=OFFLINE_PROTECTOR)
async def offline_compatible() -> Dict[str, List[str]]:
    """Returns the list of api compatible words.

    Returns:

        dict:
        Returns the list of api-compatible words as a dictionary.
    """
    return {"compatible": compatibles.offline_compatible()}
