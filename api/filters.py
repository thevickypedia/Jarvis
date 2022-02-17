from logging import Filter, LogRecord


class InvestmentFilter(Filter):
    """Class to initiate ``/investment`` filter in logs while preserving other access logs.

    >>> InvestmentFilter

    See Also:
        - Overrides logging by implementing a subclass of ``logging.Filter``
        - The method ``filter(record)``, that examines the log record and returns True to log it or False to discard it.

    """

    def filter(self, record: LogRecord) -> bool:
        """Filter out logging at ``/investment?token=`` from log streams.

        Args:
            record: ``LogRecord`` represents an event which is created every time something is logged.

        Returns:
            bool:
            False flag for the endpoint that needs to be filtered.
        """
        return record.getMessage().find("/investment?token=") == -1
