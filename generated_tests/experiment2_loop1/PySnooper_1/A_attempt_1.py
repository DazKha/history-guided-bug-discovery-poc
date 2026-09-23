import gc
import io

import pysnooper


def test_abandoned_generator_does_not_corrupt_reused_tracer():
    string_io = io.StringIO()
    snoop = pysnooper.snoop(string_io)

    @snoop
    def gen():
        yield 1
        yield 2

    g = gen()
    assert next(g) == 1
    del g
    gc.collect()

    @snoop
    def plain(foo):
        x = 7
        return x + foo

    result = plain(3)
    assert result == 10

    output = string_io.getvalue()
    assert 'def plain(foo):' in output
    assert 'Return value:.. 10' in output
    assert 'foo' in output
    assert 'x = 7' in output

