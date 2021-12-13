import inspect
import os
import traceback


class Log:
    def __init__(self, logger=None):
        if logger:
            self._logger = logger
        elif os.path.basename(traceback.format_stack()[0].strip().split()[1].strip(',').strip('"')) == 'server.py':
            import logging
            import logger.server_log_config
            self._logger = logging.getLogger('server')
        elif os.path.basename(traceback.format_stack()[0].strip().split()[1].strip(',').strip('"')) == 'client.py':
            import logging
            import logger.client_log_config
            self._logger = logging.getLogger('client')
        else:
            t = traceback.format_stack()
            f = os.path.basename(traceback.format_stack()[0].strip().split()[1].strip(',').strip('"'))
            # raise ModuleNotFoundError(f'{f} not valid file')

    def __call__(self, func):
        def decorated(*args, **kwargs):
            res = func(*args, **kwargs)
            self._logger.debug(
                f'called func "{func.__name__}" args params: {args}, kwargs params: {kwargs}; '
                f'module: "{func.__module__}"; '
                f'func: "{traceback.format_stack()[0].strip().split()[-1]}"; '
                f'file: "{os.path.basename(inspect.stack()[1][1])}"',
                stacklevel=2
            )
            return res

        return decorated
