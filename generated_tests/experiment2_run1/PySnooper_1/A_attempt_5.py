import io
import re
import pysnooper


def test_recursive_snoop_indentation():
    string_io = io.StringIO()

    @pysnooper.snoop(string_io)
    def factorial(n):
        if n <= 1:
            return 1
        return n * factorial(n - 1)

    result = factorial(3)
    assert result == 6
    output = string_io.getvalue()
    lines = output.splitlines()
    # Find the line entries for the outer frame's 'return n * factorial(n - 1)'
    # and the inner frame's lines. The outer frame's return line should have
    # zero indentation (top-level frame).
    return_lines = [l for l in lines if 'return n * factorial(n - 1)' in l]
    assert return_lines, 'expected return lines in output'
    # The first return line belongs to the outermost frame (n=3) and should
    # have no leading spaces.
    first_return = return_lines[0]
    assert not first_return.startswith(' '), (
        'outer frame return line should not be indented, got: %r' % first_return
    )

