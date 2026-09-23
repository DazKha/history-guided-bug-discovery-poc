import os
import sys
import locale
import pathlib
import tempfile

import pytest


NON_ASCII_VALUE = '\u65e5\u672c\u8a9e\u30c6\u30b9\u30c8'


def _run_child(output_path):
    import pysnooper

    @pysnooper.snoop(pathlib.Path(output_path))
    def my_function():
        local_value = NON_ASCII_VALUE
        return local_value

    return my_function()


def test_path_output_preserves_non_ascii_under_ascii_locale(tmp_path):
    output_path = tmp_path / 'trace.log'

    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['LANG'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'

    import subprocess

    child_code = (
        'import sys\n'
        'sys.path.insert(0, {!r})\n'
        'import locale\n'
        'assert locale.getpreferredencoding(False).lower() in ("ascii", "us-ascii"), locale.getpreferredencoding(False)\n'
        'import pathlib\n'
        'import pysnooper\n'
        'NON_ASCII_VALUE = {!r}\n'
        '@pysnooper.snoop(pathlib.Path({!r}))\n'
        'def my_function():\n'
        '    local_value = NON_ASCII_VALUE\n'
        '    return local_value\n'
        'my_function()\n'
    ).format(
        os.path.dirname(os.path.dirname(os.path.abspath(pysnooper.__file__))),
        NON_ASCII_VALUE,
        str(output_path),
    )

    completed = subprocess.run(
        [sys.executable, '-c', child_code],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert completed.returncode == 0, (
        'child process failed with return code {}; stderr={!r}'.format(
            completed.returncode, completed.stderr
        )
    )

    raw_bytes = output_path.read_bytes()
    decoded = raw_bytes.decode('utf-8')

    observation = NON_ASCII_VALUE in decoded

    assert observation, (
        'expected non-ASCII value {!r} to appear in UTF-8 decoded trace file; '
        'decoded content was {!r}'.format(NON_ASCII_VALUE, decoded)
    )
