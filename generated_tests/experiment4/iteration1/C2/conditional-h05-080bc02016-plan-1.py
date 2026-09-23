import io
import os
import subprocess
import sys
import textwrap

import pytest


MODULE_SOURCE = (
    "import pysnooper\n"
    "@pysnooper.snoop(string_io)\n"
    "def f():\n"
    "    return 'h\u00e9llo'\n"
)


RUNNER = textwrap.dedent(
    '''
    import io
    import sys

    import pysnooper

    string_io = io.StringIO()
    import utf8_no_coding

    result = utf8_no_coding.f()
    assert result == 'h\u00e9llo', repr(result)
    sys.stdout.write(string_io.getvalue())
    '''
)


def test_utf8_source_line_under_c_locale(tmp_path):
    module_path = tmp_path / 'utf8_no_coding.py'
    module_path.write_bytes(MODULE_SOURCE.encode('utf-8'))

    runner_path = tmp_path / 'runner.py'
    runner_path.write_text(RUNNER, encoding='utf-8')

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
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30.0,
    )

    stdout = completed.stdout.decode('utf-8', 'replace')
    stderr = completed.stderr.decode('utf-8', 'replace')

    assert completed.returncode == 0, (
        'runner failed with returncode {}\nstdout:\n{}\nstderr:\n{}'.format(
            completed.returncode, stdout, stderr
        )
    )

    return_lines = [line for line in stdout.splitlines() if 'return' in line]
    assert return_lines, (
        'no trace line containing "return" found in output:\n' + stdout
    )

    assert any('h\u00e9llo' in line for line in return_lines), (
        'expected the traced source line to contain the exact literal '
        "'h\u00e9llo' as written in the UTF-8 file, but got:\n" + '\n'.join(return_lines)
    )
