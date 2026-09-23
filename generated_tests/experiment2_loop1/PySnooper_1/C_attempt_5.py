import sys
import io
import pysnooper


def test_tracer_restores_original_trace_function_on_reuse():
    original_trace = sys.gettrace()
    string_io = io.StringIO()
    snoop = pysnooper.snoop(string_io)

    def foo(x):
        return x + 1

    with snoop:
        result1 = foo(1)
    assert result1 == 2
    assert sys.gettrace() is original_trace, (
        'sys.gettrace() was not restored after first with-block: '
        'expected %r, got %r' % (original_trace, sys.gettrace())
    )

    with snoop:
        result2 = foo(2)
    assert result2 == 3
    assert sys.gettrace() is original_trace, (
        'sys.gettrace() was not restored after second with-block: '
        'expected %r, got %r' % (original_trace, sys.gettrace())
    )

    output = string_io.getvalue()
    assert 'result1 = foo(1)' in output
    assert 'result2 = foo(2)' in output

