import io
import os
import subprocess
import sys
import textwrap

import pytest


MODULE_SOURCE = (
    "import pysnooper\n"
    "def h(string_io):\n"
    "    with pysnooper.snoop(string_io):\n"
    "        value = 'h\u00e9llo'\n"
    "    return value\n"
)


RUNNER_SOURCE = textwrap.dedent(
    '''
    import io
    import sys

    import utf8_withblock

    string_io = io.StringIO()
    result = utf8_withblock.h(string_io)
    sys.stdout.write(string_io.getvalue())
    '''
)


def test_utf8_source_line_under_c_locale(tmp_path):
    module_path = tmp_path / 'utf8_withblock.py'
    module_path.write_bytes(MODULE_SOURCE.encode('utf-8'))

    runner_path = tmp_path / 'runner.py'
    runner_path.write_text(RUNNER_SOURCE, encoding='utf-8')

    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['LANG'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'
    env['PYTHONPATH'] = os.pathsep.join(
        [str(tmp_path)] + ([env['PYTHONPATH']] if env.get('PYTHONPATH') else [])
    )

    completed = subprocess.run(
        [sys.executable, str(runner_path)],
        cwd=str(tmp_path),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30.0,
    )

    stdout = completed.stdout.decode('utf-8', 'replace')
    stderr = completed.stderr.decode('utf-8', 'replace')

    assert completed.returncode == 0, (
        'subprocess failed with return code %r\nstdout:\n%s\nstderr:\n%s'
        % (completed.returncode, stdout, stderr)
    )

    trace_lines = [line for line in stdout.splitlines() if 'value =' in line]
    assert trace_lines, (
        'no trace line containing "value =" was produced\nstdout:\n%s\nstderr:\n%s'
        % (stdout, stderr)
    )

    selected = trace_lines[0]
    assert 'h\u00e9llo' in selected, (
        'traced source line did not contain the exact non-ASCII literal; '
        'got: %r' % (selected,)
    )
