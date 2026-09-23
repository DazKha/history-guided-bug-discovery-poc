import io
import gc
import pysnooper


def test_generator_close_runs_finally():
    string_io = io.StringIO()
    cleaned_up = []

    @pysnooper.snoop(string_io)
    def gen():
        try:
            yield 1
            yield 2
        finally:
            cleaned_up.append(True)

    g = gen()
    assert next(g) == 1
    g.close()
    gc.collect()
    assert cleaned_up == [True]

