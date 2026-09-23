import os
import subprocess
import sys
import textwrap

import pytest


CHILD_SCRIPT = textwrap.dedent(
    '''
    import sys

    import pysnooper

    @pysnooper.snoop()
    def decorated(value):
        return len(value)

    result = None
    exception = None
    try:
        result = decorated('caf\u00e9')
    except BaseException as exc:
        exception = exc

    sys.stdout.write('RESULT:%r\n' % (result,))
    sys.stdout.write('EXCEPTION:%s\n' % (type(exception).__name__ if exception is not None else 'None'))
    '''
)


def _run_child(env_overrides):
    env = dict(os.environ)
    env.update(env_overrides)
    proc = subprocess.run(
        [sys.executable, '-c', CHILD_SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    return proc


def _parse_child_stdout(raw_bytes):
    text = raw_bytes.decode('utf-8', 'replace')
    result = None
    exception_name = None
    for line in text.splitlines():
        if line.startswith('RESULT:'):
            result = line[len('RESULT:'):]
        elif line.startswith('EXCEPTION:'):
            exception_name = line[len('EXCEPTION:'):]
    return result, exception_name


def test_non_ascii_argument_with_ascii_stderr():
    proc = _run_child({
        'LC_ALL': 'C',
        'LANG': 'C',
        'PYTHONUTF8': '0',
        'PYTHONCOERCECLOCALE': '0',
    })

    result, exception_name = _parse_child_stdout(proc.stdout)

    observation = (result, exception_name)
    assert observation == ('4', 'None'), (
        'decorated function with non-ASCII argument did not return normally; '
        'stdout=%r stderr=%r' % (proc.stdout, proc.stderr)
    )
