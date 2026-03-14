import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from occm_core.model_fetch_utils import extract_model_ids_from_opencode_models_output


def test_extract_model_ids_from_provider_prefixed_lines() -> None:
    output = "\n".join(
        [
            "opencode/gpt-5",
            "opencode/gpt-5.4",
            "openai/gpt-4o",
        ]
    )
    assert extract_model_ids_from_opencode_models_output(output, "opencode") == [
        "gpt-5",
        "gpt-5.4",
    ]


def test_extract_model_ids_deduplicates_and_ignores_noise() -> None:
    output = "\n".join(
        [
            "opencode/gpt-5",
            "INFO something",
            "opencode/gpt-5",
            "gpt-5.1-codex",
            "",
        ]
    )
    assert extract_model_ids_from_opencode_models_output(output, "opencode") == [
        "gpt-5",
        "gpt-5.1-codex",
    ]
