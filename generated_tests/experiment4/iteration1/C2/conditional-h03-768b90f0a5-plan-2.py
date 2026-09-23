import os
import subprocess
import sys
import textwrap


def test_utf8_source_line_under_c_locale(tmp_path):
    module_path = tmp_path / 'pysnooper_utf8_b.py'
    log_path = tmp_path / 'pysnooper_utf8_b.log'

    source = textwrap.dedent(
        u'import pysnooper\n'
        u'@pysnooper.snoop(%r)\n'
        u'def f():\n'
        u"    s = 'h\u00e9llo'\n"
        u'    return s\n'
    ) % (str(log_path),)

    with open(str(module_path), 'w', encoding='utf-8') as f:
        f.write(source)

    if log_path.exists():
        log_path.unlink()

    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['LANG'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'
    env['PYTHONIOENCODING'] = 'utf-8'

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env['PYTHONPATH'] = os.pathsep.join(
        [str(tmp_path), repo_root] + ([env['PYTHONPATH']] if env.get('PYTHONPATH') else [])
    )

    code = (
        'import sys; '
        'sys.path.insert(0, %r); '
        'import pysnooper_utf8_b; '
        'pysnooper_utf8_b.f()'
    ) % (str(tmp_path),)

    proc = subprocess.run(
        [sys.executable, '-c', code],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30.0,
    )

    assert proc.returncode == 0, (
        'subprocess failed: rc=%r stdout=%r stderr=%r'
        % (proc.returncode, proc.stdout, proc.stderr)
    )

    assert log_path.exists(), 'log file was not created'

    with open(str(log_path), 'r', encoding='utf-8') as f:
        log_contents = f.read()

    matching_lines = [line for line in log_contents.splitlines() if 's = ' in line]
    assert matching_lines, (
        'no trace line containing "s = " found in log:\n%s' % (log_contents,)
    )

    source_line = matching_lines[0]

    assert u'h\u00e9llo' in source_line, (
        'expected exact Unicode text h\u00e9llo in trace line, got: %r\nfull log:\n%s'
        % (source_line, log_contents)
    )
    assert u'\ufffd' not in source_line, (
        'trace line contains U+FFFD replacement character: %r\nfull log:\n%s'
        % (source_line, log_contents)
    )
