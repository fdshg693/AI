---
paths:
  - "tools/integration/**"
---

# integration — このリポジトリの成果物を自分の環境へ取り込むための便利ツール群

このリポジトリの `claude-plugins/` 等をユーザー自身の環境（他リポジトリ・PC上の任意のディレクトリ）へ配置するためのツール群。導入手順そのもの（マーケットプレイス経由のインストール等）は [docs/integrations/](../../docs/integrations/) のOKF概念ドキュメントを参照。

## ツール一覧

- [scripts/](scripts/) — `config/` の設定に従って、スキル等のフォルダ/ファイルを複数の配置先へコピーするCLIツール（`skill-deploy` コマンド）。詳細は [scripts/README.md](scripts/README.md) 参照。
