import io
import sys

import pysnooper


def test_generator_close_restores_trace():
    string_io = io.StringIO()
    original_tracer = sys.gettrace()

    @pysnooper.snoop(string_io)
    def gen():
        yield 1
        yield 2

    g = gen()
    assert next(g) == 1
    g.close()

    assert sys.gettrace() is original_tracer, (
        'sys.gettrace() was not restored after generator.close(); '
        'tracer remained active: %r' % (sys.gettrace(),)
    )

    before = string_io.getvalue()

    def unrelated():
        x = 123
        return x

    assert unrelated() == 123
    after = string_io.getvalue()
    assert after == before, (
        'Tracer emitted output for unrelated code after generator.close(): '
        '%r' % (after[len(before):],)
    )

