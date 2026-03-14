import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from occm_core.model_fetch_utils import build_models_fetch_error_message


def test_403_cloudflare_1010_not_reported_as_expired_key() -> None:
    message = build_models_fetch_error_message(
        status_code=403,
        reason="Forbidden",
        api_key_present=True,
        response_body="error code: 1010",
    )
    assert "API Key可能无效或已过期" not in message
    assert "访问策略拦截" in message
    assert "Cloudflare 1010" in message


def test_401_without_api_key_prompts_for_api_key() -> None:
    message = build_models_fetch_error_message(
        status_code=401,
        reason="Unauthorized",
        api_key_present=False,
        response_body="",
    )
    assert "请先配置Provider的API Key" in message
