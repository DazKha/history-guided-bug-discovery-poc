import io
import os
import subprocess
import sys
import textwrap

import pytest


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="LC_ALL=C locale semantics are POSIX-specific",
)
def test_utf8_source_line_preserved_under_c_locale(tmp_path):
    """A UTF-8 source file with non-ASCII text and no coding declaration
    must be echoed verbatim into the trace even when the process locale is C.
    """
    module_path = tmp_path / "utf8_target_module.py"
    module_path.write_text(
        textwrap.dedent(
            '''\
            import pysnooper

            @pysnooper.snoop()
            def greet():
                message = "h\u00e9llo"
                return message
            '''
        ),
        encoding="utf-8",
    )

    driver_path = tmp_path / "driver.py"
    driver_path.write_text(
        textwrap.dedent(
            '''\
            import io
            import sys

            import pysnooper

            import utf8_target_module

            stream = io.StringIO()
            utf8_target_module.greet = pysnooper.snoop(stream)(
                utf8_target_module.greet.__wrapped__
            )
            utf8_target_module.greet()
            sys.stdout.write(stream.getvalue())
            '''
        ),
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["PYTHONPATH"] = str(tmp_path) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        [sys.executable, str(driver_path)],
        cwd=str(tmp_path),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout = result.stdout.decode("utf-8", errors="replace")
    stderr = result.stderr.decode("utf-8", errors="replace")

    assert result.returncode == 0, (
        "driver failed under LC_ALL=C:\n"
        "stdout:\n%s\nstderr:\n%s" % (stdout, stderr)
    )

    assert "h\u00e9llo" in stdout, (
        "Expected the exact non-ASCII source text 'h\u00e9llo' to appear "
        "verbatim in the trace output under LC_ALL=C, but it did not.\n"
        "Trace output was:\n%s" % stdout
    )

    assert "h\ufffd" not in stdout and "h\u00c3\u00a9llo" not in stdout, (
        "Trace output contains mojibake/replacement characters for the "
        "non-ASCII source line under LC_ALL=C:\n%s" % stdout
    )
