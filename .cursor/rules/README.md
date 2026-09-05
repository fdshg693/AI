# このフォルダについて

`.cursor/rules/` は意図的に空にしている（Project Rules を配置していない）。

以前は各ディレクトリの `AGENTS.md` を `tools/internal/plugin_meta/generate/generate_cursor_rules.py` でコピーし、`.mdc` ファイルとしてここに生成していた。しかし Cursor はネストした `AGENTS.md` をネイティブに読み込み、親ディレクトリの内容と結合して（より具体的な方を優先して）適用する（詳細は [cursor-plugins/meta/skills/cursor-memory/SKILL.md](../../cursor-plugins/meta/skills/cursor-memory/SKILL.md) 参照）。そのため生成した `.mdc` はリポジトリ各所の `AGENTS.md` と内容が重複するだけの二重管理になっており、削除した。

このリポジトリの `AGENTS.md` 群（ルート含む）をそのまま参照させれば Cursor 側の指示は足りる。

`generate_cursor_rules.py` 自体は参考実装として残しているが、lefthook や `justfile` の `generate` からは外してあり、このリポジトリでは実行されない。

**注意:** このファイルは `.md` 拡張子であり `.mdc` ではないため、Cursor の Project Rules としては解釈されない（Cursor は `.mdc` 以外を rules として無視する）。誤って rules として拾わせないためにも、このフォルダに `.mdc` ファイルを置かないこと。
