import os
import sys
import subprocess
import textwrap


def test_file_output_preserves_non_ascii_under_ascii_locale(tmp_path):
    target = tmp_path / "trace.log"
    target.write_text("lala", encoding="ascii")

    script = textwrap.dedent(
        '''
        import sys
        import pysnooper

        path = sys.argv[1]

        @pysnooper.snoop(path)
        def my_function():
            value = "na\u00efve"
            return value

        result = my_function()
        assert result == "na\u00efve"
        '''
    )

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["PYTHONUTF8"] = "0"
    env["PYTHONCOERCECLOCALE"] = "0"

    proc = subprocess.run(
        [sys.executable, "-c", script, str(target)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    stdout = proc.stdout.decode("utf-8", "replace")
    stderr = proc.stderr.decode("utf-8", "replace")

    assert proc.returncode == 0, (
        "decorated call failed under ASCII locale; "
        "stdout=%r stderr=%r" % (stdout, stderr)
    )

    with open(str(target), encoding="utf-8") as output_file:
        output = output_file.read()

    assert output.startswith("lala")
    assert "na\u00efve" in output
