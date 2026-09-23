import json
import os
import subprocess
import sys
import textwrap

import pytest


SCRIPT = textwrap.dedent(
    '''
    import json
    import os
    import sys

    import pysnooper

    out_path = sys.argv[1]

    @pysnooper.snoop(out_path)
    def my_function():
        value = 'caf\u00e9'
        return 42

    result = my_function()

    exists = os.path.exists(out_path)
    if exists:
        with open(out_path, 'rb') as f:
            raw = f.read()
        content = raw.decode('utf-8', 'replace')
    else:
        content = ''

    sys.stdout.write(json.dumps({'result': result, 'exists': exists, 'content': content}))
    '''
)


def _run_script(tmp_path):
    script_path = tmp_path / 'snoop_script.py'
    script_path.write_text(SCRIPT, encoding='utf-8')
    out_path = tmp_path / 'trace.log'

    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['LANG'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'
    env['PYTHONIOENCODING'] = 'utf-8'

    proc = subprocess.run(
        [sys.executable, str(script_path), str(out_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=str(tmp_path),
        timeout=30.0,
    )
    return proc, out_path


def test_file_output_non_ascii_locale(tmp_path):
    proc, out_path = _run_script(tmp_path)

    stdout = proc.stdout.decode('utf-8', 'replace')
    stderr = proc.stderr.decode('utf-8', 'replace')

    assert proc.returncode == 0, (
        'subprocess failed with returncode {!r}\nstdout:\n{}\nstderr:\n{}'.format(
            proc.returncode, stdout, stderr
        )
    )

    payload = json.loads(stdout)

    assert payload['result'] == 42
    assert payload['exists'] is True
    assert 'caf\u00e9' in payload['content']
