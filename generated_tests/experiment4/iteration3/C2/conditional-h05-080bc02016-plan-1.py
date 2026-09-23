import io
import os
import subprocess
import sys
import textwrap


MODULE_SOURCE = (
    'import pysnooper\n'
    '@pysnooper.snoop(string_io)\n'
    'def f():\n'
    '    s = "h\u00e9llo"\n'
    '    return s\n'
)


DRIVER_SOURCE = (
    'import io\n'
    'import sys\n'
    'import pysnooper\n'
    'string_io = io.StringIO()\n'
    'import locale_mod\n'
    'result = locale_mod.f()\n'
    'sys.stdout.write("RESULT:" + repr(result) + "\\n")\n'
    'sys.stdout.write("TRACE_START\\n")\n'
    'sys.stdout.write(string_io.getvalue())\n'
    'sys.stdout.write("TRACE_END\\n")\n'
)


def test_non_ascii_source_line_under_c_locale(tmp_path):
    module_path = tmp_path / 'locale_mod.py'
    module_path.write_bytes(MODULE_SOURCE.encode('utf-8'))

    driver_path = tmp_path / 'driver.py'
    driver_path.write_text(DRIVER_SOURCE, encoding='utf-8')

    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['LANG'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'
    env['PYTHONPATH'] = str(tmp_path) + os.pathsep + env.get('PYTHONPATH', '')

    completed = subprocess.run(
        [sys.executable, str(driver_path)],
        cwd=str(tmp_path),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )

    stdout = completed.stdout.decode('utf-8', 'replace')
    stderr = completed.stderr.decode('utf-8', 'replace')

    assert completed.returncode == 0, (
        'driver failed: rc=%r\nstdout=%r\nstderr=%r'
        % (completed.returncode, stdout, stderr)
    )

    assert 'TRACE_START' in stdout and 'TRACE_END' in stdout, (
        'trace markers missing: stdout=%r stderr=%r' % (stdout, stderr)
    )

    trace = stdout.split('TRACE_START', 1)[1].split('TRACE_END', 1)[0]

    assert 'h\u00e9llo' in trace, (
        'expected exact non-ASCII source text in trace output; got: %r'
        % (trace,)
    )

    assert 'h\ufffdllo' not in trace, (
        'trace output contains replacement characters instead of the '
        'original non-ASCII text: %r' % (trace,)
    )
