import tornado.escape

def test_xhtml_escape_single_quote():
    result = tornado.escape.xhtml_escape("'")
    assert result != "'", f"xhtml_escape did not escape single quote: {result!r}"

