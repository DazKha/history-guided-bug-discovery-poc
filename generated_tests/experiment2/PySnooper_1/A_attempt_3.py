import io
import pysnooper


def test_generator_context_manager_traces_generator_body():
    string_io = io.StringIO()

    @pysnooper.snoop(string_io)
    def gen(x):
        y = x + 1
        yield y
        z = y + 1
        yield z

    g = gen(1)
    assert next(g) == 2
    assert next(g) == 3

    output = string_io.getvalue()
    assert 'call' in output
    assert 'line' in output
    assert 'return' in output
    assert 'y = x + 1' in output
    assert 'z = y + 1' in output

