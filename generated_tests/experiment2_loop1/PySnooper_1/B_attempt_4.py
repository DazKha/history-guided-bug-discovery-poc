import io
import sys

import pysnooper


def test_with_block_restores_trace_on_exception():
    string_io = io.StringIO()
    snoop = pysnooper.snoop(string_io)

    original_trace = sys.gettrace()
    assert original_trace is None

    try:
        with snoop:
            raise ValueError('boom')
    except ValueError:
        pass

    assert sys.gettrace() is original_trace

