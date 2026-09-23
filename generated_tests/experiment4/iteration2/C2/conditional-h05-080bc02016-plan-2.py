import io
import os
import sys
import textwrap
import subprocess

import pytest


MODULE_SOURCE = textwrap.dedent(
    u'''\
    import pysnooper

    @pysnooper.snoop()
    def f():
        x = 'h\u00e9llo'
        return x
    '''
)


CHILD_SCRIPT = textwrap.dedent(
    u'''\
    import io
    import os
    import sys

    sys.path.insert(0, {tmpdir!r})

    import pysnooper

    import utf8mod2

    captured = io.StringIO()
    original_stderr = sys.stderr
    sys.stderr = captured
    try:
        result = utf8mod2.f()
    finally:
        sys.stderr = original_stderr

    sys.stdout.buffer.write(captured.getvalue().encode('utf-8'))
    sys.stdout.buffer.write(b'\\n---RESULT---\\n')
    sys.stdout.buffer.write(repr(result).encode('utf-8'))
    '''
)


def test_utf8_source_line_under_c_locale(tmp_path):
    module_path = tmp_path / 'utf8mod2.py'
    module_path.write_bytes(MODULE_SOURCE.encode('utf-8'))

    script_path = tmp_path / 'child_runner.py'
    script_path.write_text(
        CHILD_SCRIPT.format(tmpdir=str(tmp_path)), encoding='utf-8'
    )

    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['LANG'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'
    env['PYTHONIOENCODING'] = 'utf-8'

    completed = subprocess.run(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=30.0,
    )

    stdout_bytes = completed.stdout
    assert completed.returncode == 0, (
        'child process failed: returncode={!r} stderr={!r}'.format(
            completed.returncode, completed.stderr
        )
    )

    marker = b'\n---RESULT---\n'
    assert marker in stdout_bytes, (
        'child did not emit result marker; stdout={!r}'.format(stdout_bytes)
    )
    trace_bytes, _, result_bytes = stdout_bytes.partition(marker)
    trace_text = trace_bytes.decode('utf-8')
    result_text = result_bytes.decode('utf-8')

    assert result_text == repr(u'h\u00e9llo'), (
        'unexpected function result: {!r}'.format(result_text)
    )

    observed_trace = trace_text
    expected_substring = u'h\u00e9llo'
    replacement_char = u'\ufffd'

    assert expected_substring in observed_trace, (
        'expected exact non-ASCII source text {!r} in trace output, '
        'got: {!r}'.format(expected_substring, observed_trace)
    )
    assert replacement_char not in observed_trace, (
        'trace output contains replacement character {!r}: {!r}'.format(
            replacement_char, observed_trace
        )
    )
