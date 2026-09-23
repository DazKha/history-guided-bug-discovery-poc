import unittest

from tornado.escape import xhtml_escape


class XhtmlEscapeSingleQuoteTest(unittest.TestCase):
    def test_xhtml_escape_single_quote(self):
        # xhtml_escape is documented to escape HTML-special characters.
        # A single quote is special in HTML attribute contexts and must be
        # escaped to &#39;.
        self.assertEqual(xhtml_escape("'"), "&#39;")

    def test_xhtml_escape_mixed_quotes(self):
        self.assertEqual(xhtml_escape("'\""), "&#39;&quot;")


if __name__ == "__main__":
    unittest.main()

