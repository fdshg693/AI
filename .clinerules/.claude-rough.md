---
paths:
  - ".claude/rough/**"
---

## `.claude/rough` 運用ルール

複雑なタスクに着手する前、要件や方針をまだ固めきれていない場合に自由形式で考えを書き出す場所（任意）。詳細は [.claude/rough/README.md](../rough/README.md) を参照。

- 形式は自由。[.claude/plans/README.md](../plans/README.md) の5点フォーマットに縛られない。サンプル: [.claude/rough/references/example.md](../rough/references/example.md)。
- シンプルなタスクでは経由不要。直接 `.claude/plans/` に詳細プランを書く。
- 方針が固まったら、必ず `.claude/plans/README.md` のフォーマットに従って `.claude/plans/` 配下に詳細プランへ整理してから実装に進むこと。ラフプランのままでは実装に着手しない。
