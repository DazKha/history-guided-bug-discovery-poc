import os
import subprocess
import sys
import textwrap


def test_file_output_non_ascii_under_ascii_locale(tmp_path):
    """Trace output to a file must be written even when the trace contains
    non-ASCII characters and the process runs under an ASCII default encoding.

    Frozen hypothesis: FileWriter.write opens the output path without an
    explicit encoding, so under LC_ALL=C / PYTHONUTF8=0 the default text
    encoding is ASCII and writing a non-ASCII variable repr raises
    UnicodeEncodeError, leaving the requested path without the trace.
    """
    out_path = tmp_path / "trace.log"
    script = textwrap.dedent(
        """
        import pysnooper

        @pysnooper.snoop({path!r})
        def f():
            value = 'caf\u00e9'
            return value

        result = f()
        assert result == 'caf\u00e9', result
        """
    ).format(path=str(out_path))

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["PYTHONUTF8"] = "0"
    env["PYTHONIOENCODING"] = "ascii"

    proc = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, (
        "decorated function run failed under ASCII locale; "
        "stderr:\n" + proc.stderr
    )
    assert out_path.exists(), "requested trace output path was not created"
    content = out_path.read_text(encoding="utf-8", errors="replace")
    assert "caf\u00e9" in content, (
        "trace output at the requested path does not contain the non-ASCII "
        "variable value; content was: " + repr(content)
    )

