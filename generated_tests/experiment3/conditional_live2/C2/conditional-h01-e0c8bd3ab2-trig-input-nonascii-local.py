import os
import sys
import subprocess
import textwrap

import pytest


NON_ASCII_VALUE = 'h\u00e9llo-\u4e16\u754c'


def test_file_output_preserves_non_ascii_under_ascii_locale(tmp_path):
    """
    Frozen hypothesis: PySnooper's FileWriter.write opens the output path
    without an explicit encoding, so under a non-UTF-8 default text encoding
    (LC_ALL=C, PYTHONUTF8=0, PYTHONCOERCECLOCALE=0) writing a trace that
    contains a non-ASCII variable repr can fail or corrupt the trace.

    Trigger plan: create a temporary output path, decorate a function that
    assigns a non-ASCII string local with @pysnooper.snoop(path), run the
    function under a non-UTF-8 default text encoding, then read the file back
    as UTF-8 and assert the non-ASCII value appears.
    """
    output_path = tmp_path / 'snoop.log'

    script = textwrap.dedent(
        '''
        import sys
        import pysnooper

        path = sys.argv[1]

        @pysnooper.snoop(path)
        def my_function():
            value = {value!r}
            return value

        my_function()
        '''
    ).format(value=NON_ASCII_VALUE)

    script_path = tmp_path / 'run_snoop.py'
    script_path.write_text(script, encoding='utf-8')

    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['LANG'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'
    env['PYTHONIOENCODING'] = 'ascii'

    completed = subprocess.run(
        [sys.executable, str(script_path), str(output_path)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stderr_text = completed.stderr.decode('utf-8', 'replace')

    assert completed.returncode == 0, (
        'Tracing to a filesystem path failed under a non-UTF-8 default '
        'text encoding. stderr was:\n' + stderr_text
    )

    assert output_path.exists(), (
        'The requested output path was not created. stderr was:\n'
        + stderr_text
    )

    output = output_path.read_text(encoding='utf-8')

    assert NON_ASCII_VALUE in output, (
        'The non-ASCII variable value {!r} was not preserved in the trace '
        'file. File contents were:\n{}'.format(NON_ASCII_VALUE, output)
    )

