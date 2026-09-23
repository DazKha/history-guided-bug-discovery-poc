import unittest
import tornado.escape

class XhtmlEscapeSingleQuoteTest(unittest.TestCase):
    def test_single_quote_escaped(self):
        escaped = tornado.escape.xhtml_escape("'")
        self.assertNotIn("'", escaped, "xhtml_escape left a literal single quote unescaped")
        self.assertIn(escaped, ("&#39;", "&apos;"), "xhtml_escape did not produce a recognized single-quote entity")

if __name__ == '__main__':
    unittest.main()
