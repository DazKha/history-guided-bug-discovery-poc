import io
import os
import sys
import textwrap
import subprocess

import pytest

import pysnooper
from pysnooper import tracer


MODULE_SOURCE = textwrap.dedent(u'''\
    import pysnooper

    @pysnooper.snoop()
    def f():
        s = 'h\u00e9llo'
        return s
''')


CHILD_SCRIPT = textwrap.dedent(u'''\
    import io
    import sys
    import pysnooper
    from pysnooper import tracer

    module_name = sys.argv[1]
    module = __import__(module_name)

    string_io = io.StringIO()
    tracer_obj = pysnooper.snoop(string_io)
    wrapped = tracer_obj(module.f)
    wrapped()
    sys.stdout.write(string_io.getvalue())
''')


def _write_module(folder, module_name):
    path = os.path.join(folder, module_name + '.py')
    with open(path, 'wb') as fp:
        fp.write(MODULE_SOURCE.encode('utf-8'))
    return path


def _run_child(folder, module_name, locale_value):
    env = dict(os.environ)
    env['LC_ALL'] = locale_value
    env['LANG'] = locale_value
    env['PYTHONUTF8'] = '0'
    env['PYTHONCOERCECLOCALE'] = '0'
    env['PYTHONPATH'] = folder + os.pathsep + env.get('PYTHONPATH', '')
    proc = subprocess.run(
        [sys.executable, '-c', CHILD_SCRIPT, module_name],
        cwd=folder,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 0, proc.stderr.decode('utf-8', 'replace')
    return proc.stdout.decode('utf-8', 'replace')


def test_non_ascii_source_line_under_c_locale(tmp_path):
    folder = str(tmp_path)
    module_name = 'pysnooper_nonascii_module'
    _write_module(folder, module_name)

    output = _run_child(folder, module_name, 'C')

    assert u'h\u00e9llo' in output
    assert u'h\ufffdllo' not in output


def test_non_ascii_source_line_consistent_across_locales(tmp_path):
    folder = str(tmp_path)
    module_name = 'pysnooper_nonascii_module2'
    _write_module(folder, module_name)

    output_c = _run_child(folder, module_name, 'C')
    output_utf8 = _run_child(folder, module_name, 'C.UTF-8')

    assert u'h\u00e9llo' in output_c
    assert u'h\u00e9llo' in output_utf8
    assert u'h\ufffdllo' not in output_c
    assert u'h\ufffdllo' not in output_utf8


def test_source_cache_reuse_does_not_preserve_mojibake(tmp_path):
    folder = str(tmp_path)
    module_name = 'pysnooper_nonascii_module3'
    _write_module(folder, module_name)

    sys.path.insert(0, folder)
    try:
        module = __import__(module_name)
        tracer.source_cache.clear()

        string_io = io.StringIO()
        wrapped = pysnooper.snoop(string_io)(module.f)
        wrapped()
        first_output = string_io.getvalue()

        string_io2 = io.StringIO()
        wrapped2 = pysnooper.snoop(string_io2)(module.f)
        wrapped2()
        second_output = string_io2.getvalue()

        assert u'h\u00e9llo' in first_output
        assert u'h\u00e9llo' in second_output
        assert u'h\ufffdllo' not in first_output
        assert u'h\ufffdllo' not in second_output
    finally:
        sys.path.remove(folder)
        sys.modules.pop(module_name, None)
        tracer.source_cache.clear()

