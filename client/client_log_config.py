import os
import logging
from common.variables import LOGGING_LEVEL

formatter = logging.Formatter('%(asctime)-30s %(levelname) -10s %(module)-20s %(message)-10s')
log_file = os.path.join('log/', 'client.log')

file_hndlr = logging.FileHandler(log_file, encoding='utf8')
file_hndlr.setFormatter(formatter)

logger = logging.getLogger('client')
logger.addHandler(file_hndlr)
logger.setLevel(LOGGING_LEVEL)


if __name__ == '__main__':
    logger.critical('Критическая ошибка')
    logger.error('Ошибка')
    logger.debug('Отладочная информация')
    logger.info('Информационное сообщение')
