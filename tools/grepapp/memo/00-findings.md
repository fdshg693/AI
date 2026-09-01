# Grep MCP サーバー実測データ

調査日: 2026-09-02

## 検証方法

`fastmcp.Client` で `https://mcp.grep.app` に直接接続して検証した。Web記事は概要把握にのみ
使用し、スキーマ・レスポンス形状はすべて実測値を正とする。

## エンドポイント

- `https://mcp.grep.app` (Streamable HTTP、mslearn と同じ方式)
- ブラウザ直接アクセスは不可(MCPクライアント経由が前提)
- 認証不要(公開GitHubリポジトリのみが検索対象のため)

## 提供ツール(`tools/list` 実測)

`searchGitHub` の1つのみ。

Description(要約): "Find real-world code examples from over a million public GitHub
repositories" — キーワードや自然文ではなく、実際にコードに現れるリテラルなパターン
(`'useState('`, `'import React from'` 等)を渡す設計であることを強調している。
`useRegexp=true` で正規表現も使え、複数行にまたがるパターンは `(?s)` プレフィックスを
付ける運用(ツールの description に例あり)。

### inputSchema(実測、JSON Schema draft-07)

| パラメータ        | 型       | 必須 | デフォルト | 説明                                                                                |
| ----------------- | -------- | ---- | ---------- | ----------------------------------------------------------------------------------- |
| `query`           | string   | ✅   | -          | 検索するリテラルなコードパターン                                                    |
| `matchCase`       | boolean  | -    | `false`    | 大文字小文字を区別するか                                                            |
| `matchWholeWords` | boolean  | -    | `false`    | 単語単位でマッチするか                                                              |
| `useRegexp`       | boolean  | -    | `false`    | `query` を正規表現として解釈するか                                                  |
| `repo`            | string   | -    | -          | リポジトリ名で絞り込み(例: `'facebook/react'`)。部分一致可(`'vercel/'` で org 全体) |
| `path`            | string   | -    | -          | ファイルパスで絞り込み(例: `'/route.ts'`)。部分一致可                               |
| `language`        | string[] | -    | -          | 言語で絞り込み(例: `['TypeScript','TSX']`)                                          |

mslearn の `microsoft_docs_search` にあった `maxTokenBudget` のようなレスポンスサイズ
制御パラメータは存在しない。ページング用パラメータも存在しない。

## レスポンス形状(実測)

`CallToolResult` は `structured_content` も `data` も常に `None`。中身はすべて `content`
(TextContent のリスト)に入る。

- **ヒットありの場合**: 1マッチ(1ファイル)につき1つの TextContent ブロック。1クエリ
  あたり最大10ブロック(ページング手段がスキーマに無く、増やせない)。各ブロックの形式:

  ```text
  Repository: <owner/repo>
  Path: <file path>
  URL: <github blob URL>
  License: <license名 or "Unknown">

  Snippets:
  --- Snippet 1 (Line <N>) ---
  <該当行を含む複数行のコード>

  --- Snippet 2 (Line <M>) ---
  ...
  ```

  1ファイル内に複数マッチがあれば同じブロック内に `Snippet` が複数入る。

- **ヒット0件の場合**: ブロックが1つだけで、本文は
  `"No results found for your query."`(実測)。`is_error` は `False` のまま。

## 実測ログ(抜粋)

```
query='useState(', language=['TSX'], matchCase=True
  → 初回タイムアウト(timeout=20s)で 504 Gateway Timeout

query='CORS(', language=['Python'], matchCase=True (timeout=40s)
  → is_error=False, content blocks=10, 正常なブロック形式を確認

query='zzzzzz_this_should_never_match_anything_qqqqqq'
  → is_error=False, content blocks=1, text="No results found for your query."

query='useEffect(', repo='vercel/next.js', language=['TypeScript']
  → is_error=False, content blocks=10, repo/language絞り込みが機能することを確認
```

## 既知のリスク・注意点

- 初回呼び出しで `timeout=20` 秒だと `504 Gateway Timeout` が発生した(2回目以降、
  `timeout=40` 秒では成功)。コールドスタートか一時的な負荷かは切り分けられていないが、
  mslearn の既定30秒より長めのタイムアウトを既定にする方が安全(`config.py` では45秒)。
- レート制限は公式ブログ記事に明記が無い(grep.app の Web UI 自体は今回の調査中に
  一度 429 を返した)。CLI側で特別なリトライ・バックオフは実装しない(mslearnにも無い)が、
  README/SKILL.md には「レート制限は非公開」と明記しておく。
- 検索結果は最大10件固定で、ページング手段がスキーマに存在しない。1クエリで全件網羅は
  期待できない前提を SKILL.md の判断フローに書く。

## 参照URL

- https://vercel.com/blog/grep-a-million-github-repositories-via-mcp
- https://vercel.com/changelog/search-any-public-github-repo-with-grep
- https://grep.app
- https://mcp.grep.app (実エンドポイント、直接ブラウザアクセスは405)
