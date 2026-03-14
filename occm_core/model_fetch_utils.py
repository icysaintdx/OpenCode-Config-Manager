from typing import Optional


def _safe_snippet(text: str, limit: int = 160) -> str:
    value = (text or "").strip().replace("\n", " ").replace("\r", " ")
    if len(value) <= limit:
        return value
    return value[:limit] + "..."


def decode_http_error_body(body: bytes) -> str:
    if not body:
        return ""
    try:
        return body.decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""


def build_models_fetch_error_message(
    status_code: int,
    reason: str,
    api_key_present: bool,
    response_body: Optional[str] = None,
) -> str:
    body_text = (response_body or "").strip()
    body_lower = body_text.lower()
    base = f"HTTP {status_code}: {reason}"

    if status_code in (401, 403):
        if not api_key_present:
            return f"{base}\n\n该API需要认证。请先配置Provider的API Key。"

        if "error code: 1010" in body_lower or "cloudflare" in body_lower:
            return (
                f"{base}\n\n请求被访问策略拦截（Cloudflare 1010），"
                "不一定是 API Key 问题。请检查网络/IP/地区限制。"
            )

        if any(
            token in body_lower
            for token in (
                "invalid api key",
                "api key is invalid",
                "unauthorized",
                "invalid authentication",
                "incorrect api key",
            )
        ):
            return f"{base}\n\nAPI Key 可能无效或已过期。"

        snippet = _safe_snippet(body_text)
        if snippet:
            return (
                f"{base}\n\n认证被拒绝，但返回内容未明确指向 API Key 失效：\n"
                f"{snippet}"
            )

        return f"{base}\n\n认证被拒绝，可能是 API Key、网络策略或服务端权限策略导致。"

    snippet = _safe_snippet(body_text)
    if snippet:
        return f"{base}\n\n响应摘要: {snippet}"
    return base


def extract_model_ids_from_opencode_models_output(
    output: str, provider_name: str
) -> list[str]:
    model_ids: list[str] = []
    seen: set[str] = set()
    prefix = f"{provider_name}/"

    for raw_line in (output or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        model_id = ""
        if line.startswith(prefix):
            model_id = line[len(prefix) :].strip()
        elif "/" not in line and " " not in line and "\t" not in line:
            model_id = line

        if model_id and model_id not in seen:
            seen.add(model_id)
            model_ids.append(model_id)

    return model_ids
