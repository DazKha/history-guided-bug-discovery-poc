import os
import subprocess
import sys
import textwrap


def test_utf8_source_line_preserved_under_c_locale(tmp_path):
    """A UTF-8 source file with a non-ASCII literal must be traced verbatim.

    PySnooper's get_source_from_frame decodes source bytes with the platform
    default encoding when no PEP-263 coding declaration is present.  Under
    LC_ALL=C that default is ASCII, so the non-ASCII bytes in the source line
    are replaced with U+FFFD and the emitted trace line no longer matches the
    real source text.
    """
    module_path = tmp_path / "pysnooper_utf8_target.py"
    module_path.write_text(
        textwrap.dedent(
            '''\
            import pysnooper


            @pysnooper.snoop()
            def greet():
                message = "h\u00e9llo"
                return message


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

    stdout = result.stdout.decode("utf-8", "replace")
    stderr = result.stderr.decode("utf-8", "replace")
    combined = stdout + stderr

    assert result.returncode == 0, combined
    assert "h\u00e9llo" in combined, (
        "Trace output did not contain the exact source text 'h\u00e9llo'; "
        "the source line was mis-decoded under LC_ALL=C.\n"
        "--- stdout ---\n%s\n--- stderr ---\n%s" % (stdout, stderr)
    )
    assert "h\ufffdllo" not in combined, (
        "Trace output contains the replacement character U+FFFD instead of "
        "the real source text 'h\u00e9llo'.\n"
        "--- stdout ---\n%s\n--- stderr ---\n%s" % (stdout, stderr)
    )
