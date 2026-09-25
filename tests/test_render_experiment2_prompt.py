from pathlib import Path

import pytest

from scripts.render_experiment2_prompt import render_prompt


ROOT = Path(__file__).resolve().parents[1]


def test_render_prompt_uses_current_condition_c_assembly_without_writing_files():
    prompt, prompt_hash = render_prompt("C", 1, root=ROOT)

    assert "STRUCTURED HISTORICAL BUG KNOWLEDGE" in prompt
    assert "SUPPORTED, WEAK, or NOT_APPLICABLE" in prompt
    assert len(prompt_hash) == 64
    assert all(character in "0123456789abcdef" for character in prompt_hash)
    assert not (ROOT / "prompt-renders").exists()


def test_render_prompt_refuses_to_overwrite_requested_output(tmp_path):
    output = tmp_path / "prompt.txt"
    output.write_text("keep me", encoding="utf-8")

    from scripts.render_experiment2_prompt import write_prompt

    with pytest.raises(ValueError, match="refusing to overwrite"):
        write_prompt(output, "new prompt", ROOT)

    assert output.read_text(encoding="utf-8") == "keep me"
