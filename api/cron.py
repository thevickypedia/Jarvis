from datetime import datetime
from os import environ, getcwd

from crontab import CronTab


class CronScheduler:
    """Initiates CronScheduler object to check for existing schedule and add if not.

    >>> CronScheduler

    """

    def __init__(self, logger):
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
            self.logger.warning(f"No crontab was found for {environ.get('USER')}.")
            return False
        for job in self.cron:
            if job.is_enabled() and 'report_gatherer.py' in str(job):
                self.logger.info(f"Existing crontab schedule found for {environ.get('USER')}")
                return True

    def scheduler(self, start: int, end: int) -> None:
        """Creates a crontab schedule to run every 30 minutes between the ``start`` and ``end`` time.

        Args:
            start: Time when the schedule starts everyday.
            end: Time when the schedule ends everyday.
        """
        self.logger.info('Creating a new cron schedule.')
        entry = f"cd {getcwd()} && source ../venv/bin/activate && python report_gatherer.py && deactivate"
        job = self.cron.new(command=entry)
        job.minute.every(30)
        job.hours.during(vfrom=start, vto=end)
        job.dow.during(vfrom=1, vto=5)
        self.cron.write()

    def controller(self, hours_type: str = 'EXTENDED') -> None:
        """Determines the start and end time based on the current timezone.

        Args:
            hours_type: Takes either ``EXTENDED`` or ``REGULAR`` as argument.
        """
        if self.checker():
            return
        from rh_helper import MarketHours
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
