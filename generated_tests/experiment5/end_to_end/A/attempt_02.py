import unittest
import tornado.escape

class XhtmlEscapeSingleQuoteTest(unittest.TestCase):
    def test_single_quote_escaped(self):
        result = tornado.escape.xhtml_escape("it's")
        self.assertIn("&#39;", result, "Single quote should be escaped to &#39;")
        self.assertNotIn("'", result, "Single quote should not appear unescaped")

if __name__ == "__main__":
    unittest.main()
