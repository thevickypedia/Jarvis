from json import dump, load
from os import path, remove


class Credentials:
    """Reads all the required oauth and api keys stored in credentials.json file.

    >>> Credentials

    """

    def __init__(self):
        self.file = 'credentials.json'
        self.directory = path.dirname(__file__)

    def get(self) -> dict:
        """Reads credentials stored in credentials.json file and returns a dictionary.

        Returns:
            dict:
            A dictionary of parameters stored key-value pairs present in credentials.json.

        """
        return load(open(path.join(self.directory, self.file)))

    def put(self, params: dict) -> None:
        """Dumps the parameters into credentials.json file.

        Args:
            params: Takes the credentials key-value pair as an argument.

        """
        remove(self.file)
        with open(path.join(self.directory, self.file), 'w') as write_file:
            dump(params, write_file, indent=2, allow_nan=False)
