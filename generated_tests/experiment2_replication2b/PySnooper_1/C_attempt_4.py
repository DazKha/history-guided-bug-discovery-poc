import io
import re

import pysnooper


def test_depth_restored_after_exception():
    string_io = io.StringIO()
    snoop = pysnooper.snoop(string_io)

    @snoop
    def raises():
        raise ValueError('boom')

    @snoop
    def normal():
        x = 1
        return x

    try:
        raises()
    except ValueError:
        pass

    result = normal()
    assert result == 1

    output = string_io.getvalue()
    assert 'Call ended by exception' in output

    normal_lines = [
        line for line in output.splitlines()
        if 'def normal():' in line or 'x = 1' in line or 'return x' in line
    ]
    assert normal_lines, output
    for line in normal_lines:
        assert not line.startswith(' '), (
            'Trace line for normal() is unexpectedly indented after an '
            'exception-ended traced call: {!r}\nFull output:\n{}'.format(
                line, output
            )
        )

