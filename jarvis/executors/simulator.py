import os
import time
from datetime import datetime
from multiprocessing import Process
from typing import Dict, List, NoReturn

import gmailconnector
import yaml

from jarvis.executors import offline, word_match
from jarvis.modules.audio import speaker
from jarvis.modules.logger import config
from jarvis.modules.logger.custom_logger import logger
from jarvis.modules.models import models
from jarvis.modules.offline import compatibles
from jarvis.modules.utils import shared, support


def get_simulation_data() -> Dict[str, List[str]]:
    """Reads the simulation file and loads it as a dictionary.

    Returns:
        Dict[str, List[str]]:
        Returns the required data to run the simulation.
    """
    if os.path.isfile(models.fileio.simulation):
        with open(models.fileio.simulation) as file:
            try:
                data = yaml.load(stream=file, Loader=yaml.FullLoader)
            except yaml.YAMLError as error:
                logger.error(error)
            else:
                return data


def initiate_simulator(simulation_data: Dict[str, List[str]]) -> NoReturn:
    """Runs simulation on a preset of phrases.

    Args:
        simulation_data: A key value pair of category and phrase list.
    """
    start = time.time()
    log_file = config.multiprocessing_logger(filename=os.path.join('logs', 'simulation_%d-%m-%Y_%H:%M_%p.log'))
    offline_compatible = compatibles.offline_compatible()
    successful, failed = 0, 0
    shared.called_by_offline = True
    for category, task_list in simulation_data.items():
        logger.info("Requesting category: %s", category)
        for task in task_list:
            if not word_match.word_match(phrase=task, match_list=offline_compatible):
                logger.warning("'%s' is not an offline compatible request.", task)
                continue
            logger.info("Request: %s", task)
            try:
                response = offline.offline_communicator(command=task)
            except Exception as error:
                failed += 1
                logger.error(error)
            else:
                if not response or response.startswith("I was unable to process"):
                    failed += 1
                else:
                    successful += 1
                    logger.info("Response: %s", response)
    shared.called_by_offline = False
    with open(log_file) as file:
        errors = len(file.read().split('ERROR')) - 1
    mail_obj = gmailconnector.SendEmail(gmail_user=models.env.open_gmail_user, gmail_pass=models.env.open_gmail_pass)
    mail_res = mail_obj.send_email(subject=f"Simulation results - {datetime.now().strftime('%c')}",
                                   attachment=log_file, recipient=models.env.recipient, sender="Jarvis Simulator",
                                   body=f"Total simulations attempted: {sum(len(i) for i in simulation_data.values())}"
                                        f"\n\nSuccessful: {successful}\n\nFailed: {failed}\n\nError-ed: {errors}\n\n"
                                        f"Run Time: {support.time_converter(second=time.time() - start)}")
    if mail_res.ok:
        logger.info("Test result has been sent via email")
    else:
        logger.critical("ATTENTION::Failed to send test results via email")
        logger.critical(mail_res.json())


def simulation(*args) -> NoReturn:
    """Initiates simulation in a dedicated process logging into a dedicated file."""
    simulation_data = get_simulation_data()
    if not simulation_data:
        speaker.speak(f"There are no metrics for me to run a simulation {models.env.title}!")
        return
    process = Process(target=initiate_simulator, args=(simulation_data,))
    process.name = "simulator"
    process.start()
    speaker.speak(text=f"Initiated simulation {models.env.title}! "
                       "I will send you an email with the results once it is complete.")
