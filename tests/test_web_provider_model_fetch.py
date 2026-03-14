import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from occm_web.pages.provider import _build_model_list_urls, _extract_model_ids


def test_build_model_list_urls_with_v1_suffix() -> None:
    urls = _build_model_list_urls("https://api.example.com/v1")
    assert urls == ["https://api.example.com/v1/models"]


def test_build_model_list_urls_without_v1_suffix() -> None:
    urls = _build_model_list_urls("https://api.example.com")
    assert urls == [
        "https://api.example.com/v1/models",
        "https://api.example.com/models",
    ]


def test_extract_model_ids_from_openai_style_payload() -> None:
    payload = {
        "data": [
            {"id": "gpt-4o"},
            {"id": "gpt-5"},
        ]
    }
    assert _extract_model_ids(payload) == ["gpt-4o", "gpt-5"]
