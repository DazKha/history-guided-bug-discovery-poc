import sys

import pysnooper


def test_snooped_generator_close_restores_trace():
    original_tracer = sys.gettrace()

    @pysnooper.snoop()
    def f():
        yield 1
        yield 2

    generator = f()
    assert sys.gettrace() is original_tracer

    first = next(generator)
    assert first == 1
    assert sys.gettrace() is original_tracer

    generator.close()

    assert sys.gettrace() is original_tracer

