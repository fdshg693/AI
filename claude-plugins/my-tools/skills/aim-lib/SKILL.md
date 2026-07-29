---
name: using-aim-library
description: "`tools/aim` のグローバルインストール済み Python 実装をライブラリとして使い、OpenRouter 経由で AI モデルへ単発リクエストを送る方法を説明する。Python コードからプロンプトを送信したい、モデル略記を解決したい、応答本文を取り出したい場合に使う。CLI コマンドを実行する場合は `aim-cli` を使う。"
meta:
  requires_repo_tools: tools/aim
  requires_env: OPENROUTER_API_KEY
  dependencies: aim-cli, python>=3.11
  requires_install: tools/aim (uv tool install --editable tools/aim)
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.0
---

# aim を Python ライブラリとして使う

`tools/aim` は現在、独立した `aim` Python パッケージではなく、`aim_cli` モジュールとして配布されている。ライブラリ利用では `aim` コマンドや `aim_cli.main()` を呼ばず、`aim_cli` が提供する薄いラッパー（`create_client` / `call` / `call_async` / `AimError`）を使う。**`openrouter` を直接 import しない** — `openrouter` への依存はパッケージの依存関係にも追加しない。理由は2つ。

- `aim_cli` 側だけが `openrouter` に依存する構成にすることで、利用側パッケージの依存を `aim-cli` 1つに絞れる
- ログ記録（`calls.jsonl` への追記）が `call`/`call_async` の内部で行われるため、将来 `aim_cli` にログ処理を追加・変更しても、利用側は変更なしにその恩恵を受けられる

## 前提条件

- `tools/aim` がグローバル環境にインストール済みであること（README の前提どおり `uv tool install --editable tools/aim`）
- Python 3.11 以上を使うこと
- `OPENROUTER_API_KEY` が環境変数、または `tools/aim/.env` に設定済みであること。環境変数が優先される
- 未インストール・API キー未設定の場合、このスキルでインストールやキー発行を行わず、`tools/aim/README.md` のセットアップ手順を案内する

## 基本パターン（同期）

```python
from aim_cli import MODELS, create_client, call


def ask_aim(prompt: str, model: str = "mini-m3") -> str:
    if not prompt.strip():
        raise ValueError("prompt must not be empty")

    try:
        model_id = MODELS[model]
    except KeyError as e:
        available = ", ".join(sorted(MODELS))
        raise ValueError(f"unknown model {model!r}; choose one of: {available}") from e

    with create_client() as client:
        return call(client, model_id, prompt)


print(ask_aim("フランスの首都は？"))
```

モデル略記を OpenRouter の実 ID に変換するため、`MODELS[model]` を使う。`mini-m3` を通常の既定値とし、単純な下書きや定型変換だけなら `gpt-120b`、より高い精度・推論力が必要なら `glm-5.2` または `gpt-luna` に切り替える。

利用可能な略記と実際のモデル ID は次のとおり（`aim --list-models` の出力が正）。

| 略記       | OpenRouter モデル ID       | 用途                           |
| ---------- | -------------------------- | ------------------------------ |
| `gpt-120b` | `openai/gpt-oss-120b:free` | 非常に簡単で精度を求めない処理 |
| `mini-m3`  | `minimax/minimax-m3`       | 通常の既定値                   |
| `glm-5.2`  | `z-ai/glm-5.2`             | `mini-m3` では不足する処理     |
| `gpt-luna` | `openai/gpt-5.6-luna`      | 特に高精度が必要な処理         |

## 非同期（並列実行）で使う

`aim_cli.create_client()` が返すクライアントは、同期版の `call()` に加えて非同期版の `call_async()` からも同じクライアントで使い回せる。複数プロンプトを並列に投げたい場合、CLIを複数プロセス/スレッドで叩く代わりに、単一プロセス・単一イベントループ上で `asyncio.gather` を使えばOSスレッドを使わずに並行実行できる。

```python
import asyncio

from aim_cli import MODELS, create_client, call_async


async def ask_aim_many(prompts: list[str], model: str = "mini-m3", max_concurrency: int = 4) -> list[str]:
    model_id = MODELS[model]
    semaphore = asyncio.Semaphore(max_concurrency)

    async def one(client, prompt: str) -> str:
        async with semaphore:
            return await call_async(client, model_id, prompt)

    async with create_client() as client:
        return await asyncio.gather(*(one(client, p) for p in prompts))


print(asyncio.run(ask_aim_many(["フランスの首都は？", "日本の首都は？"])))
```

- 同じクライアントを `async with` 1つで開き、複数の `call_async` 呼び出しで使い回す（コネクションプールが再利用され、リクエストごとに新規プロセス/新規コネクションを作らずに済む）
- 同時実行数の上限は `ThreadPoolExecutor(max_workers=...)` ではなく `asyncio.Semaphore(...)` で制御する。`config.toml` の `jobs` のような同時実行数設定は、この `Semaphore` の初期値にそのまま渡せる
- 呼び出し元が同期コードの場合は `asyncio.run(...)` の中に非同期処理を閉じ込める（実例: `tools/aim-use/aim-summarize/aim_summarize/cli.py` の `_generate_all_async` / `summarizer.generate_summary_async`）
- 単発・逐次呼び出ししかしないなら同期版（`call`）で十分。非同期版（`call_async`）は「複数リクエストを並列に送りたい」場合にのみ選ぶ

## エラー処理

API 呼び出しをアプリケーション内で扱う場合は、`aim_cli.AimError` を捕捉して呼び出し元へ伝播する（内部の `openrouter.errors.OpenRouterError` は `AimError` にラップされるため、呼び出し側は `openrouter` を import しなくてよい）。`resolve_api_key()`（`create_client()` が内部で呼ぶ）は API キーがないと CLI 用にメッセージを出して `SystemExit` するため、ライブラリとして独自のエラー契約が必要なら、呼び出し前に API キーを検証するか、キー解決処理をアプリケーション側で行う。

```python
from aim_cli import AimError


try:
    answer = ask_aim(prompt, model="glm-5.2")
except AimError as e:
    # 401 / 402 / 429 など。必要に応じて再試行・フォールバックする
    raise RuntimeError("OpenRouter API request failed") from e
```

## CLI 版との違い

- ライブラリ版は `aim` コマンドを起動せず、Python プロセス内で呼び出す
- 標準入力・標準出力・`argparse` は使わない。戻り値の文字列を呼び出し元で処理する
- `call`/`call_async` はCLI版と同じ `calls.jsonl` への監査ログ追記を内部で行う（呼び出し元が明示的にログを書く必要はない）
- このツールの契約は user メッセージ 1件の単発呼び出しであり、system プロンプト・マルチターン・エージェント機能は扱わない

クライアントは必ず `with`（非同期なら `async with`）ブロックで使う。API キーやプロンプトを例外メッセージ・標準出力・不要なログへ出力しない。`openrouter` パッケージを直接 import する必要はなく、依存関係にも追加しない — `aim_cli` の `create_client`/`call`/`call_async`/`AimError` のみで完結させる。
