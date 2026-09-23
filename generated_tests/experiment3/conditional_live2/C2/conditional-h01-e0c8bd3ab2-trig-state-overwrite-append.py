import os
import sys
import subprocess
import textwrap

import pytest


NON_ASCII = '\u00e9\u00e8\u00ea\u4e2d\u6587'


CHILD_SCRIPT = textwrap.dedent(
    '''
    import sys
    import pysnooper

    path = sys.argv[1]
    non_ascii = sys.argv[2]

    @pysnooper.snoop(path)
    def append_fn():
        value = non_ascii
        return value

    @pysnooper.snoop(path, overwrite=True)
    def overwrite_fn():
        value = non_ascii
        return value

    append_fn()
    overwrite_fn()
    '''
)


def test_non_ascii_file_output_under_c_locale(tmp_path):
    path = tmp_path / 'snoop.log'
    path.write_text('lala', encoding='ascii')

    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['LANG'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'
    env['PYTHONIOENCODING'] = 'ascii'

    script_path = tmp_path / 'child_script.py'
    script_path.write_text(CHILD_SCRIPT, encoding='utf-8')

    proc = subprocess.run(
        [sys.executable, str(script_path), str(path), NON_ASCII],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stderr_text = proc.stderr.decode('utf-8', 'replace')
    assert proc.returncode == 0, (
        'Child process failed under non-UTF-8 locale.\n'
        'returncode={!r}\nstderr:\n{}'.format(proc.returncode, stderr_text)
    )

    content = path.read_text(encoding='utf-8')
    assert NON_ASCII in content, (
        'Non-ASCII value {!r} was not preserved in the trace file.\n'
        'File content:\n{}'.format(NON_ASCII, content)
    )

