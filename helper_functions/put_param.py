from os import system

from boto3 import client

from creds import Credentials
from helper_functions.logger import logger


class AWSClient:
    """Class to initiate AWS ssm client.

    >>> AWSClient

    """

    def __init__(self):
        self.client = client('ssm')
        self.cred = Credentials()

    def put_parameters(self, name: str, value: str):
        """Uses boto3 to update credentials in AWS and returns 200 if successful.

        Args:
            name: Name of the parameter that has to dropped in AWS.
            value: Value of the parameter that has to dropped in AWS as SecureString.

        """
        response = self.client.put_parameter(Name=f'/Jarvis/{name}', Value=value, Type='SecureString', Overwrite=True)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            logger.critical(f'Parameter {name} has been updated on SSM parameter store.')
            logger.warning(f'Update your ENV VAR:{name}={value}')
            system(f"""osascript -e 'display notification "Update your ENV VAR:{name}={value}" with title "Jarvis"'""")
        else:
            logger.error(f'Parameter {name} WAS NOT added to SSM parameter store.')
        data = self.cred.get()
        data[name] = value
        self.cred.put(data)
        logger.critical(f'Parameter {name} has been updated in params.json.')
