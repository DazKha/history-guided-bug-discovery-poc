import tornado.escape


def test_xhtml_escape_escapes_single_quote():
    escaped = tornado.escape.xhtml_escape("'")
    assert "'" not in escaped, (
        "xhtml_escape left a raw single quote in the output: %r" % escaped
    )

