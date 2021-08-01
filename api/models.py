from pydantic import BaseModel


class GetData(BaseModel):
    """Default values for the input data."""

    phrase: str = None
    command: str = None
