import os
import subprocess
import sys
import textwrap


def test_file_output_non_ascii_under_ascii_locale(tmp_path):
    """Trace output to a path must be written even when the trace contains
    non-ASCII characters and the process default text encoding is ASCII.

    The decorated function must also return its correct value.
    """
    out_path = tmp_path / "trace.log"
    script = tmp_path / "run_snoop.py"
    script.write_text(
        textwrap.dedent(
            """
            import pysnooper

            @pysnooper.snoop({path!r})
            def f():
                value = 'caf\u00e9'
                return 42

            result = f()
            assert result == 42, result
            """
        ).format(path=str(out_path)),
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["PYTHONUTF8"] = "0"
    env["PYTHONIOENCODING"] = "ascii"

    proc = subprocess.run(
        [sys.executable, str(script)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stderr = proc.stderr.decode("utf-8", "replace")
    assert proc.returncode == 0, (
        "decorated function run failed under ASCII default encoding; "
        "stderr:\n" + stderr
    )
    assert out_path.exists(), "trace output file was not created at the requested path"
    content = out_path.read_text(encoding="utf-8")
    assert "caf\u00e9" in content, (
        "trace output did not contain the non-ASCII variable value; "
        "content:\n" + content
    )
