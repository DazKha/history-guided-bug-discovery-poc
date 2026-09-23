import os
import sys
import tempfile
import subprocess
import textwrap


def test_utf8_source_without_coding_declaration_under_c_locale():
    """
    PySnooper's get_source_from_frame decodes source files using the platform default
    encoding when no PEP-263 coding declaration is present.  Under LC_ALL=C the
    default encoding is ASCII, so a UTF-8 source file containing non-ASCII characters
    is mis-decoded (mojibake).  The trace output must still contain the exact Unicode
    text 'héllo' as written in the source file.
    """
    # Create a temporary directory for the test module and its output.
    with tempfile.TemporaryDirectory() as tmpdir:
        module_path = os.path.join(tmpdir, "utf8_source_module.py")
        output_path = os.path.join(tmpdir, "trace_output.txt")

        # Write a UTF-8 encoded module with a non-ASCII string literal and no coding
        # declaration.  The function is decorated with @pysnooper.snoop() and writes
        # the trace to a file so we can inspect it after the subprocess finishes.
        source = textwrap.dedent(
            '''\
            import pysnooper

            @pysnooper.snoop("{output_path}")
            def greet():
                message = "héllo"
                return message

            greet()
            '''
        ).format(output_path=output_path)

        with open(module_path, "w", encoding="utf-8") as f:
            f.write(source)

        # Run the module in a subprocess with LC_ALL=C so that the default locale
        # encoding is ASCII.  This forces the buggy decoding path in PySnooper.
        env = os.environ.copy()
        env["LC_ALL"] = "C"
        env["LANG"] = "C"
        env["PYTHONIOENCODING"] = "utf-8"

        result = subprocess.run(
            [sys.executable, module_path],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # The subprocess should succeed; if it fails, the test cannot evaluate the
        # hypothesis.
        assert result.returncode == 0, (
            f"Subprocess failed with return code {result.returncode}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Read the trace output produced by PySnooper.
        with open(output_path, "r", encoding="utf-8") as f:
            trace_output = f.read()

        # The trace must contain the exact Unicode text 'héllo' as written in the
        # UTF-8 source file.  If the bug is present, the non-ASCII bytes are decoded
        # as ASCII with 'replace', producing 'h\ufffdllo' instead.
        assert "héllo" in trace_output, (
            "Trace output does not contain the exact Unicode text 'héllo'.\n"
            "This indicates that the source line was mis-decoded under LC_ALL=C.\n"
            f"Trace output:\n{trace_output}"
        )

        # Additionally, ensure the mojibake replacement character is not present in
        # the line that should contain the literal.
        assert "h\ufffdllo" not in trace_output, (
            "Trace output contains the replacement character U+FFFD instead of 'é', "
            "confirming the locale-dependent decoding bug.\n"
            f"Trace output:\n{trace_output}"
        )
