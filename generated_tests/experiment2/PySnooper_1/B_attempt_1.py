import io
import sys

import pysnooper


def test_with_block_exception_restores_trace():
    original_trace = sys.gettrace()
    string_io = io.StringIO()
    snoop = pysnooper.snoop(string_io)

    try:
        with snoop:
            raise ValueError('boom')
    except ValueError:
        pass

    assert sys.gettrace() is original_trace

