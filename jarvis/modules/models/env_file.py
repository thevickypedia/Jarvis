"""Module to load the environment variable containing the path to a dotenv file that holds the required secrets.

The module first checks the environment variable options for the dotenv file path.
If none are found, it falls back to the default file.

**Jarvis**

- Options: ``JARVIS_ENV`` or ``ENV_FILE``
- Default: ``.jarvis.env``

**Vault**

- Options: ``VAULT_ENV`` or ``ENV_FILE``
- Default: ``.vault.env``

See Also:
    Refer `VaultAPI documentation <https://github.com/thevickypedia/VaultAPI/>`__ for a secure and seamless integration.
"""

import os
import sys
from typing import List, Optional, Union

from pydantic import BaseModel, Field, FilePath

if sys.version_info.minor > 10:
    pass
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """Override for python 3.10 due to lack of StrEnum."""


def get_env(keys: List[str], default: str = None) -> str | None:
    """Get environment variables with case insensitivity.

    Args:
        keys: Options for the key.
        default: Default value.

    Returns:
        str:
        Returns the value for the given key.
    """
    for _key, _value in os.environ.items():
        if _key.lower() in keys:
            return _value
    return default


class EnvFile(BaseModel):
    """Object to handle env files.

    >>> EnvFile

    Attributes:
        default: Default env file to look for.
        options: Options for env file in existing env vars.
        filepath: Loaded filepath for the env file.
    """

    default: Optional[str] = Field(default=None)
    options: Optional[List[str]] = Field(default=None)
    filepath: Optional[FilePath] = Field(default=None)

    @classmethod
    def from_preset(cls, options: List[str], default: str) -> Union["EnvFile", None]:
        """Loads ``EnvFile`` object from preset values.

        Args:
            options: Different options to consider when looking for env file.
            default: Default env filename.

        Returns:
            Union[EnvFile, None]:
            Returns the ``EnvFile`` object if file exists.
        """
        filepath = FilePath(get_env(keys=options, default=default))
        if filepath.exists():
            return cls(default=default, options=options, filepath=filepath)
        else:
            return None


jarvis = EnvFile.from_preset(options=["jarvis_env", "env_file"], default=".jarvis.env")
vault = EnvFile.from_preset(options=["vault_env", "env_file"], default=".vault.env")
