import os
import subprocess
import sys
import textwrap


def test_utf8_source_line_preserved_under_c_locale(tmp_path):
    module_name = "pysnooper_utf8_locale_module"
    module_path = tmp_path / (module_name + ".py")
    log_path = tmp_path / "trace.log"

    source = textwrap.dedent(
        u'''\
        import pysnooper

        @pysnooper.snoop({log!r})
        def f():
            s = 'h\u00e9llo'
            return s
        '''
    ).format(log=os.fspath(log_path))

    with open(os.fspath(module_path), "w", encoding="utf-8") as fh:
        fh.write(source)

    driver = textwrap.dedent(
        u'''\
        import sys
        sys.path.insert(0, {dir!r})
        import {mod} as m
        result = m.f()
        assert result == 'h\u00e9llo', repr(result)
        '''
    ).format(dir=os.fspath(tmp_path), mod=module_name)

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["PYTHONUTF8"] = "0"
    env["PYTHONCOERCECLOCALE"] = "0"

    proc = subprocess.run(
        [sys.executable, "-c", driver],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout = proc.stdout.decode("utf-8", "replace")
    stderr = proc.stderr.decode("utf-8", "replace")
    assert proc.returncode == 0, (stdout, stderr)

    with open(os.fspath(log_path), "r", encoding="utf-8") as fh:
        log_text = fh.read()

    matching = [line for line in log_text.splitlines() if "s = " in line]
    assert matching, log_text
    line = matching[0]
    assert "s = 'h\u00e9llo'" in line, repr(line)
    assert "\ufffd" not in line, repr(line)
