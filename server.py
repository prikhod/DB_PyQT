import argparse
import dis
import inspect
import logging
from json import JSONDecodeError
from time import time, sleep

import logger.server_log_config
from logger.func_logger import Log
from select import select
import socket

from common.utils import get_message, send_message, port, server_ip
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, MESSAGE_TEXT, MESSAGE, SENDER, RESPONSE_200, RESPONSE_400, DESTINATION, \
    EXIT

_logger = logging.getLogger('server')


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
        default='0.0.0.0',
        help='server ip address.',
    )
    args = parser.parse_args()
    return args


class Port:
    def __init__(self, value=7777):
        self._value = value

    def __get__(self, instance, instance_type):
        return self._value

    def __set__(self, instance, value):
        if not isinstance(value, int):
            raise TypeError("Int type required")
        if not 1024 <= value <= 49151:
            raise argparse.ArgumentTypeError(f'port must be in range [1024,49151]')
        self._value = value


class ServerVerifier(type):
    def __init__(self, clsname, bases, clsdict):
        is_sock_stream = False

        for key, value in clsdict.items():
            if isinstance(value, socket.socket):
                raise TypeError(f"Don't create socket in class!")

            if value != 'Port':
                try:
                    instrs = dis.get_instructions(value)
                    for instr in instrs:
                        if instr.argval == 'socket':
                            _next_instr = next(instrs)
                            if _next_instr.argval == 'SOCK_STREAM':
                                is_sock_stream = True
                            if _next_instr.argval == 'connect':
                                raise TypeError(f"Call connect in server!")
                except TypeError:
                    pass
        if not is_sock_stream:
            raise TypeError(f"Use SOCK_STREAM!")
        type.__init__(self, clsname, bases, clsdict)


class Server(metaclass=ServerVerifier):
    _port = Port()

    def __init__(self):
        args = _parse_args()
        try:
            _server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._port = args.port
            _server_socket.bind((args.server_address, self._port))

            _server_socket.listen(MAX_CONNECTIONS)
            _server_socket.settimeout(0.5)
        except Exception as e:
            print("server start failed", e)
            sleep(10)
            raise e
        self.server_socket = _server_socket
        _logger.info(f'server start at {args.server_address}:{self._port}')
        print(f'server start at {args.server_address}:{self._port}')
        self.clients = []
        self.messages = []
        self.names = dict()

    @Log(_logger)
    def process_client_message(self, message, client):
        """
        Validate message from client
        :param client:
        :param message:
        :return:
        """
        _logger.debug(f'Message from client: {message}')
        if ACTION in message and \
                message[ACTION] == PRESENCE \
                and TIME in message \
                and USER in message:
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'username is used'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and DESTINATION in message \
                and TIME in message \
                and SENDER in message \
                and MESSAGE_TEXT in message:
            self.messages.append(message)
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            try:
                self.clients.remove(self.names[message[ACCOUNT_NAME]])
            except:
                pass
            try:
                self.names.pop(message[ACCOUNT_NAME]).close()
            except:
                pass
            return
        else:
            response = RESPONSE_400
            response[ERROR] = 'Bad request'
            send_message(client, response)
            return

    def run(self):
        while True:
            try:
                conn, client_address = self.server_socket.accept()
            except Exception:
                pass
            else:
                self.clients.append(conn)
                _logger.info(f'connection complete {client_address}')
                print(f'connection complete {client_address}')

            rlist = []
            wlist = []
            try:
                if self.clients:
                    rlist, wlist, _ = select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            if rlist:
                for _client in rlist:
                    try:
                        self.process_client_message(get_message(_client), _client)
                    except (ConnectionResetError, JSONDecodeError):
                        _logger.info(f'{_client} disconnected.')
                        self.clients.remove(_client)

            if self.messages and wlist:
                _msg = self.messages.pop()
                print(f'current message: {_msg}')
                message = {
                    ACTION: MESSAGE,
                    SENDER: _msg[SENDER],
                    DESTINATION: _msg[DESTINATION],
                    TIME: time(),
                    MESSAGE_TEXT: _msg[MESSAGE_TEXT]
                }
                for waiting_client in wlist:
                    try:
                        send_message(waiting_client, message)
                        print(f'message sent: {message}')
                    except:
                        _logger.info(f'{waiting_client} disconnected.')
                        print(f'{waiting_client} disconnected.')
                        self.clients.remove(waiting_client)

                for i in self.messages:
                    try:
                        if message[DESTINATION] in self.names \
                                and self.names[message[DESTINATION]] in wlist:
                            send_message(self.names[message[DESTINATION]], message)
                            _logger.info(f'{message[SENDER]} send message to {message[DESTINATION]}')
                        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in wlist:
                            raise ConnectionError
                        else:
                            _logger.error(
                                f'bad user {message[DESTINATION]}')
                    except Exception:
                        _logger.info(f'connection with {i[DESTINATION]} lost')
                        self.clients.remove(self.names[i[DESTINATION]])
                        self.names.pop(i[DESTINATION])
                self.messages.clear()


if __name__ == '__main__':
    server = Server()
    server.run()
