import os
import subprocess
import sys
import textwrap


SCRIPT = textwrap.dedent(
    '''
    import sys

    import pysnooper

    @pysnooper.snoop()
    def echo(value):
        return value

    result = None
    error = None
    try:
        result = echo('caf\\u00e9')
    except BaseException as exc:
        error = type(exc).__name__

    sys.stdout.write('RESULT=%r\\n' % (result,))
    sys.stdout.write('ERROR=%r\\n' % (error,))
    sys.stdout.write('STDERR_ENCODING=%r\\n' % (getattr(sys.stderr, 'encoding', None),))
    '''
)


def test_non_ascii_argument_with_default_stderr_output(tmp_path):
    script_path = tmp_path / 'snoop_non_ascii.py'
    script_path.write_text(SCRIPT)
    stderr_path = tmp_path / 'stderr.log'

    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'

    with open(str(stderr_path), 'wb') as stderr_file:
        completed = subprocess.run(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=stderr_file,
            env=env,
            cwd=str(tmp_path),
            timeout=30.0,
        )

    stdout_text = completed.stdout.decode('utf-8', 'replace')
    observed = {}
    for line in stdout_text.splitlines():
        if '=' in line:
            key, _, value = line.partition('=')
            observed[key] = value

    assert observed.get('RESULT') == repr('caf\u00e9'), observed
    assert observed.get('ERROR') == 'None', observed
