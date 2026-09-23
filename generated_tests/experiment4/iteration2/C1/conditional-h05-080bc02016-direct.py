import io
import os
import subprocess
import sys
import textwrap

import pytest


MODULE_SOURCE = textwrap.dedent(
    '''\
    def greet():
        value = "h\u00e9llo"
        return value
    '''
)


RUNNER_SOURCE = textwrap.dedent(
    '''\
    import io
    import sys

    import pysnooper

    import target_module

    stream = io.StringIO()
    decorated = pysnooper.snoop(stream)(target_module.greet)
    decorated()
    sys.stdout.write(stream.getvalue())
    '''
)


def _write(path, text):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def test_utf8_source_line_is_not_mojibake_under_c_locale(tmp_path):
    module_path = tmp_path / "target_module.py"
    runner_path = tmp_path / "runner.py"

    _write(str(module_path), MODULE_SOURCE)
    _write(str(runner_path), RUNNER_SOURCE)

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(tmp_path) + os.pathsep + env.get("PYTHONPATH", "")

    completed = subprocess.run(
        [sys.executable, str(runner_path)],
        cwd=str(tmp_path),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout = completed.stdout.decode("utf-8", errors="replace")
    stderr = completed.stderr.decode("utf-8", errors="replace")

    assert completed.returncode == 0, (
        "runner failed under LC_ALL=C\nstdout:\n%s\nstderr:\n%s" % (stdout, stderr)
    )

    assert "h\u00e9llo" in stdout, (
        "expected the exact non-ASCII source text 'h\u00e9llo' in the trace output "
        "under LC_ALL=C, but got:\n%s" % stdout
    )

    assert "\ufffd" not in stdout, (
        "trace output contains replacement characters, indicating the UTF-8 source "
        "line was mis-decoded under LC_ALL=C:\n%s" % stdout
    )
