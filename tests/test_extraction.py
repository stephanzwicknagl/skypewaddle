import unittest
import pandas as pd
import extraction.get_conversations
import extraction.get_calls


class TestExtraction(unittest.TestCase):
    """
    def test_extraction(self):
        self.assertEqual(1, 1)
    """
    def test_conversations(self):
        input = "./tests/test_data/mock.json"

        options, indexes = extraction.get_conversations.extract_conversations(
            input, test=True)

        self.assertEqual(options, ['8:BBB'])
        self.assertEqual(indexes, {'8:BBB': 0})

    def test_calls(self):
        input = "./tests/test_data/mock.json"

        expected_result = pd.read_csv("./tests/test_data/mock.csv").set_index('Call ID')

        result = extraction.get_calls.get_calls(input, 0, "Europe/Berlin")

        # why does this comparison fail?
        self.assertTrue(result.equals(expected_result))

