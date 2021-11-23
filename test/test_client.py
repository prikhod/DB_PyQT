import sys
sys.path.insert(0, '..')
import unittest
from datetime import datetime
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from client import create_presence, process_answer


class TestClient(unittest.TestCase):

    def test_create_presence(self):
        data = create_presence()
        _now = datetime.now()
        data[TIME] = _now
        self.assertEqual(data, {
            ACTION: PRESENCE,
            TIME: _now,
            USER: {
                ACCOUNT_NAME: 'Guest'
            }
        })

    def test_200_process_answer(self):
        answer = process_answer({RESPONSE: 200})
        self.assertEqual(answer, '200: OK')

    def test_400_process_answer(self):
        error_message = 'Bad Request'
        answer = process_answer({RESPONSE: 400, ERROR: error_message})
        self.assertEqual(answer, f'400: {error_message}')

    def test_bad_response_process_answer(self):
        error_message = 'Bad Request'
        with self.assertRaises(ValueError):
            process_answer({RESPONSE: 200, ERROR: error_message})


if __name__ == '__main__':
    unittest.main()
