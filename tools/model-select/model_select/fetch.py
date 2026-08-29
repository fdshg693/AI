"""OpenRouter Models API（GET /api/v1/models）呼び出し。"""

from __future__ import annotations

import requests

MODELS_URL = "https://openrouter.ai/api/v1/models"
MODEL_AUTHORS = "openai,anthropic,google"


def fetch_models() -> list[dict]:
    """openai/anthropic/google のモデル一覧を取得し、レスポンスの``data``配列をそのまま返す。

    認証不要。ネットワーク例外・非200レスポンスはそのまま呼び出し元に伝播させる。
    """
    response = requests.get(MODELS_URL, params={"model_authors": MODEL_AUTHORS}, timeout=30)
    response.raise_for_status()
    return response.json()["data"]
