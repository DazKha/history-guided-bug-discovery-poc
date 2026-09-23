import os
import subprocess
import sys
import textwrap


def test_utf8_source_line_under_c_locale(tmp_path):
    module_name = "pysnooper_utf8_target"
    module_path = tmp_path / (module_name + ".py")

    source = textwrap.dedent(
        u'''
        import pysnooper

        @pysnooper.snoop()
        def f():
            s = 'h\u00e9llo'
            return s
        '''
    )
    module_path.write_text(source, encoding="utf-8")

    driver = textwrap.dedent(
        u'''
        import sys
        sys.path.insert(0, {path!r})
        import {module_name} as m
        result = m.f()
        assert result == 'h\u00e9llo', repr(result)
        '''
    ).format(path=str(tmp_path), module_name=module_name)

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["PYTHONUTF8"] = "0"
    env["PYTHONCOERCECLOCALE"] = "0"
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.run(
        [sys.executable, "-c", driver],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=30.0,
    )

    stderr_text = proc.stderr.decode("utf-8", "replace")
    stdout_text = proc.stdout.decode("utf-8", "replace")

    assert proc.returncode == 0, (
        "driver failed\nSTDOUT:\n" + stdout_text + "\nSTDERR:\n" + stderr_text
    )

    matching_lines = [
        line for line in stderr_text.splitlines() if "s = " in line
    ]
    assert matching_lines, (
        "no trace line containing 's = ' found\nSTDERR:\n" + stderr_text
    )

    trace_line = matching_lines[0]
    assert "s = 'h\u00e9llo'" in trace_line, (
        "trace line did not contain the exact UTF-8 source text; "
        "got: " + repr(trace_line)
    )
    assert "\ufffd" not in trace_line, (
        "trace line contained U+FFFD replacement characters: "
        + repr(trace_line)
    )
