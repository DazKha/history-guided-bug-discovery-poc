import sys
import pysnooper


def test_generator_close_restores_trace():
    original_tracer = sys.gettrace()

    @pysnooper.snoop()
    def f(x1):
        x2 = (yield x1)
        x3 = 'foo'
        x4 = (yield 2)
        return

    assert sys.gettrace() is original_tracer
    generator = f(0)
    assert sys.gettrace() is original_tracer
    first_item = next(generator)
    assert first_item == 0
    assert sys.gettrace() is original_tracer

    generator.close()

    assert sys.gettrace() is original_tracer

