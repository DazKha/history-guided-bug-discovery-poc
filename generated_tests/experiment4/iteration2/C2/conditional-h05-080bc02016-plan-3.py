import io
import os
import subprocess
import sys
import textwrap

import pytest


MODULE_SOURCE = textwrap.dedent(
    u'''\
    def greet():
        message = "h\u00e9llo"
        return message
    '''
)


CHILD_SCRIPT = textwrap.dedent(
    u'''\
    import io
    import os
    import sys

    sys.path.insert(0, sys.argv[1])

    import pysnooper

    import utf8mod3

    log_path = os.path.join(sys.argv[1], "trace.log")
    decorated = pysnooper.snoop(log_path)(utf8mod3.greet)
    decorated()

    with open(log_path, "rb") as log_file:
        sys.stdout.buffer.write(log_file.read())
    '''
)


def test_utf8_source_line_preserved_under_c_locale(tmp_path):
    module_path = tmp_path / "utf8mod3.py"
    module_path.write_bytes(MODULE_SOURCE.encode("utf-8"))

    script_path = tmp_path / "run_snoop.py"
    script_path.write_bytes(CHILD_SCRIPT.encode("utf-8"))

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["PYTHONUTF8"] = "0"
    env["PYTHONCOERCECLOCALE"] = "0"

    completed = subprocess.run(
        [sys.executable, str(script_path), str(tmp_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=30.0,
    )

    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")

    trace_text = completed.stdout.decode("utf-8")

    assert "h\u00e9llo" in trace_text
    assert "\ufffd" not in trace_text
