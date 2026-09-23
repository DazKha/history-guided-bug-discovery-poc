import io
import pytest
import pysnooper


def test_exception_call_ended_by_exception_marker():
    string_io = io.StringIO()

    @pysnooper.snoop(string_io)
    def my_function():
        x = 1
        raise ValueError('boom')

    with pytest.raises(ValueError, match='boom'):
        my_function()

    output = string_io.getvalue()
    assert 'Call ended by exception' in output

