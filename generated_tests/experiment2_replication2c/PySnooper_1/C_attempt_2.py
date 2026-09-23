import io
import pytest
import pysnooper


def test_exception_message_in_output():
    string_io = io.StringIO()

    @pysnooper.snoop(string_io)
    def my_function():
        raise ValueError('boom')

    with pytest.raises(ValueError, match='boom'):
        my_function()

    output = string_io.getvalue()
    assert 'Call ended by exception' in output
    assert 'ValueError: boom' in output

