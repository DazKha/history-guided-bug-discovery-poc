import unittest

from tornado.escape import xhtml_escape


class XhtmlEscapeSingleQuoteTest(unittest.TestCase):
    def test_single_quote_is_escaped(self):
        escaped = xhtml_escape("'")
        self.assertNotIn("'", escaped)
        self.assertIn("&#x27;", escaped)


if __name__ == "__main__":
    unittest.main()

