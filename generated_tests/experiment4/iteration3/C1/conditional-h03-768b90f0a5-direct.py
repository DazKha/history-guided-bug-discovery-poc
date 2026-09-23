import os
import sys
import subprocess
import textwrap
import tempfile


def test_utf8_source_line_not_mojibake_under_c_locale():
    """Under LC_ALL=C, a UTF-8 source file with no coding declaration must
    still produce a trace line containing the exact Unicode text 'héllo'."""

    module_source = textwrap.dedent(
        '''\
        import pysnooper


        @pysnooper.snoop()
        def greet():
            message = "héllo"
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

        proc = subprocess.run(
            [sys.executable, module_path],
            cwd=tmpdir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=60,
        )

    output = proc.stdout.decode("utf-8", "replace")

    assert proc.returncode == 0, (
        "Tracing run failed under LC_ALL=C.\nOutput:\n" + output
    )

    assert "héllo" in output, (
        "Expected the traced source line to contain the exact Unicode text "
        "'héllo' as written in the UTF-8 source file, but it did not.\n"
        "Output:\n" + output
    )

    assert "h\ufffdllo" not in output, (
        "The traced source line was mis-decoded (mojibake): the non-ASCII "
        "bytes were replaced with U+FFFD instead of being decoded as UTF-8.\n"
        "Output:\n" + output
    )
