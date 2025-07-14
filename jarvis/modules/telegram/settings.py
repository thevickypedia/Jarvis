"""Telegram settings with different types of objects and members as received in the payload."""

from pydantic import BaseModel


class Chat(BaseModel):
    """Base class for Chat model."""

    message_id: int
    message_type: str = None
    date: int

    first_name: str
    last_name: str
    id: int
    type: str
    username: str
    is_bot: bool
    language_code: str


# Below are the DataClass objects
class Text(BaseModel):
    """Base class for Text model."""

    text: str


class PhotoFragment(BaseModel):
    """Base class for PhotoFragment model."""

    file_id: str
    file_size: int
    file_unique_id: str
    height: int
    width: int


class Audio(BaseModel):
    """Base class for Audio model."""

    duration: int
    file_id: str
    file_name: str
    file_size: int
    file_unique_id: str
    mime_type: str


class Voice(BaseModel):
    """Base class for Voice model."""

    duration: int
    file_id: str
    file_size: int
    file_unique_id: str
    mime_type: str


class Document(BaseModel):
    """Base class for Document model."""

    file_id: str
    file_name: str
    file_size: int
    file_unique_id: str
    mime_type: str


class Video(BaseModel):
    """Base class for Video model."""

    duration: int
    file_id: str
    file_name: str
    file_size: int
    file_unique_id: str
    height: int
    mime_type: str
    width: int

    class Thumb(BaseModel):
        """Nested class for Thumb model."""

        file_id: str
        file_size: int
        file_unique_id: str
        height: int
        width: int

    class Thumbnail(BaseModel):
        """Nested class for Thumbnail model."""

        file_id: str
        file_size: int
        file_unique_id: str
        height: int
        width: int
