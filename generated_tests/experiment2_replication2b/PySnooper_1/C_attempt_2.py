import io
import pytest
import pysnooper


def test_exception_trace_does_not_report_normal_return():
    string_io = io.StringIO()

    @pysnooper.snoop(string_io)
    def my_function():
        x = 7
        raise ValueError('boom')

    with pytest.raises(ValueError, match='boom'):
        my_function()

    output = string_io.getvalue()
    assert 'ValueError: boom' in output
    assert 'Call ended by exception' in output
    assert 'Return value:..' not in output

