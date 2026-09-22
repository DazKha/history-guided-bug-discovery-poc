import io
import sys

import pysnooper


def test_generator_close_restores_trace():
    string_io = io.StringIO()
    original_tracer = sys.gettrace()

    @pysnooper.snoop(string_io)
    def f(x1):
        x2 = (yield x1)
        x3 = 'foo'
        x4 = (yield 2)
        return

    assert sys.gettrace() is original_tracer
    generator = f(0)
    assert sys.gettrace() is original_tracer
    first_item = next(generator)
    assert sys.gettrace() is original_tracer
    assert first_item == 0

    generator.close()

    assert sys.gettrace() is original_tracer

