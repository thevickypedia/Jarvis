# noinspection PyUnresolvedReferences
"""Module for speech-synthesis running on a docker container.

>>> SpeechSynthesis

"""

import os
import subprocess
import time
from typing import NoReturn

import docker
import psutil
import requests
from docker.client import DockerClient
from docker.errors import APIError, ContainerError, DockerException, NotFound

from jarvis.executors import port_handler, process_map
from jarvis.modules.exceptions import EgressErrors
from jarvis.modules.logger import logger, multiprocessing_logger
from jarvis.modules.models import models


def find_pid_by_port(port: int) -> int:
    """Find the PID of the process using a specific port number.

    Args:
        port: Port number that the process is listening to.

    Returns:
        int:
        ID of the process that's listening to the port.
    """
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr.port == port:
                return conn.pid
    except psutil.Error as error:
        # network connections aren't available via psutil for macOS
        if models.settings.os != models.supported_platforms.macOS:
            logger.error(error)
    try:
        result = subprocess.run(
            ["lsof", "-i", f":{port}", "-t"], capture_output=True, text=True
        )
        if result.returncode == 0:
            return int(result.stdout.strip())
    except (
        subprocess.CalledProcessError,
        subprocess.SubprocessError,
        FileNotFoundError,
    ) as error:
        if isinstance(error, subprocess.CalledProcessError):
            result = error.output.decode(encoding="UTF-8").strip()
            logger.error("[%d]: %s", error.returncode, result)
        else:
            logger.error(error)


def check_existing() -> bool:
    """Checks for existing connection.

    Returns:
        bool:
        A boolean flag whether a valid connection is present.
    """
    if port_handler.is_port_in_use(port=models.env.speech_synthesis_port):
        logger.info("%d is currently in use.", models.env.speech_synthesis_port)
        try:
            res = requests.get(
                url=f"http://{models.env.speech_synthesis_host}:{models.env.speech_synthesis_port}",
                timeout=1,
            )
            if res.ok:
                logger.info(
                    "http://{host}:{port} is accessible.".format(
                        host=models.env.speech_synthesis_host,
                        port=models.env.speech_synthesis_port,
                    )
                )
                return True
            return False
        except EgressErrors as error:
            logger.error(error)
            if not port_handler.kill_port_pid(port=models.env.speech_synthesis_port):
                logger.critical(
                    "ATTENTION::Failed to kill existing PID. Attempting to re-create session."
                )


def run_existing_container(client: DockerClient, verified: bool = False) -> str | None:
    """Tries to run the container if a container ID is present in the CID file in fileio directory.

    Args:
        client: DockerClient object.
        verified: Boolean flag to simply validate the container ID and return it.

    See Also:
        - .cid file should exist with a valid container ID to tun speech synthesis
        - Checks if the container state has been exited, not running and not dead.
        - If at least one of the condition doesn't match, removes the container.

    Returns:
        str:
        Container ID.
    """
    try:
        with open(models.fileio.speech_synthesis_cid) as file:
            container_id = file.read()
        if not container_id.strip():
            raise FileNotFoundError
    except FileNotFoundError:
        if verified:
            logger.info("Container ID not found")
        return
    try:
        container = client.containers.get(container_id)
        if verified:
            return container.id
        state = container.attrs.get("State")
        if any(
            (
                state["Running"],
                state["Dead"],
                state["ExitCode"],
                state["Error"],
                state["OOMKilled"],
            )
        ):
            logger.info(
                "Purging available container [%s] since one or more reuse conditions weren't met",
                container.id,
            )
            container.remove()
            return
        logger.info(
            "Starting available container [%s] since all the reuse conditions were met",
            container.id,
        )
        container.start()
        # Just because the container ID is valid, it doesn't mean
        #   it belongs to speech-synthesis, or it runs and maps the expected port
        time.sleep(5)
        if check_existing():
            return container.id
        else:
            logger.warning(
                "Container ID is valid, but API is unreachable. Hence removing container."
            )
            container.remove()
    except NotFound as error:
        logger.warning(error.explanation)
    except ContainerError as error:
        err = f": {error.stderr}" if error.stderr else ""
        logger.error(
            "Command '{}' in image '{}' returned non-zero exit status {}{}",
            error.command,
            error.image,
            error.exit_status,
            err,
        )
    except DockerException as error:
        logger.critical(error.__str__())


def run_new_container(client: DockerClient) -> str:
    """Spins up a new docker container for speech-synthesis. Pulls the image if not found locally.

    Args:
        client: DockerClient object.

    Returns:
        str:
        Container ID.
    """
    models.env.home = str(models.env.home)
    try:
        # This may take a while depending on image availability
        logger.info("Spinning up a new docker container to run speech-synthesis API")
        result = client.containers.run(
            image="thevickypedia/speech-synthesis",
            ports={"5002/tcp": models.env.speech_synthesis_port},
            environment=[f"HOME={models.env.home}"],
            volumes={models.env.home: {"bind": models.env.home, "mode": "rw"}},
            working_dir=os.getcwd(),
            user=f"{os.getuid()}:{os.getgid()}",
            detach=True,
            restart_policy={"Name": "on-failure", "MaximumRetryCount": 10},
        )
        return result.id
    except ContainerError as error:
        # should never get here since detach flag is set to true
        err = f": {error.stderr}" if error.stderr else ""
        logger.error(
            "Command '{}' in image '{}' returned non-zero exit status {}{}",
            error.command,
            error.image,
            error.exit_status,
            err,
        )
    except APIError as error:
        logger.error(error.explanation)


def stream_logs(client: DockerClient, container_id: str) -> NoReturn:
    """Stream logs into the log file specific for speech synthesis.

    Args:
        client: DockerClient object.
        container_id: Container ID.
    """
    logs = client.api.logs(
        container=container_id,
        stdout=True,
        stderr=True,
        stream=True,
        timestamps=True,
        tail="all",
        since=None,
        follow=None,
        until=None,
    )
    log_file = open(
        file=models.fileio.speech_synthesis_log, mode="a", buffering=1
    )  # 1 line buffer on file
    os.fsync(log_file.fileno())  # Tell os module to write the buffer of the file
    __asterisks = "".join(["*" for _ in range(120)])
    __spaces = "".join(["-" for _ in range(47)])
    log_file.write(f"\n{__asterisks}\n")
    log_file.write(f"{__spaces} STREAMING CONTAINER LOGS {__spaces}\n")
    log_file.write(f"{__asterisks}\n\n")
    for line in logs:
        log_file.write(line.decode(encoding="UTF-8"))
        log_file.flush()  # Write everything in buffer to file right away
    log_file.close()


def speech_synthesis_api() -> None:
    """Initiates speech synthesis API using docker."""
    multiprocessing_logger(filename=models.fileio.speech_synthesis_log)
    try:
        docker_client = docker.from_env()
    except DockerException as error:
        logger.critical(error.__str__())
        return
    if check_existing():  # Test call to speech synthesis API successful
        # Map existing API session with docker
        if container_id := run_existing_container(docker_client, True):
            logger.info("Dry run successful, streaming logs")
            stream_logs(docker_client, container_id)
        logger.warning("Unable to stream container logs locally")
        # Container logs will not be available outside docker, so try to update the process map with docker's PID
        # Identified the PID to update in process map
        if pid := find_pid_by_port(models.env.speech_synthesis_port):
            process_map.update(speech_synthesis_api.__name__, models.settings.pid, pid)
        else:
            # Failed to get the PID of the listening API, hence removing entry from process map
            process_map.remove(speech_synthesis_api.__name__)
        return

    container_id = run_existing_container(docker_client) or run_new_container(
        docker_client
    )
    if not container_id:
        return
    # Due to lack of a "cidfile" flag, create one manually
    with open(models.fileio.speech_synthesis_cid, "w") as file:
        file.write(container_id)
    logger.info(f"Started speech synthesis in docker container {container_id!r}")
    if models.env.speech_synthesis_port != 5002:
        logger.info(
            "Docker port 5002 has been mapped to %d on localhost",
            models.env.speech_synthesis_port,
        )
    stream_logs(docker_client, container_id)
