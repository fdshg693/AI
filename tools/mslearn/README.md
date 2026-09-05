# mslearn — fastmcp で自作した Microsoft Learn MCP CLI ラッパー

**関連スキル: `claude-plugins/my-tools/skills/ms-learn`**

`memo/00-overview.md` の調査結論としては、公式が Microsoft Learn MCP サーバー本体と
`microsoft-docs` / `microsoft-code-reference` の Agent Skill 一式を配布しており
(`/plugin install microsoft-docs@claude-plugins-official`)、それを直接使うのが最短ルート。

このツールはあえてそれを使わず、**Python の `fastmcp` ライブラリで MCP クライアントを自前で
立て、CLI でラップする** 学習目的の実装。CLI 経由にすることで、結果を他の CLI ツール
(`jq` など)に流し込んで柔軟にカスタマイズできる点が公式スキルにはない利点になる。

設計意図とセットアップはこのファイルに、AI に読ませる判断フロー・引数・出力形式は
`claude-plugins/my-tools/skills/ms-learn/SKILL.md` を参照。

## 前提条件

- Python 3.11+ / uv
- `fastmcp` パッケージ(下記インストール手順で入る)
- 認証不要(Microsoft Learn MCP サーバーは公開エンドポイント、API キー不要)

## インストール

グローバルCLIとして使う場合は `uv tool install --editable`(`pip install -e` の代替)で
エディタブルインストールする。リポジトリルートから実行可能。

```bash
uv tool install --editable tools/mslearn
```

インストール後は `mslearn` コマンドが PATH 上でどこからでも使える。

## 使い方

```bash
mslearn search "Azure Functions Python v2 programming model timeout"
mslearn code-search "blob storage upload" --language python
mslearn fetch https://learn.microsoft.com/azure/azure-functions/functions-versions
mslearn tools
mslearn call microsoft_docs_search --args '{"query": "..."}'
```

サブコマンド・オプション・出力形式・終了コードの詳細は
`claude-plugins/my-tools/skills/ms-learn/SKILL.md` を正本とする(AIが実行時に読む前提で
自己完結して書かれている)。

## このツールの目的

- `fastmcp.Client` で Streamable HTTP の MCP サーバーに接続し、`tools/list` / `tools/call`
  を直接叩く経験を積む(公式スキルは MCP プロトコルをホスト側が隠蔽してしまう)
- 3 つの公式ツール(`microsoft_docs_search` / `microsoft_docs_fetch` /
  `microsoft_code_sample_search`)それぞれに薄いサブコマンドを用意しつつ、
  サーバー側でツールが増減・改名されても詰まないよう `call <tool_name>` という
  汎用パススルーと、ハードコードに頼らず `tools/list` を都度呼ぶ `tools` サブコマンドを
  持たせる(`memo/01-mcp-server.md` に記載の「クライアントはツール一覧をハードコードせず
  動的に扱うべき」というベストプラクティスをそのまま踏襲)
- `--json` で全サブコマンドの出力を単一 JSON にでき、`jq` や他スクリプトへパイプできる
  ようにする(公式スキルにない、CLI ラップならではの柔軟性)

## 実装メモ(動作確認済みの実際のレスポンス形状)

各ツールを実際に叩いて確認した戻り値の形。`fastmcp` の `CallToolResult` は
`.data` / `.content` / `.structured_content` / `.is_error` を持つが、ツールごとに
埋まる場所が違う:

| ツール                         | 使うフィールド                                                  | 形                                                          |
| ------------------------------ | --------------------------------------------------------------- | ----------------------------------------------------------- |
| `microsoft_docs_search`        | `result.structured_content["results"]`                          | `list[{"title", "content", "contentUrl"}]`                  |
| `microsoft_code_sample_search` | `result.structured_content["results"]`                          | `list[{"description", "codeSnippet", "link", "language"}]`  |
| `microsoft_docs_fetch`         | `result.content[0].text`(`structured_content`/`data` は `None`) | Markdown 文字列丸ごと(タイトルは先頭の `# ` 見出しから復元) |

`microsoft_docs_fetch` に Microsoft Learn 以外の URL(例: `https://example.com`)を渡すと、
MCP レベルのエラーにはならず「The provided URL is not a valid Microsoft documentation
webpage link.」という説明文が本文として返ってくる(`is_error=False`)。エラー扱いにはならない
点に注意。

## `tav-cli` / `tav-lit` との違い

- API キー不要(Microsoft Learn MCP は公開エンドポイント)なので `.env` 管理が無い
- 監査ログ機構は持たない(必要になれば `tav-cli` の `TAVILY_WRITE_LOG` 相当を後から足せる)
- `--topic` のようなトピック単位の蓄積レイアウトは持たない。`search` / `code-search` /
  `fetch` のいずれも本文が大きくなりがちなので `tav-lit` の設計を踏襲し、
  1回の呼び出し(1クエリ/1URL)ごとに専用フォルダを作って結果を書き出し、
  標準出力には `index.md` のパスだけ出す(中身は出さない)。`index.md` の各行には
  その結果ファイルの文字数が付記されており、呼び出し側は index.md を読んで
  「読みたいファイル」をタイトルで選んだ上で、その中で文字数が大きいものだけを
  `aim-ask` に回す、という判断に使う(`ms-digest` スキル参照)。合計文字数のような
  集計値は、どのみち index.md を開いて中身を見る以上意味を持たないため出さない
  (`--json` を付けたときだけ全文入り JSON で標準出力に出し、ファイルは書かない)
- 出力フォルダは `NNNN-<クエリ or URL のスラッグ>/` で、同じクエリを再実行しても
  連番が進むだけで上書きされない(取得時点によって結果が変わりうるため)。
  並列実行時の連番衝突を避けるため、採番は出力ディレクトリ単位のファイルロックで
  直列化する。`search` / `fetch` の各結果ファイルは先頭見出しの直後に
  `URL:` 行を持ち（`fetch` は MCP 本文に無かった分をこちらで挿入する）、
  `aim-ask` が出典を転記できるようにする。
  `search` の結果のうち `learn.microsoft.com/answers/...`(Microsoft Q&A の
  コミュニティ回答)は公式ドキュメントと混ざらないよう `qa/` サブフォルダに分離し、
  ファイル名は連番のみ(`0001.md` など)。タイトル・リンク一覧はフォルダ直下の
  `index.md` にまとめる。

## ファイル構成

薄い CLI エントリポイント(`mslearn_cli.py`)と、責務ごとに分けた実装パッケージ
(`mslearn_core/`)に分離することで、1ファイルに argparse・MCP 接続・出力整形・
ファイル書き出しが全部混ざる状態を避けている(`tav-cli` の `tav_core` / `tav_cli` と
同じ分割方針)。

```text
tools/mslearn/
├── README.md              ← このファイル(設計意図・セットアップ)
├── pyproject.toml          ← `mslearn` コンソールコマンドのパッケージング
├── mslearn_cli.py           ← エントリポイント。argparse サブコマンド定義 + main()
├── mslearn_core/
│   ├── config.py             ← 定数(終了コード・既定エンドポイント・出力先 env var)
│   ├── client.py              ← `fastmcp.Client` のラッパー(接続・tools/call・tools/list)
│   ├── rendering.py           ← 生の結果1件 → `(category, title, markdown)` への変換
│   │                            (search/code-search/fetch それぞれの本文整形と、
│   │                            search の Q&A URL 判定、fetch への `URL:` 行挿入)
│   └── output.py              ← `(category, title, markdown)` のリスト →
│                                  クエリ/URL ごとの連番フォルダ書き出し
│                                  (`qa/` サブフォルダ分離 + `index.md` 生成) +
│                                  「index.md のパスだけ」の標準出力サマリ
├── tests/                  ← オフライン unittest（fetch の URL 行・並列採番）
└── memo/                   ← 事前調査メモ(公式 MCP サーバー/Agent Skill の調査結果)
```

`claude-plugins/my-tools/skills/ms-learn/` 側には `SKILL.md`(AI が実行時に読む判断フロー・
使い方)と `README.md`(スキルの設計意図)だけが残る。CLI 本体はこのライブラリ依存として
明示的に切り出してあり、スキル側から `mslearn_cli.py` を直接叩くことはしない。
