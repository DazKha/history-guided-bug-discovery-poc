import sys
import pysnooper


def test_closed_generator_restores_original_trace_function():
    original_tracer = sys.gettrace()

    @pysnooper.snoop()
    def gen():
        yield 1
        yield 2

    generator = gen()
    assert next(generator) == 1
    generator.close()

    assert sys.gettrace() is original_tracer

