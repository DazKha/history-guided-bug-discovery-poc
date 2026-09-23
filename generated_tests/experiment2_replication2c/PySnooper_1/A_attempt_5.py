import io
import pytest
import pysnooper


def test_generator_close_runs_finally():
    string_io = io.StringIO()
    cleanup_ran = []

    @pysnooper.snoop(string_io)
    def gen_func():
        try:
            yield 1
            yield 2
        finally:
            cleanup_ran.append(True)

    g = gen_func()
    first = next(g)
    assert first == 1
    g.close()
    assert cleanup_ran == [True], (
        "Generator finally block did not run after close(); "
        "cleanup_ran=%r" % (cleanup_ran,)
    )

