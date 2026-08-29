# aim-ask

指定したファイルまたはディレクトリに同一プロンプトを並列に投げ、パスと応答の対応付きで結果を返すステートレスなCLIツールです。

## セットアップ

OPENROUTER_API_KEYを設定したうえで、リポジトリルートからインストールします。

```bash
uv tool install --editable tools/aim-use/aim-ask
```

## 使い方

```bash
aim-ask src/foo.py src/bar.py
aim-ask src/foo.py --prompt "このファイルのバグを指摘してください"
aim-ask claude-plugins/my-tools/skills/aim-ask --format json
```

--prompt、--model、--jobs、--format markdown|json、--full-content-namesを指定できます。設定ファイルはカレントディレクトリから親方向に.aim-use/aim-ask.tomlを探索します。

## 挙動

- ファイル1つ、またはディレクトリ1つを1パスとして扱い、パスごとにAI呼び出しを1回行います。複数パスは--jobsの範囲で並列実行します。
- ディレクトリは、.git、**pycache**、node_modules、.venv、venvを除いた相対パスのツリー listing と各ファイル内容を1つの入力にまとめます。
- バイナリ/UTF-8として読めないファイルは、ツリー listingに読み込みスキップの注記を残し、内容だけを除外します。
- 総サイズの上限や切り詰めはありません。大きなディレクトリは入力が大きくなり得るため、小規模なスキルフォルダを主な用途とします。参照ドキュメント一式などを抱えて大きくなりがちなディレクトリでは、`--full-content-names "SKILL.md,README.md"`のように内容を渡すファイル名を絞り込み、それ以外はツリー上のパスのみ（内容なし）にできます。

出力は既定でMarkdown、--format jsonでJSONです。各結果には入力文字列のpath、解決後のresolved_path、success、response、errorが含まれます。

## AI呼び出しのメタデータ

AI呼び出し時に`trace`（`tool: "aim-ask"`, `file_path`）と`session_id`（実行1回につき1つ、複数ファイルの呼び出しをまとめて識別）を付与しています。これにより`tools/aim`のログ（ローカルJSONL、設定していればGrafana Cloud側）で`aim`単体利用や他ツールと区別して分析できます。詳細は[tools/aim/README.md](../../aim/README.md)を参照してください。
