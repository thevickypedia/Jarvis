from os import path
from json import load, dump


class Credentials:
    """Reads all the required oauth and api keys stored in params.json file.

    >>> Credentials

    """

    def __init__(self):
        self.file = 'params.json'
        self.directory = path.dirname(__file__)

    def get(self):
        """Reads credentials stored in params.json file and returns a dictionary.

        Returns:
            A dictionary of parameters stored key-value pairs present in params.json.

        """
        return load(open(path.join(self.directory, self.file)))

    def put(self, params: dict):
        """Dumps the parameters into params.json file.

        Args:
            params: Takes the credentials key-value pair as an argument.
        """
        with open(path.join(self.directory, self.file), 'w') as write_file:
            dump(params, write_file, indent=2, allow_nan=False)
