from pydantic import BaseModel


class GetData(BaseModel):
    """BaseModel that handles input data for the API which is treated as members for the class ``GetData``.

    See Also:
        - ``command``: Offline command sent via API which ``Jarvis`` has to perform.
        - ``phrase``: Secret phrase to authenticate the request sent to the API.

    """

    phrase: str = None
    command: str = None
