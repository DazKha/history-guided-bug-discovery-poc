import io
import sys

import pytest

import pysnooper


def test_trace_restored_after_exception_in_with_block():
    string_io = io.StringIO()
    snoop = pysnooper.snoop(string_io)

    original_trace = sys.gettrace()

    with pytest.raises(RuntimeError):
        with snoop:
            raise RuntimeError('boom')

    assert sys.gettrace() is original_trace

