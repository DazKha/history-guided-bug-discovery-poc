import os
import subprocess
import sys
import textwrap


def test_file_output_preserves_non_ascii_under_non_utf8_locale(tmp_path):
    """Tracing to a path must preserve non-ASCII text regardless of locale.

    Runs a child interpreter with a non-UTF-8 default text encoding
    (LC_ALL=C, PYTHONUTF8=0, PYTHONCOERCECLOCALE=0) and asserts that the
    non-ASCII local variable value appears in the trace file when read back
    as UTF-8.
    """
    out_path = tmp_path / "trace.log"
    script = textwrap.dedent(
        """
        import sys
        import pysnooper

        @pysnooper.snoop({path!r})
        def f():
            value = "caf\u00e9 \u2603"
            return value

        f()
        """
    ).format(path=str(out_path))

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["PYTHONUTF8"] = "0"
    env["PYTHONCOERCECLOCALE"] = "0"
    env.pop("PYTHONIOENCODING", None)

    proc = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, (
        "child process failed under non-UTF-8 locale; "
        "stderr=%r stdout=%r" % (proc.stderr, proc.stdout)
    )
    assert out_path.exists(), "trace file was not created at the requested path"

    data = out_path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AssertionError(
            "trace file is not valid UTF-8: %r" % (data,)
        ) from exc

    assert "caf\u00e9 \u2603" in text, (
        "non-ASCII variable value was not preserved in the trace file; "
        "file contents=%r" % (text,)
    )
