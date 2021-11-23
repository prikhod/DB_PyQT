import sys
sys.path.insert(0, '..')
import argparse
import unittest
import json
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE, ENCODING
from common.utils import get_message, send_message, port, server_ip


class TestSocket:

    def __init__(self, message):
        self.message = message
        self.encoded_message = None
        self.received_message = None

    def send(self, message_to_send):
        json_test_message = json.dumps(self.message)
        self.encoded_message = json_test_message.encode(ENCODING)
        self.received_message = message_to_send

    def recv(self, dummy):
        json_test_message = json.dumps(self.message)
        return json_test_message.encode(ENCODING)


class Tests(unittest.TestCase):

    def setUp(self):
        self.good_request = {ACTION: PRESENCE, TIME: 1, USER: {ACCOUNT_NAME: 'Guest'}}
        self.good_response = {RESPONSE: 200}
        self.bad_response = {RESPONSE: 400, ERROR: 'Bad Request'}

    def test_send_message(self):
        socket = TestSocket(self.good_request)
        send_message(socket, self.good_request)
        self.assertEqual(socket.encoded_message, socket.received_message)

    def test_send_message_exception(self):
        socket = TestSocket(self.good_request)
        send_message(socket, self.good_request)
        with self.assertRaises(Exception):
            send_message(socket, json)

    def test_get_good_message(self):
        socket_good = TestSocket(self.good_response)
        self.assertEqual(get_message(socket_good), self.good_response)

    def test_get_bad_message(self):
        socket_bad = TestSocket(self.bad_response)
        self.assertEqual(get_message(socket_bad), self.bad_response)

    def test_port_valid(self):
        p = port('3333')
        self.assertTrue(isinstance(p, int))

    def test_port_invalid(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            port('333333')

    def test_serverip_valid(self):
        raised = False
        try:
            server_ip('127.0.0.127')
        except argparse.ArgumentTypeError:
            raised = True
        self.assertFalse(raised)

    def test_serverip_invalid(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            server_ip('127.0.0')


if __name__ == '__main__':
    unittest.main()
