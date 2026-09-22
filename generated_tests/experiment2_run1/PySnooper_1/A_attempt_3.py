import io
import sys
import gc

import pysnooper


def test_generator_early_close_restores_trace():
    string_io = io.StringIO()
    original_tracer = sys.gettrace()

    @pysnooper.snoop(string_io)
    def f():
        yield 1
        yield 2
        yield 3

    gen = f()
    assert next(gen) == 1
    gen.close()
    gc.collect()

    assert sys.gettrace() is original_tracer

