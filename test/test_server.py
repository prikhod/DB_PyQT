import sys
sys.path.insert(0, '..')
import unittest
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from server import process_client_message


class TestServer(unittest.TestCase):
    good_response = {RESPONSE: 200}
    bad_response = {RESPONSE: 400, ERROR: 'Bad Request'}

    good_request = {ACTION: PRESENCE, TIME: 1, USER: {ACCOUNT_NAME: 'Guest'}}
    bad_request_without_action = {TIME: 1, USER: {ACCOUNT_NAME: 'Guest'}}
    bad_request_without_time = {ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Guest'}}
    bad_request_bad_time = {ACTION: PRESENCE, TIME: 'a', USER: {ACCOUNT_NAME: 'Guest'}}
    bad_request_without_user = {ACTION: PRESENCE, TIME: 1}
    bad_request_bad_user = {ACTION: PRESENCE, TIME: 1, USER: {ACCOUNT_NAME: 'User'}}
    bad_request_unnecessary_params = {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}, "unnecessary": "param"}

    def test_without_action(self):
        self.assertEqual(process_client_message(self.bad_request_without_action), self.bad_response)

    def test_without_time(self):
        self.assertEqual(process_client_message(self.bad_request_without_time), self.bad_response)

    def test_bad_time(self):
        self.assertEqual(process_client_message(self.bad_request_bad_time), self.bad_response)

    def test_without_user(self):
        self.assertEqual(process_client_message(self.bad_request_without_user), self.bad_response)

    def test_bad_user(self):
        self.assertEqual(process_client_message(self.bad_request_bad_user), self.bad_response)

    def test_unnecessary_params(self):
        self.assertEqual(process_client_message(self.bad_request_unnecessary_params), self.bad_response)

    def test_ok(self):
        self.assertEqual(process_client_message(self.good_request), self.good_response)


if __name__ == '__main__':
    unittest.main()
