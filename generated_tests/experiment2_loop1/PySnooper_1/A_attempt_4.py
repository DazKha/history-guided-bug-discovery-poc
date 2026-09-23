import gc
import sys

import pysnooper


def test_abandoned_generator_does_not_leak_tracer():
    original_tracer = sys.gettrace()

    @pysnooper.snoop()
    def f(x1):
        x2 = (yield x1)
        x3 = 'foo'
        x4 = (yield 2)
        return

    generator = f(0)
    first_item = next(generator)
    assert first_item == 0

    del generator
    gc.collect()

    assert sys.gettrace() is original_tracer

