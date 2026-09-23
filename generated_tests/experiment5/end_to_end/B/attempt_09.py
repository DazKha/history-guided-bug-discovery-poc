import tornado.escape


def test_xhtml_escape_escapes_apostrophe():
    result = tornado.escape.xhtml_escape("it's")
    assert "'" not in result, (
        "xhtml_escape left a literal apostrophe unescaped: %r" % result
    )
    assert "&#39;" in result or "&#x27;" in result, (
        "xhtml_escape did not produce an apostrophe entity: %r" % result
    )


def test_xhtml_escape_escapes_double_quote():
    result = tornado.escape.xhtml_escape('say "hi"')
    assert '"' not in result, (
        "xhtml_escape left a literal double quote unescaped: %r" % result
    )
    assert "&quot;" in result, (
        "xhtml_escape did not produce a double-quote entity: %r" % result
    )

