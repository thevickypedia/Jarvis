"""Initiates logger to log start time, restart time, results from security mode and offline communicator
In order to use a common logger across multiple files, a dedicated logger has been created."""

from logging import basicConfig, getLogger

basicConfig(
    filename='threshold.log', filemode='a',
    format='%(asctime)s - %(levelname)s - %(funcName)s - Line: %(lineno)d - %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p'
)

logger = getLogger('jarvis.py')
# noinspection PyUnresolvedReferences,PyProtectedMember


class CheckLogger:
    """Logging works the same way regardless of callable method, static method, function or class"""

    @staticmethod
    def function1():
        """This WILL be logged as it is an error info"""
        logger.error(sys._getframe(0).f_code.co_name)
        called_func = sys._getframe(1).f_code.co_name.replace("<module>", __name__)
        parent_func = sys._getframe(2).f_code.co_name.replace("<module>", __name__) if not called_func == '__main__' \
            else None
        logger.error(f'I was called by {called_func} which was called by {parent_func}')

    @staticmethod
    def function2():
        """This WILL be logged as it is a critical info"""
        logger.critical(sys._getframe(0).f_code.co_name)
        called_func = sys._getframe(1).f_code.co_name.replace("<module>", __name__)
        parent_func = sys._getframe(2).f_code.co_name.replace("<module>", __name__) if not called_func == '__main__' \
            else None
        logger.critical(f'I was called by {called_func} which was called by {parent_func}')
        CheckLogger.function1()

    @staticmethod
    def function3():
        """This WILL be logged as it is a fatal info"""
        logger.fatal(sys._getframe(0).f_code.co_name)
        called_func = sys._getframe(1).f_code.co_name.replace("<module>", __name__)
        parent_func = sys._getframe(2).f_code.co_name.replace("<module>", __name__) if not called_func == '__main__' \
            else None
        logger.fatal(f'I was called by {called_func} which was called by {parent_func}')
        CheckLogger.function2()

    @staticmethod
    def function4():
        """This WILL NOT be logged as no logger level is set"""
        logger.info('function 4')

    @staticmethod
    def function5():
        """This WILL NOT be logged as no logger level is set"""
        logger.debug('function 5')


if __name__ == '__main__':
    import sys
    CheckLogger.function3()
    CheckLogger.function4()
    CheckLogger.function5()
    for method_name, return_value in CheckLogger.__dict__.items():
        if type(return_value) == staticmethod:
            print(return_value.__func__ or return_value.__get__(CheckLogger))
