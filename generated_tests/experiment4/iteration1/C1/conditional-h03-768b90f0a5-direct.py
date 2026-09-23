import os
import subprocess
import sys
import textwrap


def test_utf8_source_line_under_c_locale(tmp_path):
    """A UTF-8 source file with a non-ASCII literal must be traced verbatim.

    Under LC_ALL=C the platform default encoding is ASCII.  PySnooper's
    get_source_from_frame must still emit the exact source text 'h\u00e9llo'
    rather than a replacement-character mojibake version.
    """
    module_path = tmp_path / "pysnooper_utf8_target.py"
    module_path.write_text(
        textwrap.dedent(
            '''\
            import pysnooper


            @pysnooper.snoop()
            def greet():
                value = "h\u00e9llo"
                return value


            if __name__ == "__main__":
                greet()
            '''
        ),
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(tmp_path), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)

    result = subprocess.run(
        [sys.executable, str(module_path)],
        capture_output=True,
        env=env,
        cwd=str(tmp_path),
    )

    stdout = result.stdout.decode("utf-8", errors="replace")
    stderr = result.stderr.decode("utf-8", errors="replace")
    combined = stdout + stderr

    assert result.returncode == 0, combined
    assert "h\u00e9llo" in combined, (
        "Expected the traced source line to contain the exact Unicode text "
        "'h\u00e9llo', but got:\n" + combined
    )
    assert "h\ufffdllo" not in combined, (
        "Source line was mis-decoded under LC_ALL=C (mojibake):\n" + combined
    )
