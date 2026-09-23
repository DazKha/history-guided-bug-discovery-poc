import os
import sys
import tempfile
import subprocess
import textwrap


def test_file_output_preserves_non_ascii_under_non_utf8_locale():
    """
    Tracing to a filesystem path must preserve non-ASCII variable representations
    independent of the process locale.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "trace.log")
        script = textwrap.dedent(
            f'''
            import pysnooper

            @pysnooper.snoop({out_path!r})
            def f():
                value = "caf\u00e9"
                return value

            f()
            '''
        )
        script_path = os.path.join(tmpdir, "script.py")
        with open(script_path, "w", encoding="utf-8") as fh:
            fh.write(script)

        env = os.environ.copy()
        env["LC_ALL"] = "C"
        env["LANG"] = "C"
        env["PYTHONUTF8"] = "0"
        env["PYTHONIOENCODING"] = "ascii"

        result = subprocess.run(
            [sys.executable, script_path],
            env=env,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            f"Tracing to a file failed under non-UTF-8 locale.\n"
            f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
        )

        with open(out_path, "r", encoding="utf-8") as fh:
            trace_text = fh.read()

        assert "caf\u00e9" in trace_text, (
            f"Non-ASCII value 'caf\u00e9' was not preserved in trace output.\n"
            f"Trace contents: {trace_text!r}"
        )
