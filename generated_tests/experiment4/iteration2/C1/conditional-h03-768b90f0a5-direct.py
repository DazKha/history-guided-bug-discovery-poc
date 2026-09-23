import os
import sys
import subprocess
import textwrap
import tempfile


def test_utf8_source_line_preserved_under_c_locale():
    """PySnooper must show the exact UTF-8 source line even under LC_ALL=C.

    A UTF-8 source file with no PEP-263 coding declaration and a non-ASCII
    literal ('héllo') is traced in a subprocess whose locale is forced to C
    (ASCII default encoding).  The emitted trace line must contain the exact
    Unicode text 'héllo', not a mojibake replacement such as 'h\ufffdllo'.
    """
    module_source = textwrap.dedent(
        '''\
        import pysnooper


        @pysnooper.snoop()
        def greet():
            message = "h\u00e9llo"
            return message


        greet()
        '''
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        module_path = os.path.join(tmpdir, "utf8_source_module.py")
        with open(module_path, "w", encoding="utf-8") as fh:
            fh.write(module_source)

        env = dict(os.environ)
        env["LC_ALL"] = "C"
        env["LANG"] = "C"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONPATH"] = tmpdir + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [sys.executable, module_path],
            capture_output=True,
            env=env,
            cwd=tmpdir,
        )

    stdout = result.stdout.decode("utf-8", "replace")
    stderr = result.stderr.decode("utf-8", "replace")
    combined = stdout + stderr

    assert result.returncode == 0, (
        "Traced module failed under LC_ALL=C.\n"
        "stdout:\n%s\nstderr:\n%s" % (stdout, stderr)
    )

    assert "h\u00e9llo" in combined, (
        "Expected the exact UTF-8 source text 'h\u00e9llo' in the trace output "
        "under LC_ALL=C, but it was missing (mojibake / replacement chars?).\n"
        "stdout:\n%s\nstderr:\n%s" % (stdout, stderr)
    )

    assert "h\ufffdllo" not in combined, (
        "Trace output contains the replacement character U+FFFD instead of the "
        "real source text 'h\u00e9llo', indicating locale-dependent decoding.\n"
        "stdout:\n%s\nstderr:\n%s" % (stdout, stderr)
    )
