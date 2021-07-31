from os import environ

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from models import GetData


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
    """# Offline Communicator for Jarvis

    ## Args:
    - **input_data:** - Takes the following arguments as data instead of a QueryString.
        - **command:** The task which Jarvis has to do.
        - **passphrase:** Pass phrase for authentication.

    ## Returns:
    - A dictionary with the command requested and the response for it from Jarvis.

    ## See Also:
    - Include response_model only when the response should have same keys as arguments
        - @app.post("/offline-communicator", response_model=GetData)

    """
    passphrase = input_data.phrase
    command = input_data.command
    if passphrase == environ.get('offline_phrase'):
        with open('../offline_request', 'w') as off_file:
            off_file.write(command)
        return {"status": "SUCCESS", "description": "Request will be processed by Jarvis."}
    else:
        return {"status": "FAILED", "description": "Auth failed"}


origins = [
    "http://localhost.com",
    "https://localhost.com",
    "https://thevickypedia.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # allow_origin_regex='https://.*\.ngrok.io',  # noqa: W605
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == '__main__':
    from uvicorn import run

    # noinspection PyTypeChecker
    run(app=app, port=4483)
