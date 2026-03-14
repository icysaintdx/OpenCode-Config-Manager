import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from occm_core.config_manager import ConfigManager


def test_load_json_supports_jsonc_with_trailing_commas(tmp_path: Path) -> None:
    path = tmp_path / "opencode.json"
    path.write_text(
        """
{
  // comment
  "provider": {
    "openai": {
      "npm": "@ai-sdk/openai",
      "options": {
        "baseURL": "https://api.openai.com/v1",
        "apiKey": "sk-test",
      },
      "models": {},
    },
  },
}
""",
        encoding="utf-8",
    )

    data = ConfigManager.load_json(path)

    assert isinstance(data, dict)
    assert "provider" in data
    assert "openai" in data["provider"]
