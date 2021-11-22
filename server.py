import argparse
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
def process_client_message(message, messages_list, client, clients, names):
    """
    Validate message from client
    :param names:
    :param clients:
    :param client:
    :param messages_list:
    :param message:
    :return:
    """
    _logger.debug(f'Message from client: {message}')
    if ACTION in message and \
            message[ACTION] == PRESENCE \
            and TIME in message \
            and USER in message:
        if message[USER][ACCOUNT_NAME] not in names.keys():
            names[message[USER][ACCOUNT_NAME]] = client
            send_message(client, RESPONSE_200)
        else:
            response = RESPONSE_400
            response[ERROR] = 'username is used'
            send_message(client, response)
            clients.remove(client)
            client.close()
        return
    elif ACTION in message \
            and message[ACTION] == MESSAGE \
            and DESTINATION in message \
            and TIME in message \
            and SENDER in message \
            and MESSAGE_TEXT in message:
        messages_list.append(message)
        return
    elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
        try:
            clients.remove(names[message[ACCOUNT_NAME]])
        except:
            pass
        try:
            names.pop(message[ACCOUNT_NAME]).close()
        except:
            pass
        return
    else:
        response = RESPONSE_400
        response[ERROR] = 'Bad request'
        send_message(client, response)
        return


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


def main():
    args = _parse_args()
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((args.server_address, args.port))

        server_socket.listen(MAX_CONNECTIONS)
        server_socket.settimeout(0.5)
    except Exception as e:
        print("server start failed", e)
        sleep(10)
        raise e
    _logger.info(f'server start at {args.server_address}:{args.port}')
    print(f'server start at {args.server_address}:{args.port}')
    clients = []
    messages = []
    names = dict()

    while True:
        try:
            conn, client_address = server_socket.accept()
        except Exception:
            pass
        else:
            clients.append(conn)
            _logger.info(f'connection complete {client_address}')
            print(f'connection complete {client_address}')

        rlist = []
        wlist = []
        try:
            if clients:
                rlist, wlist, _ = select(clients, clients, [], 0)
        except OSError:
            pass

        if rlist:
            for _client in rlist:
                try:
                    process_client_message(get_message(_client), messages, _client, clients, names)
                except (ConnectionResetError, JSONDecodeError):
                    _logger.info(f'{_client} disconnected.')
                    clients.remove(_client)

        if messages and wlist:
            _msg = messages.pop()
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
                    clients.remove(waiting_client)

            for i in messages:
                try:
                    if message[DESTINATION] in names \
                            and names[message[DESTINATION]] in wlist:
                        send_message(names[message[DESTINATION]], message)
                        _logger.info(f'{message[SENDER]} send message to {message[DESTINATION]}')
                    elif message[DESTINATION] in names and names[message[DESTINATION]] not in wlist:
                        raise ConnectionError
                    else:
                        _logger.error(
                            f'bad user {message[DESTINATION]}')
                except Exception:
                    _logger.info(f'connection with {i[DESTINATION]} lost')
                    clients.remove(names[i[DESTINATION]])
                    names.pop(i[DESTINATION])
            messages.clear()


if __name__ == '__main__':
    main()
