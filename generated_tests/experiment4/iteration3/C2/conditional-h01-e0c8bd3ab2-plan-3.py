import os
import sys
import subprocess
import textwrap


def test_file_output_preserves_non_ascii_under_ascii_locale(tmp_path):
    target = tmp_path / "trace.log"
    target.write_text("lala", encoding="ascii")

    script = textwrap.dedent(
        """
        import sys
        import pysnooper

        path = sys.argv[1]

        @pysnooper.snoop(path, overwrite=True)
        def my_function():
            value = '\u65e5\u672c\u8a9e'
            return value

        result = my_function()
        assert result == '\u65e5\u672c\u8a9e'
        """
    )

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["PYTHONUTF8"] = "0"
    env["PYTHONCOERCECLOCALE"] = "0"

    completed = subprocess.run(
        [sys.executable, "-c", script, str(target)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    stdout = completed.stdout.decode("utf-8", "replace")
    stderr = completed.stderr.decode("utf-8", "replace")

    assert completed.returncode == 0, (
        "decorated call failed under non-UTF-8 locale; "
        "stdout=%r stderr=%r" % (stdout, stderr)
    )

    content = target.read_text(encoding="utf-8")
    assert "lala" not in content
    assert "\u65e5\u672c\u8a9e" in content
