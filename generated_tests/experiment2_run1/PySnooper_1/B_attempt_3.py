import io
import pysnooper


def test_reuse_tracer_across_with_blocks():
    string_io = io.StringIO()
    snoop = pysnooper.snoop(string_io)

    def foo(x):
        with snoop:
            y = x + 1
        return y

    def bar(x):
        with snoop:
            z = x * 2
        return z

    assert foo(1) == 2
    assert bar(3) == 6
    output = string_io.getvalue()
    assert 'y = x + 1' in output
    assert 'z = x * 2' in output

