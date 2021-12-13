import os
import logging.handlers
from common.variables import LOGGING_LEVEL

formatter = logging.Formatter('%(asctime)-30s %(levelname)-10s %(module)-20s %(message)-10s')
log_file = os.path.join('log/', 'server.log')

file_hndlr = logging.handlers.TimedRotatingFileHandler(log_file, encoding='utf8', interval=1, when='D')
file_hndlr.setFormatter(formatter)

logger = logging.getLogger('server')
logger.addHandler(file_hndlr)
logger.setLevel(LOGGING_LEVEL)


if __name__ == '__main__':
    logger.critical('Критическая ошибка')
    logger.error('Ошибка')
    logger.debug('Отладочная информация')
    logger.info('Информационное сообщение')
