import io
import pytest
import pysnooper


def test_exception_ended_by_exception_line():
    string_io = io.StringIO()

    @pysnooper.snoop(string_io)
    def my_function():
        raise ValueError('boom')

    with pytest.raises(ValueError):
        my_function()

    output = string_io.getvalue()
    assert 'Call ended by exception' in output

