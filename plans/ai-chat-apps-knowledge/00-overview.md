---
type: Plan
status: implementing-in-progress
---

## 実装ステータス

- [x] [01-research-official-sources.md](01-research-official-sources.md) — 3アプリの公式情報源と取得手段の調査
- [x] [02-baseline-scenarios.md](02-baseline-scenarios.md) — スキル無しのベースライン（RED）を取る
- [x] [03-skill-core-and-scripts.md](03-skill-core-and-scripts.md) — SKILL.md（ハブ）と取得・検索スクリプト
- [x] [04-web-feature-maps.md](04-web-feature-maps.md) — WEB版の機能マップ3本と横断比較表
- [x] [05-verify-and-register.md](05-verify-and-register.md) — GREEN 検証・メタ・カタログ・登録
- [ ] [06-desktop-apps.md](06-desktop-apps.md) — （余力があれば）デスクトップアプリ対応

# AIチャットアプリ（ChatGPT・Gemini・Claude）知識スキル 実装プラン - 概要

## 要件

- ChatGPT・Gemini・Claude の**利用者向けアプリ**（API・コーディングCLIではない）について、最新の公式情報に基づいて答えるスキルを1つ作る。
- まずは WEB 版（chatgpt.com / gemini.google.com / claude.ai）に対応する。デスクトップアプリ（必要ならモバイル）は余力があれば後続ステップで足す。
- 「ChatGPT の WEB 版で MCP サーバーを繋ぐには」「プロジェクトの上限は」のような機能の詳細を、少ない手順で公式ページまで辿れるようにする。アプリ間で同等の機能（Projects ↔ Gems ↔ Projects など）を引き比べられるようにする。
- 作り方は [writing-skill-complex](../../skills/plugins/cc-knowledge/skills/writing-skill-complex/SKILL.md) に沿う。サブエージェントでスキル無しのベースラインを取り（RED）、スキルを書き、同じシナリオで通ることを確かめる（GREEN）。構成もハブの SKILL.md ＋ 必要時に読む補助ファイル群にする。

## 実装ステップ

1. [01-research-official-sources.md](01-research-official-sources.md) — 公式ヘルプセンター・リリースノートの所在、sitemap/llms.txt の有無、取得可否（ボット遮断・JS 描画）を調べる
2. [02-baseline-scenarios.md](02-baseline-scenarios.md) — 評価シナリオを決め、スキル無しのサブエージェントで回答させて失敗の型を記録する
3. [03-skill-core-and-scripts.md](03-skill-core-and-scripts.md) — スキルの骨格（SKILL.md・README.md）と、索引ダウンロード・検索・ページ取得のスクリプトを作る
4. [04-web-feature-maps.md](04-web-feature-maps.md) — アプリごとの機能マップ（機能名 → 公式ページ URL・プラン制限・最終確認日）と横断比較表を書く
5. [05-verify-and-register.md](05-verify-and-register.md) — ステップ2のシナリオで GREEN を確認し、抜け穴を塞ぐ。meta・カタログ・プラグイン説明を更新する
6. [06-desktop-apps.md](06-desktop-apps.md) — （任意）デスクトップアプリの機能差分を同じ型で足す

## 主要な決定事項

| 決定                                                                                                                                             | 理由                                                                                                                                                                                                                                                                                                                              |
| ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 3アプリを1スキル `ai-chat-apps` にまとめる（アプリ別に3スキルへ分けない）                                                                        | 主な用途の1つが横断比較で、3つに分けると比較のたびに3スキルを読むことになる。アプリ別の詳細は補助ファイルに分けて段階的に読ませれば SKILL.md は太らない                                                                                                                                                                           |
| 置き場所は `skills/plugins/ai-tools-knowledge/skills/ai-chat-apps/`                                                                              | [repo-layout「置き場所の判定基準」](../../maintenance/docs/repo-layout.md#置き場所の判定基準)の「他 AI ツールの知識」に当たる。プラグインの説明文が「AI coding tools」に限っているので、ステップ5で説明文・keywords を広げる（ステップ1完了時点で `topics` の方が自然と判断したら変えてよい。その場合はこの表と各ステップを直す） |
| 情報は「機能マップ（手書き・短い）＋ 公式ページの都度取得」の2層にする                                                                           | 機能の存在・名前・対応関係は月単位でしか変わらないが、上限値・対応プラン・手順は頻繁に変わる。手書きで持つのは「どの機能がどのページに書かれているか」と最終確認日までにし、具体値は回答時に公式ページから取る                                                                                                                    |
| 回答時は「公式ページ ＞ リリースノート ＞ 一般 Web 検索」の順で根拠を取り、URL と確認日を必ず添える                                              | 学習データの記憶はこの領域で特に古くなりやすい（機能名の変更・提供範囲の拡大が速い）。ベースラインで実際にどう間違えるかはステップ2で確かめる                                                                                                                                                                                     |
| スクリプトは [writing-skill-web](../../skills/plugins/cc-knowledge/skills/writing-skill-web/SKILL.md) の `scripts/` テンプレートをコピーして使う | 索引ダウンロード・鮮度判定・ページ取得はリポジトリ内に実績のある型がある。クライアントを新しく書かない                                                                                                                                                                                                                            |
| 公式の索引が取れない情報源は、索引のスナップショットを持たず `web-lookup` スキル（`page` サブコマンド等）でその都度取る                          | 取得できない索引をスクリプト化しても壊れるだけ。ステップ1の結果、Claude（llms.txt）と ChatGPT（コレクションのクロール）はスクリプト化し、Gemini（sitemap にタイトルが無く、並列取得で CAPTCHA）は機能マップの手書き ID ＋ `web-lookup page` にした                                                                                |
| 英語版のヘルプを正にする                                                                                                                         | ChatGPT の日本語版リリースノートは英語版より約4か月遅れていた（ステップ1）                                                                                                                                                                                                                                                        |
| 置き場所は `ai-tools-knowledge` のまま                                                                                                           | ステップ1で `topics` に変える理由は見つからなかった                                                                                                                                                                                                                                                                               |

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照）

### 新規

- `skills/plugins/ai-tools-knowledge/skills/ai-chat-apps/SKILL.md`
- `skills/plugins/ai-tools-knowledge/skills/ai-chat-apps/README.md`（メンテナ向け。情報源・更新手順・テンプレートの出自）
- `skills/plugins/ai-tools-knowledge/skills/ai-chat-apps/chatgpt.md` / `gemini.md` / `claude-ai.md`（WEB 版の機能マップ）
- `skills/plugins/ai-tools-knowledge/skills/ai-chat-apps/comparison.md`（横断比較表）
- `skills/plugins/ai-tools-knowledge/skills/ai-chat-apps/webref_cli.py`・`download_index.py`・`search_index.py`・`fetch_claude_pages.py`・`download_url_index.py`（テンプレートのコピー）・`.gitignore`
- `skills/plugins/ai-tools-knowledge/skills/ai-chat-apps/output/claude-index.md`・`chatgpt-index.md`（索引スナップショット。コミットする。`output/temp/` はしない）
- `skills/plugins/ai-tools-knowledge/skills/ai-chat-apps/tests/scenarios.md`（評価シナリオと RED/GREEN の記録）
- （ステップ6）`.../ai-chat-apps/desktop.md`

### 変更

- `skills/plugins/ai-tools-knowledge/plugin.json`（description・keywords）
- `skills/plugins/ai-tools-knowledge/skills/CATALOG.md`（生成物。手編集しない）
- その他、pre-commit が再生成するカタログ類（`.claude-plugin/skill-catalog.json` 等。ステップ5で確認）

## ルール更新ポイント

- 新しいルールファイルは作らない。スキルの使い方はスキル自身（SKILL.md）、情報源と更新手順はスキルの `README.md` に書く。
- `registry/ai-tools.yaml` は既存のプラグイン `ai-tools-knowledge` にスキルを1つ足すだけなら変更不要の見込み。ステップ5で `changing-skills-and-tools` スキルの手順に照らして確認する。

## 進め方

- **TODO化**: ステップ一覧の各項目をそのまま1つの TODO にする。各ステップの実行主体・TODO 粒度は各ステップファイルの「進め方」節に書く。
- `skills/` はサブモジュール。スキル本体のコミットはサブモジュールの中で行い、アンブレラでポインタを更新する（2段階）。プランファイル自体はアンブレラ側。
