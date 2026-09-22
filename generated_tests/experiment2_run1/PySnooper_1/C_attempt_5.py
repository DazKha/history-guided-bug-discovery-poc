import io
import os
import sys
import tempfile

import pytest

import pysnooper


def test_file_output_non_ascii_under_ascii_locale(tmp_path):
    path = tmp_path / 'foo.log'

    @pysnooper.snoop(str(path))
    def my_function():
        value = 'caf\u00e9'
        return value

    result = my_function()
    assert result == 'caf\u00e9'

    assert path.exists(), 'trace output file was not created at the requested path'
    output = path.read_text(encoding='utf-8')
    assert 'caf\u00e9' in output

