import os
import subprocess
import sys
import textwrap


def test_utf8_source_line_preserved_under_c_locale(tmp_path):
    module_path = tmp_path / 'pysnooper_utf8_a.py'
    module_source = textwrap.dedent(
        u'''\
        import pysnooper

        @pysnooper.snoop()
        def f():
            s = 'h\u00e9llo'
            return s
        '''
    )
    module_path.write_text(module_source, encoding='utf-8')

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    env = dict(os.environ)
    env['LC_ALL'] = 'C'
    env['LANG'] = 'C'
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONPATH'] = repo_root + os.pathsep + str(tmp_path) + os.pathsep + env.get('PYTHONPATH', '')

    runner = (
        'import sys\n'
        'sys.path.insert(0, {tmp!r})\n'
        'import pysnooper.tracer as tracer\n'
        'tracer.source_cache.clear()\n'
        'import pysnooper_utf8_a\n'
        'pysnooper_utf8_a.f()\n'
    ).format(tmp=str(tmp_path))

    proc = subprocess.run(
        [sys.executable, '-c', runner],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30.0,
    )

    stderr_text = proc.stderr.decode('utf-8', 'replace')

    matching_lines = [
        line for line in stderr_text.splitlines()
        if 's = ' in line
    ]
    assert matching_lines, (
        'No trace line containing the assignment to s was found.\n'
        'stderr was:\n' + stderr_text
    )

    source_line = matching_lines[0]

    assert 'h\u00e9llo' in source_line, (
        'Expected the exact Unicode text h\u00e9llo in the traced source line, '
        'but got: {!r}\nFull stderr:\n{}'.format(source_line, stderr_text)
    )
    assert '\ufffd' not in source_line, (
        'Traced source line contains U+FFFD replacement character: {!r}\n'
        'Full stderr:\n{}'.format(source_line, stderr_text)
    )
