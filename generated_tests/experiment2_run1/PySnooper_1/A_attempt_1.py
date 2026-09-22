import io
import pysnooper

def test_generator_with_block_in_helper():
    string_io = io.StringIO()

    def helper():
        with pysnooper.snoop(string_io):
            x = 1

    def gen():
        helper()
        yield 42

    g = gen()
    next(g)
    output = string_io.getvalue()
    # The generator frame should not be traced after the with block exits.
    # If it is, we will see lines from the generator (e.g., 'yield 42') in the output.
    assert 'yield 42' not in output, f"Unexpected tracing of generator after with block: {output!r}"

