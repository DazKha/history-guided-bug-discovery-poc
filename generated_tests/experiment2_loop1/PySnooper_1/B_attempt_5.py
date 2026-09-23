import io
import sys

import pysnooper


def test_with_block_restores_trace_on_exception():
    string_io = io.StringIO()
    original_trace = sys.gettrace()

    try:
        with pysnooper.snoop(string_io):
            raise ValueError('boom')
    except ValueError:
        pass

    assert sys.gettrace() is original_trace

