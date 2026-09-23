import io
import os
import subprocess
import sys
import textwrap

import pytest


@pytest.fixture
def locale_env():
    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['LANG'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'
    return env


def test_utf8_source_line_under_c_locale(tmp_path, locale_env):
    module_name = 'locale_mod_file'
    module_path = tmp_path / (module_name + '.py')
    log_path = tmp_path / 'snoop.log'

    content = (
        'import pysnooper\n'
        '@pysnooper.snoop({log!r})\n'
        'def f():\n'
        '    s = "h\u00e9llo"\n'
        '    return s\n'
    ).format(log=str(log_path))

    module_path.write_bytes(content.encode('utf-8'))

    driver = textwrap.dedent(
        '''
        import sys
        sys.path.insert(0, {tmp!r})
        import {mod}
        result = {mod}.f()
        assert result == "h\u00e9llo", repr(result)
        '''
    ).format(tmp=str(tmp_path), mod=module_name)

    proc = subprocess.run(
        [sys.executable, '-c', driver],
        env=locale_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout = proc.stdout.decode('utf-8', 'replace')
    stderr = proc.stderr.decode('utf-8', 'replace')
    assert proc.returncode == 0, (stdout, stderr)

    assert log_path.exists(), (stdout, stderr)
    output = log_path.read_bytes().decode('utf-8', 'replace')

    assert 'h\u00e9llo' in output, output
    assert 'h\ufffdllo' not in output, output
