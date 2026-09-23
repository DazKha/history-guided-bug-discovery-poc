import gc
import sys

import pysnooper


def test_generator_gc_restores_trace():
    original_tracer = sys.gettrace()

    @pysnooper.snoop()
    def f():
        yield 1
        yield 2

    gen = f()
    assert next(gen) == 1
    del gen
    gc.collect()

    assert sys.gettrace() is original_tracer

