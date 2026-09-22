import io
import pysnooper


def test_reuse_tracer_multiple_with_blocks():
    string_io = io.StringIO()
    snoop = pysnooper.snoop(string_io)

    def foo():
        with snoop:
            x = 1
            y = 2
        with snoop:
            a = 3
            b = 4
        return x + y + a + b

    result = foo()
    assert result == 10
    output = string_io.getvalue()
    # Both with-blocks should produce trace output
    assert 'x = 1' in output, 'First with-block should be traced'
    assert 'y = 2' in output, 'First with-block should be traced'
    assert 'a = 3' in output, 'Second with-block should be traced'
    assert 'b = 4' in output, 'Second with-block should be traced'

