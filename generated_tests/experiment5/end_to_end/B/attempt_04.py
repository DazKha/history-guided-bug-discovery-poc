import unittest
import tornado.escape


class TestEscapeNonAscii(unittest.TestCase):
    def test_xhtml_escape_non_ascii(self):
        result = tornado.escape.xhtml_escape(u'\u00e9\u00e8\u00e0')
        self.assertEqual(result, u'\u00e9\u00e8\u00e0')

    def test_xhtml_escape_special_chars(self):
        result = tornado.escape.xhtml_escape(u'<b>&"\'')
        self.assertEqual(result, u'&lt;b&gt;&amp;&quot;&#39;')

    def test_url_escape_non_ascii(self):
        result = tornado.escape.url_escape(u'\u00e9\u00e8\u00e0')
        self.assertEqual(result, u'%C3%A9%C3%A8%C3%A0')

    def test_url_escape_plus(self):
        result = tornado.escape.url_escape(u'a b')
        self.assertEqual(result, u'a+b')

    def test_json_encode_non_ascii(self):
        result = tornado.escape.json_encode(u'\u00e9\u00e8\u00e0')
        self.assertIn(u'\u00e9', result)


if __name__ == '__main__':
    unittest.main()

