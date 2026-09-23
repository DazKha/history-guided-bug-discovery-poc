import io

import pytest

import pysnooper


def test_exception_return_does_not_raise_index_error():
    string_io = io.StringIO()

    @pysnooper.snoop(string_io)
    def my_function():
        raise ValueError('boom')

    with pytest.raises(ValueError, match='boom'):
        my_function()

    output = string_io.getvalue()
    assert 'Call ended by exception' in output

