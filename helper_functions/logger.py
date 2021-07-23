"""
Initiates logger to log start time, restart time, results from security mode and offline communicator.

In order to use a common logger across multiple files, a dedicated logger has been created.
"""

import logging
from datetime import datetime
from importlib import reload
from os import path

directory = path.dirname(__file__)

reload(logging)
logging.basicConfig(
    filename=datetime.now().strftime(path.join(directory, '../logs/jarvis_%d-%m-%Y_%H_%M_%S.log')), filemode='w',
    format='%(asctime)s - %(levelname)s - %(funcName)s - Line: %(lineno)d - %(message)s',
    datefmt='%b-%d-%Y %H:%M:%S'
)

logger = logging.getLogger('jarvis.py')


# noinspection PyUnresolvedReferences,PyProtectedMember


class TestLogger:
    """This is a class to test logger to verify logging using module references and different logging levels.

    Logging works the same way regardless of callable method, static method, function or class.

    >>> TestLogger

    """

    @staticmethod
    def function1() -> None:
        """This WILL be logged as it is an error info."""
        logger.error(sys._getframe(0).f_code.co_name)
        called_func = sys._getframe(1).f_code.co_name.replace("<module>", __name__)
        parent_func = sys._getframe(2).f_code.co_name.replace("<module>", __name__) if not called_func == '__main__' \
            else None
        logger.error(f'I was called by {called_func} which was called by {parent_func}')

    @staticmethod
    def function2() -> None:
        """This WILL be logged as it is a critical info."""
        logger.critical(sys._getframe(0).f_code.co_name)
        called_func = sys._getframe(1).f_code.co_name.replace("<module>", __name__)
        parent_func = sys._getframe(2).f_code.co_name.replace("<module>", __name__) if not called_func == '__main__' \
            else None
        logger.critical(f'I was called by {called_func} which was called by {parent_func}')
        TestLogger.function1()

    @staticmethod
    def function3() -> None:
        """This WILL be logged as it is a fatal info."""
        logger.fatal(sys._getframe(0).f_code.co_name)
        called_func = sys._getframe(1).f_code.co_name.replace("<module>", __name__)
        parent_func = sys._getframe(2).f_code.co_name.replace("<module>", __name__) if not called_func == '__main__' \
            else None
        logger.fatal(f'I was called by {called_func} which was called by {parent_func}')
        TestLogger.function2()

    @staticmethod
    def function4() -> None:
        """This WILL NOT be logged as no logger level is set."""
        logger.info('function 4')

    @staticmethod
    def function5() -> None:
        """This WILL NOT be logged as no logger level is set."""
        logger.debug('function 5')


if __name__ == '__main__':
    import sys
    TestLogger.function3()
    TestLogger.function4()
    TestLogger.function5()
    for method_name, return_value in TestLogger.__dict__.items():
        if type(return_value) == staticmethod:
            print(return_value.__func__ or return_value.__get__(TestLogger))
