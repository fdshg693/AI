# .claude/rough

複雑なタスクに着手する前の「ラフプラン」置き場（任意）。

## 使うタイミング

- 要件や実装方針がまだ固まっておらず、複数の選択肢を比較したり迷っている点を書き出しながら考えを整理したい場合。
- シンプルなタスク（[.claude/plans/README.md](../plans/README.md) の「単一ファイルで完結」基準に収まるもの）では不要。ラフプランを経由せず直接 `.claude/plans/` に詳細プランを書く。

## 書き方

形式は自由。[.claude/plans/README.md](../plans/README.md) が定める5点フォーマット（やること／読むべきファイル・推奨Grep／触るファイル／決定事項・注意点／`.claude/rules`更新ポイント）に従う必要はない。比較検討中の案、迷っている点、未解決の疑問をそのまま書いてよい。

サンプル: [references/example.md](references/example.md)。[.claude/plans/references/](../plans/references/) の詳細プラン例と同じ架空機能を題材に、詳細プランを書く前段階の書き殴り方を示している。

## 次のステップ

方針が固まったら、ラフプランの内容を [.claude/plans/README.md](../plans/README.md) のフォーマットに従って `.claude/plans/` 配下の詳細プランへ整理する。実装は詳細プランを正として進め、ラフプランのままでは着手しない。ラフプラン自体は削除必須ではなく、検討経緯の記録として残しておいてよい。
