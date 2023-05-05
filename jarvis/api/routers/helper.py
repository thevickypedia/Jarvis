from fastapi import APIRouter

from jarvis.api.modals.authenticator import OFFLINE_PROTECTOR
from jarvis.modules.conditions import conversation as conversation_mod
from jarvis.modules.conditions import keywords as keywords_mod

router = APIRouter()


@router.get(path="/keywords", dependencies=OFFLINE_PROTECTOR)
async def keywords():
    """Converts the keywords.py file into a dictionary of key-value pairs.

    Returns:

        Dict[str, List[str]]:
        Key-value pairs of the keywords file.
    """
    return {k: v for k, v in keywords_mod.keywords.__dict__.items() if isinstance(v, list)}


@router.get(path="/conversation", dependencies=OFFLINE_PROTECTOR)
async def conversations():
    """Converts the conversation.py file into a dictionary of key-value pairs.

    Returns:

        Dict[str, List[str]]:
        Key-value pairs of the conversation file.
    """
    return {k: v for k, v in conversation_mod.__dict__.items() if isinstance(v, list)}
