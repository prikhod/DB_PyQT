import argparse
import json
import logging
import threading
import socket
import time
import uuid
from json import JSONDecodeError
import inspect

import logger.client_log_config
from logger.func_logger import Log
from common.utils import get_message, send_message, port, server_ip
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT, MESSAGE, MESSAGE_TEXT, SENDER, DESTINATION, EXIT
from exceptions import BadMessageError

_logger = logging.getLogger('client')
lock = threading.Lock()


@Log(_logger)
def _parse_args():
    parser = argparse.ArgumentParser(description="Messenger client")
    parser.add_argument(
        '--port',
        '-p',
        type=port,
        required=False,
        default=DEFAULT_PORT,
        help='server port.'
    )

    parser.add_argument(
        '--server_address',
        '-a',
        type=server_ip,
        required=False,
        default=DEFAULT_IP_ADDRESS,
        help='server ip address.'
    )
    parser.add_argument(
        '--name',
        '-n',
        required=False,
        default=f'Guest{uuid.uuid4().__str__()}',
        help='username in chat.'
    )
    return parser.parse_args()


class ClientVerifier(type):
    def __init__(self, clsname, bases, clsdict):
        for key, value in clsdict.items():
            if isinstance(value, socket.socket):
                raise TypeError(f"Don't create socket in class!")

            if callable(value):
                lines = inspect.getsource(value).split('\n')
                for line in lines:
                    if '.accept' in line or '.listen' in line:  # парсим код на наличие вызовов ???
                        raise TypeError(f"Don't call accept() or listen() in client!")

        type.__init__(self, clsname, bases, clsdict)


class Client(metaclass=ClientVerifier):
    def __init__(self):
        args = _parse_args()

        _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            _sock.connect((args.server_address, args.port))
        except ConnectionRefusedError as e:
            _logger.critical(f'connection server failed {args.server_address}:{args.port}')
            time.sleep(1)
            raise e
        else:
            _logger.info(f'Client started. user={args.name}, server={args.server_address}, port={args.port}')
            print(f'Client started. user={args.name}, server={args.server_address}, port={args.port}')
        self.sock = _sock
        if not args.name:
            self.username = input('Введите имя пользователя: ')
        else:
            self.username = args.name

    @Log(_logger)
    def create_presence(self):
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.username
            }
        }
        _logger.debug(f'create_presence account_name={self.username}, ACTION={ACTION}: PRESENCE={PRESENCE}')
        return out

    @Log(_logger)
    def message_from_server(self):
        while True:
            try:
                message = get_message(self.sock)
                if ACTION in message \
                        and message[ACTION] == MESSAGE \
                        and SENDER in message \
                        and DESTINATION in message \
                        and MESSAGE_TEXT in message \
                        and message[DESTINATION] == self.username:
                    log_info = f'\nReceived message from {message[SENDER]}: {message[MESSAGE_TEXT]}'
                    print(log_info)
                    _logger.info(log_info)
                else:
                    _logger.error(f'bad message from server: {message}')
            except BadMessageError:
                _logger.error(f'Cannot decode message')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, JSONDecodeError):
                _logger.critical(f'connection lost')
                break

    @Log(_logger)
    def create_message(self):
        with lock:
            message = input('Input message  ')
            user = input('Input username  ')

        if message == '':
            return
        message_dict = {
            ACTION: MESSAGE,
            TIME: time.time(),
            DESTINATION: user,
            ACCOUNT_NAME: self.username,
            SENDER: self.username,
            MESSAGE_TEXT: message
        }
        _logger.info(f'message to sent: {message_dict}')
        try:
            send_message(self.sock, message_dict)
            _logger.info(f'send message to {user}')
        except:
            _logger.critical('connection lost')
            exit(1)

    @staticmethod
    @Log(_logger)
    def process_answer(response):
        _logger.debug(f'message {response}')
        if RESPONSE in response:
            if response[RESPONSE] == 200 and len(response.keys()) == 1:
                return '200: OK'
            if response[RESPONSE] == 400 and len(response.keys()) == 2:
                return f'400: {response[ERROR]}'
        raise BadMessageError

    def run(self):
        message_to_server = self.create_presence(self.username)
        send_message(self.sock, message_to_server)
        try:
            msg = get_message(self.sock)
            answer = self.process_answer(msg)
            _logger.info(f'server response {answer}')
        except json.JSONDecodeError as e:
            _logger.error(f'cannot decode message. {e}')
        except BadMessageError as e:
            _logger.error(f'{e}')
        else:
            user_receiver = threading.Thread(target=self.message_from_server)
            user_receiver.daemon = True
            user_receiver.start()
            user_process = threading.Thread(target=self.process)
            user_process.daemon = True
            user_process.start()
            _logger.debug('started')
            while user_receiver.is_alive() and user_process.is_alive():
                time.sleep(1)

    @Log(_logger)
    def process(self):
        while True:
            with lock:
                command = input('input command(message or exit): ')
            if command == 'message':
                self.create_message()
            elif command == 'exit':
                send_message(self.sock, {ACTION: EXIT, TIME: time.time(), ACCOUNT_NAME: self.username})
                with lock:
                    print('connection close')
                _logger.info('connection close')
                time.sleep(0.5)
                break
            else:
                with lock:
                    print('bad command, try once')


if __name__ == '__main__':
    client = Client()
    client.run()
