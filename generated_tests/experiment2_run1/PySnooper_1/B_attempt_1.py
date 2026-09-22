import io
import sys

import pysnooper


def test_reuse_tracer_across_with_blocks():
    string_io = io.StringIO()
    snoop = pysnooper.snoop(string_io)

    original_trace = sys.gettrace()

    def inner(x):
        y = x + 1
        return y

    with snoop:
        a = inner(1)

    assert a == 2
    assert sys.gettrace() is original_trace

    with snoop:
        b = inner(2)

    assert b == 3
    assert sys.gettrace() is original_trace

    output = string_io.getvalue()
    assert 'y = x + 1' in output
    assert output.count('y = x + 1') >= 2

