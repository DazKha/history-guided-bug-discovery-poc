import os
import subprocess
import sys
import tempfile
import textwrap


def test_file_output_non_ascii_under_ascii_locale():
    """Trace output to a path must be written even when the trace contains
    non-ASCII characters and the process runs under an ASCII default encoding.

    The frozen hypothesis claims FileWriter.write opens the output path without
    an explicit encoding, so under LC_ALL=C / PYTHONUTF8=0 the default text
    encoding is ASCII and writing a non-ASCII variable repr raises
    UnicodeEncodeError instead of producing the trace.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "trace.log")
        script_path = os.path.join(tmpdir, "run_snoop.py")

        script = textwrap.dedent(
            """
            import sys
            import pysnooper

            out_path = sys.argv[1]

            @pysnooper.snoop(out_path)
            def f():
                value = 'caf\\u00e9'
                return 42

            result = f()
            assert result == 42, result
            """
        )
        with open(script_path, "w", encoding="utf-8") as fh:
            fh.write(script)

        env = dict(os.environ)
        env["LC_ALL"] = "C"
        env["LANG"] = "C"
        env["PYTHONUTF8"] = "0"
        env["PYTHONIOENCODING"] = "ascii"

        proc = subprocess.run(
            [sys.executable, script_path, out_path],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stderr = proc.stderr.decode("utf-8", "replace")

        assert proc.returncode == 0, (
            "Decorated function run failed under ASCII locale; "
            "stderr was:\n" + stderr
        )
        assert os.path.exists(out_path), (
            "Trace output path was not created; stderr was:\n" + stderr
        )

        with open(out_path, "rb") as fh:
            raw = fh.read()
        text = raw.decode("utf-8", "replace")

        assert "caf\u00e9" in text, (
            "Trace at requested path does not contain the non-ASCII variable "
            "value; file contents were:\n" + text
        )
