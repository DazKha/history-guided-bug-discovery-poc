import tornado.escape


def test_xhtml_escape_single_quote():
    assert tornado.escape.xhtml_escape("'") == "&#39;"

