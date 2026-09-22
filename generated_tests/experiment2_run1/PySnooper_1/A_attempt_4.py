import sys
import pysnooper


def test_generator_close_restores_trace():
    original_trace = sys.gettrace()

    @pysnooper.snoop()
    def gen():
        yield 1
        yield 2

    g = gen()
    assert next(g) == 1
    g.close()
    assert sys.gettrace() is original_trace

