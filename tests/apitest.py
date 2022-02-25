import pytest


@pytest.fixture(scope="session")
def server():
    """Run pytest on APIServer which runs in a thread."""
    server = ...
    with server.run_in_parallel():
        yield
