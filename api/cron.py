import os
from datetime import datetime
from logging import Logger

from crontab import CronTab

from api.rh_helper import MarketHours
from modules.models import models

env = models.env


class CronScheduler:
    """Initiates CronScheduler object to check for existing schedule and add if not.

    >>> CronScheduler

    """

    COMMAND = f"cd {os.getcwd()} && source venv/bin/activate && python api/report_gatherer.py && deactivate"

    def __init__(self, logger: Logger):
        """Instantiates ``CronTab`` object and ``Logger`` class.

        Args:
            logger: Takes the class ``logging.Logger`` as an argument.
        """
        self.logger = logger
        self.cron = CronTab(user=True)

    def checker(self) -> bool:
        """Checks if an existing cron schedule for ``robinhood`` is present.

        Returns:
            bool:
            True if an existing schedule is found.
        """
        if not self.cron:
            self.logger.warning(f"No crontab was found for {env.root_user}.")
            return False
        for job in self.cron:
            if job.is_enabled() and job.command == self.COMMAND:
                self.logger.info(f"Existing crontab schedule found for {env.root_user}")
                return True

    def scheduler(self, start: int, end: int, weekend: bool = False) -> None:
        """Creates a crontab schedule to run every 30 minutes between the ``start`` and ``end`` time.

        Args:
            start: Time when the schedule starts every day.
            end: Time when the schedule ends every day.
            weekend: Takes a boolean flag to decide whether the cron has to be scheduled for weekends.
        """
        self.logger.info('Creating a new cron schedule.')
        job = self.cron.new(command=self.COMMAND)
        job.minute.every(30)
        job.hours.during(vfrom=start, vto=end)
        if weekend:
            job.dow.during(vfrom=0, vto=6)  # Week starts on Sunday which is 0 and ends on Saturday which is 6
        else:
            job.dow.during(vfrom=1, vto=5)
        self.cron.write()

    def controller(self, hours_type: str = 'EXTENDED') -> None:
        """Determines the start and end time based on the current timezone.

        Args:
            hours_type: Takes either ``EXTENDED`` or ``REGULAR`` as argument.
        """
        if self.checker():
            return
        self.logger.info(f'Type: {hours_type} market hours.')
        tz = datetime.utcnow().astimezone().tzname()
        data = MarketHours.hours
        start = data[hours_type][tz]['OPEN']
        end = data[hours_type][tz]['CLOSE']
        self.scheduler(start=start, end=end)


if __name__ == '__main__':
    from logging import DEBUG, Formatter, StreamHandler, getLogger

    formatter = Formatter('%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s')
    handler = StreamHandler()
    handler.setFormatter(formatter)

    module_logger = getLogger(__name__)
    module_logger.addHandler(handler)
    module_logger.setLevel(DEBUG)

    CronScheduler(module_logger).controller()
