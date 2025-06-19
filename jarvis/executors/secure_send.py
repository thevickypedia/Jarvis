from typing import Any, List

import boto3
from pydantic import BaseModel

from jarvis.executors import ciphertext, files
from jarvis.modules.exceptions import InvalidArgument
from jarvis.modules.logger import logger
from jarvis.modules.models import models
from jarvis.modules.utils import util

# set to be accessible only via offline communicators
# WATCH OUT: for changes in function name
if models.settings.pname in ("jarvis_api", "telegram_api"):
    SECRET_STORAGE = {"aws": [], "local": []}
    SESSION = boto3.Session()
    SECRET_CLIENT = SESSION.client(service_name="secretsmanager")
    SSM_CLIENT = SESSION.client(service_name="ssm")


def get_aws_secrets(name: str = None) -> str | List[str]:
    """Get secrets from AWS secretsmanager.

    Args:
        name: Get name of the particular secret.

    Returns:
        str | List[str]:
        Returns the value of the secret or list of all secrets' names.
    """
    if name:
        response = SECRET_CLIENT.get_secret_value(SecretId=name)
        return response["SecretString"]
    paginator = SECRET_CLIENT.get_paginator("list_secrets")
    page_results = paginator.paginate().build_full_result()
    return [page["Name"] for page in page_results["SecretList"]]


def get_aws_params(name: str = None) -> str | List[str]:
    """Get SSM parameters from AWS.

    Args:
        name: Get name of the particular parameter.

    Returns:
        str | List[str]:
        Returns the value of the parameter or list of all parameter names.
    """
    if name:
        response = SSM_CLIENT.get_parameter(Name=name, WithDecryption=True)
        return response["Parameter"]["Value"]
    paginator = SSM_CLIENT.get_paginator("describe_parameters")
    page_results = paginator.paginate().build_full_result()
    return [page["Name"] for page in page_results["Parameters"]]


def format_secret(secret: Any) -> list | dict | str | int | float | bool | None:
    """Format secrets into primitive and non-primitive data types.

    Args:
        secret: Secret value of any data type.

    Returns:
        list | dict | str | int | float | bool | None:
        Returns the formatted secret.
    """
    if isinstance(secret, dict):
        return {str(k): format_secret(v) for k, v in secret.items()}
    elif isinstance(secret, list):
        return [format_secret(item) for item in secret]
    elif isinstance(secret, (str, int, float, bool)) or secret is None:
        return secret
    # elif hasattr(secret, '__dict__'):
    #     return format_secret(vars(secret))
    elif hasattr(secret, "__str__") and not isinstance(secret, (str, bytes)):
        return str(secret)
    elif hasattr(secret, "__iter__") and not isinstance(secret, (str, bytes)):
        return [format_secret(item) for item in secret]
    else:
        # Fallback: convert unknown types to string
        return str(secret)


def store_secret(key: str, value: Any) -> str:
    """Stores the secret in the secure-send yaml file.

    Args:
        key: Key for payload.
        value: Value for payload.

    Returns:
        str:
        Returns the generate key that is used as identifier for the payload.
    """
    if value is None:
        logger.warning("Received a null value for '%s'", key)
        raise InvalidArgument(f"Received a null value for {key!r}")
    keygen = util.keygen_uuid()
    formatted_secret = format_secret(secret=value)
    encrypted_secret = ciphertext.encrypt(payload=formatted_secret)
    files.put_secure_send(data={keygen: {key: encrypted_secret}})
    return keygen


class SecretResponse(BaseModel):
    """Base model to store secret response from the server.

    >>> SecretResponse

    """

    response: str | None = None
    token: str | None = None


def secrets(phrase: str) -> SecretResponse | None:
    """Handle getting secrets from AWS or local env vars.

    Args:
        phrase: Takes the phrase spoken as an argument.

    Returns:
        SecretResponse:
        Response the SecretResponse object with the server response and the token.
    """
    text = phrase.lower().split()

    if "create" in text or "share" in text:
        before, part, after = phrase.partition("for")
        if custom_secret := after.strip():
            return SecretResponse(token=store_secret(key="secret", value=custom_secret))
        else:
            return SecretResponse(
                response="Please specify the secret to create after the keyword 'for'\n"
                "example: create and share secret for drogon589#"
            )

    # Calling list will always create a new list in the dict regardless of what exists
    if "list" in text:
        if "aws" in text:
            SECRET_STORAGE["aws"] = []  # reset everytime list param is called
            if "ssm" in text or "params" in text or "parameters" in text:
                try:
                    SECRET_STORAGE["aws"].extend(get_aws_params())
                except Exception as error:
                    logger.error(error)
            else:
                try:
                    SECRET_STORAGE["aws"].extend(get_aws_secrets())
                except Exception as error:
                    logger.error(error)
            return SecretResponse(
                response=", ".join(SECRET_STORAGE["aws"])
                if SECRET_STORAGE["aws"]
                else "No parameters were found"
            )
        if "local" in text:
            SECRET_STORAGE["local"] = list(models.env.__dict__.keys())
            return SecretResponse(response=", ".join(SECRET_STORAGE["local"]))
        return SecretResponse(
            response="Please specify which secrets you want to list: 'aws' or 'local''"
        )

    # calling get will always return the latest information in the existing dict
    if "get" in text or "send" in text:
        if "aws" in text:
            if SECRET_STORAGE["aws"]:
                if aws_key := [
                    key for key in phrase.split() if key in SECRET_STORAGE["aws"]
                ]:
                    aws_key = aws_key[0]
                else:
                    return SecretResponse(
                        response="No AWS params were found matching your request."
                    )
            else:
                return SecretResponse(
                    response="Please use 'list secret' before using 'get secret'"
                )
            if "ssm" in text or "params" in text or "parameters" in text:
                try:
                    return SecretResponse(
                        token=store_secret(
                            key=aws_key, value=get_aws_params(name=aws_key)
                        )
                    )
                except Exception as error:  # if secret is removed between 'list' and 'get'
                    logger.error(error)
            else:
                try:
                    return SecretResponse(
                        token=store_secret(
                            key=aws_key, value=get_aws_secrets(name=aws_key)
                        )
                    )
                except Exception as error:  # if secret is removed between 'list' and 'get'
                    logger.error(error)
            return SecretResponse(response=f"Failed to retrieve {aws_key!r}")
        if "local" in text:
            if not SECRET_STORAGE["local"]:
                SECRET_STORAGE["local"] = list(models.env.__dict__.keys())
            if local_key := [
                key for key in phrase.split() if key in SECRET_STORAGE["local"]
            ]:
                local_key = local_key[0]
            else:
                return SecretResponse(
                    response="No local params were found matching your request."
                )
            return SecretResponse(
                token=store_secret(key=local_key, value=models.env.__dict__[local_key])
            )
        return SecretResponse(
            response="Please specify which type of secret you want the value for: 'aws' or 'local'"
        )
