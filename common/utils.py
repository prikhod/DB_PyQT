import argparse
import ipaddress
import json
import sys

from common.variables import MAX_PACKAGE_LENGTH, ENCODING
from logger.func_logger import Log


@Log()
def get_message(socket):
    """
    Receive and decode message
    :param socket: client socket
    :return: dict with response
    """

    encoded_response = socket.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


@Log()
def send_message(socket, message):
    """
    Encoding message and send to socket
    :param socket: socket
    :param message: dict with message
    :return:
    """

    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    socket.send(encoded_message)


def port(p):
    try:
        p = int(p)
    except ValueError:
        raise argparse.ArgumentTypeError(f'port {p} does not valid!')

    if 1024 <= p <= 49151:
        return p
    raise argparse.ArgumentTypeError(f'port {p} does not valid!')


def server_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return ip
    except ValueError:
        raise argparse.ArgumentTypeError(f'address {ip} does not valid!')
