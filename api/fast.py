from logging import Filter, LogRecord, getLogger
from os import environ, path, remove
from threading import Thread
from time import sleep

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from models import GetData


class EndpointFilter(Filter):
    """Class to initiate endpoint filter in logs while preserving other access logs.

    >>> EndpointFilter

    """

    def filter(self, record: LogRecord) -> bool:
        """Filter out the mentioned `/endpoint` from log streams.

        Args:
            record: LogRecord represents an event which is created every time something is logged.

        Returns:
            bool:
            False flag for the endpoint that needs to be filtered.

        """
        return record.getMessage().find("/docs") == -1


getLogger("uvicorn.access").addFilter(EndpointFilter())


app = FastAPI(
    title="Jarvis API",
    description="Jarvis API and webhooks",
    version="v1.0"
)


@app.get('/', response_class=RedirectResponse, include_in_schema=False)
async def redirect_index():
    """Redirect to documents."""
    return '/docs'


@app.get('/status', include_in_schema=False)
def status():
    """Health Check for OfflineCommunicator."""
    return {'Message': 'Healthy'}


@app.post("/offline-communicator")
def read_root(input_data: GetData):
    """# Offline Communicator for Jarvis.

    ## Args:
        - input_data: - Takes the following arguments as data instead of a QueryString.
            - command: The task which Jarvis has to do.
            - passphrase: Pass phrase for authentication.

    ## Returns:
        - A dictionary with the command requested and the response for it from Jarvis.

    ## See Also:
        - Include response_model only when the response should have same keys as arguments
            - @app.post("/offline-communicator", response_model=GetData)
    """
    passphrase = input_data.phrase
    command = input_data.command
    if passphrase.startswith('\\'):  # Since passphrase is converted to Hexadecimal using a JavaScript in JarvisHelper
        passphrase = bytes(passphrase, "utf-8").decode(encoding="unicode_escape")
    if passphrase == environ.get('offline_phrase'):
        if command.lower() == 'test':
            raise HTTPException(status_code=200, detail='Test message has been received.')
        else:
            with open('../offline_request', 'w') as off_request:
                off_request.write(command)
            while True:
                if path.isfile('../offline_response'):
                    with open('../offline_response', 'r') as off_response:
                        if response := off_response.read():
                            Thread(target=delete_file).start()
                            raise HTTPException(status_code=200, detail=response)
    else:
        raise HTTPException(status_code=401, detail='Request not authorized.')


def delete_file() -> None:
    """Delete the ``offline_response`` file created by ``Jarvis`` after 2 seconds."""
    sleep(2)
    remove('../offline_response')


website = environ.get('website', 'thevickypedia.com')

origins = [
    "http://localhost.com",
    "https://localhost.com",
    f"http://{website}",
    f"https://{website}",
    f"http://{website}/*",
    f"https://{website}/*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex='https://.*\.ngrok\.io/*',  # noqa: W605
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == '__main__':
    from uvicorn import run

    run("fast:app", port=4483, reload=True)
