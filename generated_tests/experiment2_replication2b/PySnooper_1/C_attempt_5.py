import io
import pytest
import pysnooper


def test_exception_trace_does_not_crash_tracer():
    string_io = io.StringIO()

    @pysnooper.snoop(string_io)
    def my_function():
        x = 1
        raise ValueError('boom')

    with pytest.raises(ValueError, match='boom'):
        my_function()

    output = string_io.getvalue()
    assert 'ValueError' in output
    assert 'boom' in output

