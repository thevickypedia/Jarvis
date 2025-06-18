import ast
from typing import Any

from cryptography.fernet import Fernet

from jarvis.modules.models import models


def encrypt(payload: Any) -> str:
    """Encrypts the payload using Fernet symmetric encryption.

    Args:
        payload: Payload to be encrypted, can be of any data type.

    Returns:
        str:
        Encrypted payload as a string.
    """
    fernet = Fernet(models.get_fernet_key())
    encoded_payload = str(payload).encode()
    encrypted_payload = fernet.encrypt(encoded_payload)
    return encrypted_payload.decode()


def decrypt(encrypted_payload: str) -> Any:
    """Decrypts the encrypted payload using Fernet symmetric encryption.

    Args:
        encrypted_payload: Encrypted payload as bytes.

    Returns:
        Any:
        Decrypted payload, which can be of any data type.
    """
    fernet = Fernet(models.get_fernet_key())
    decrypted_payload = fernet.decrypt(encrypted_payload)
    decoded_payload = decrypted_payload.decode()
    try:
        return ast.literal_eval(decoded_payload)
    except (ValueError, SyntaxError):
        return decoded_payload


if __name__ == "__main__":
    p = {"key": "value", "nested": {"a": "b", "c": [1, 2, 3]}}
    assert p == decrypt(encrypt(p))
