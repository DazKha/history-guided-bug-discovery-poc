import io
import sys

import pytest

import pysnooper


def test_trace_restored_after_exception_in_with_block():
    string_io = io.StringIO()
    original_trace = sys.gettrace()

    with pytest.raises(ValueError):
        with pysnooper.snoop(string_io):
            raise ValueError('boom')

    assert sys.gettrace() is original_trace

