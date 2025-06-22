"""Tables to create in the base DB. SQLite is a "typeless" database, so the column types are inferred with affinity."""

from typing import Sequence

from pydantic import BaseModel

from jarvis.modules.models.classes import env


class Table(BaseModel):
    """Object to store table information.

    >>> Table

    """

    name: str
    columns: Sequence[str]
    pkey: str | None = None
    keep: bool = False


class Tables(BaseModel):
    """Table objects to be created in the base DB.

    >>> Tables

    """

    party: Table = Table(name="party", columns=("pid",), keep=True)
    fernet: Table = Table(name="fernet", columns=("key",), pkey="key")
    ics: Table = Table(name="ics", columns=("info", "date"), pkey="date")
    vpn: Table = Table(name="vpn", columns=("state",), pkey="state", keep=True)
    guard: Table = Table(name="guard", columns=("state", "trigger"), pkey="state")
    robinhood: Table = Table(name="robinhood", columns=("summary",), pkey="summary")
    restart: Table = Table(name="restart", columns=("flag", "caller"), pkey="caller")
    stopper: Table = Table(name="stopper", columns=("flag", "caller"), pkey="caller")
    listener: Table = Table(
        name="listener", columns=("state",), pkey="state", keep=True
    )
    events: Table = Table(
        name=env.event_app or "calendar", columns=("info", "date"), pkey="date"
    )
    children: Table = Table(
        name="children",
        columns=(
            "meetings",
            "events",
            "crontab",
            "party",
            "guard",
            "surveillance",
            "plot_mic",
            "undefined",
        ),
    )


tables = Tables()
