import io
import pysnooper


def test_closed_generator_does_not_corrupt_subsequent_indentation():
    gen_io = io.StringIO()

    @pysnooper.snoop(gen_io)
    def gen():
        yield 1
        yield 2

    g = gen()
    assert next(g) == 1
    g.close()

    out_io = io.StringIO()

    @pysnooper.snoop(out_io)
    def plain():
        x = 7
        return x

    assert plain() == 7
    lines = [line for line in out_io.getvalue().splitlines() if line.strip()]
    assert lines, 'expected snooped output for plain function'
    for line in lines:
        assert not line.startswith(' '), (
            'snooped output line unexpectedly indented after closing a '
            'generator: {!r}'.format(line)
        )

