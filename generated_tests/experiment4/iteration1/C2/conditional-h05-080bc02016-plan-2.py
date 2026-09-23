import io
import os
import subprocess
import sys
import textwrap

import pytest


MODULE_SOURCE = (
    "import pysnooper\n"
    "@pysnooper.snoop(string_io)\n"
    "def g():\n"
    "    msg = 'h\u00e9llo'\n"
    "    return msg\n"
)


DRIVER = textwrap.dedent(
    '''
    import io
    import sys

    import pysnooper

    string_io = io.StringIO()
    import utf8_assign

    result = utf8_assign.g()
    assert result == 'h\u00e9llo', repr(result)
    sys.stdout.write(string_io.getvalue())
    '''
)


def test_utf8_source_line_under_c_locale(tmp_path):
    module_path = tmp_path / 'utf8_assign.py'
    module_path.write_bytes(MODULE_SOURCE.encode('utf-8'))

    driver_path = tmp_path / 'driver.py'
    driver_path.write_text(DRIVER, encoding='utf-8')

    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['LANG'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'
    env['PYTHONPATH'] = os.pathsep.join(
        [str(tmp_path)] + ([env['PYTHONPATH']] if env.get('PYTHONPATH') else [])
    )

    proc = subprocess.run(
        [sys.executable, str(driver_path)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30.0,
    )

    stdout = proc.stdout.decode('utf-8', 'replace')
    stderr = proc.stderr.decode('utf-8', 'replace')

    assert proc.returncode == 0, (
        'driver failed\nstdout:\n%s\nstderr:\n%s' % (stdout, stderr)
    )

    msg_lines = [line for line in stdout.splitlines() if 'msg =' in line]
    assert msg_lines, (
        'no trace line containing "msg =" found\nstdout:\n%s\nstderr:\n%s'
        % (stdout, stderr)
    )

    assert any('h\u00e9llo' in line for line in msg_lines), (
        'traced source line did not contain the exact non-ASCII literal '
        '"h\u00e9llo"\nselected lines:\n%s\nfull stdout:\n%s'
        % ('\n'.join(msg_lines), stdout)
    )
