import io
import pysnooper

def test_invalid_watch_expression_does_not_raise():
    string_io = io.StringIO()

    @pysnooper.snoop(string_io, watch=('1 +',))
    def my_function():
        return 42

    result = my_function()
    assert result == 42
    output = string_io.getvalue()
    assert 'Traceback' not in output
    assert 'SyntaxError' not in output