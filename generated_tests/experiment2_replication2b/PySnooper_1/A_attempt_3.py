import io
import pysnooper


def test_generator_with_block_does_not_trace_after_exit():
    string_io = io.StringIO()

    def gen():
        with pysnooper.snoop(string_io):
            x = 1
        y = 2
        yield x + y

    g = gen()
    result = next(g)
    assert result == 3

    output = string_io.getvalue()
    # The line `y = 2` is after the with block and should not be traced.
    assert 'y = 2' not in output

