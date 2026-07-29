# llms.txt / llms-full.txt の実態（AWSドキュメント）

`docs.aws.amazon.com` に対して実際に `curl` してステータスコード・中身・サイズを確認した結果。

## 結論

| URL                                                                  | 存在   | サイズ                   | 中身                                                                                                   |
| -------------------------------------------------------------------- | ------ | ------------------------ | ------------------------------------------------------------------------------------------------------ |
| `https://docs.aws.amazon.com/llms.txt`                               | ✅ 200 | 約294KB                  | 全ガイド（数百件）の索引。各ガイドのタイトル・説明・トップページ`.md`リンク・ガイド別`llms.txt`リンク  |
| `https://docs.aws.amazon.com/llms-full.txt`                          | ✅ 200 | 約592KB                  | **`llms.txt` とほぼ同内容**（索引レベル）。"full" という名前だが全ページの本文が入っているわけではない |
| `https://docs.aws.amazon.com/<Service>/latest/<guide>/llms.txt`      | ✅ 200 | ガイドにより数十〜数百KB | **そのガイド1つ分**の全ページ一覧（タイトル・説明・`.md`リンク）。実質的な「サイトマップ+要約」        |
| `https://docs.aws.amazon.com/<Service>/latest/<guide>/llms-full.txt` | ❌ 404 | -                        | ガイド単位の `llms-full.txt` は存在しない                                                              |

つまり **AWS公式ドキュメントの `llms.txt` 系は「索引（ナビゲーション）」までで、本文全体を1ファイルに固めたものは提供していない**。本文が欲しい場合は、各ページの `.md` 版を個別に取得する必要がある（→ [03-custom-script-efficiency.md](03-custom-script-efficiency.md)）。

## 実例

### ルート `llms.txt`（抜粋）

```
# Amazon Web Services (AWS) Documentation
> This file provides structured access to AWS service documentation for large language models...

## Guides

- [Amazon Simple Storage Service User Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.md):
  Store data in the cloud... [llms.txt](https://docs.aws.amazon.com/AmazonS3/latest/userguide/llms.txt)
```

各エントリが「ガイドのトップページ`.md`リンク」＋「そのガイド専用の`llms.txt`へのリンク」の2段構成になっている。つまりルート`llms.txt`はエントリポイントで、実際に読みたいガイドが決まったら、そのガイド専用の`llms.txt`をさらに辿るのが正しい使い方。

### ガイド単位 `llms.txt`（例: S3 User Guide、抜粋）

```
# Amazon Simple Storage Service User Guide
> Learn how to use Amazon Simple Storage Service (Amazon S3)...

- [What is Amazon S3?](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.md)
- [Amazon S3 Object Lambda availability change](https://docs.aws.amazon.com/AmazonS3/latest/userguide/amazons3-ol-change.md)
...

## [Getting started](https://docs.aws.amazon.com/AmazonS3/latest/userguide/GetStartedWithS3.md)

- [Using Amazon S3 with the AWS CLI](https://docs.aws.amazon.com/AmazonS3/latest/userguide/GettingStartedS3CLI.md): ...
```

見出し構造（`##`/`###`）がそのままガイドの目次階層になっており、各ページへの`.md`直リンク付き。**このファイル1つを取得するだけで、そのガイドの全ページURL一覧と概要が手に入る**（後述のsitemap.xmlより取得が軽く、説明文も付いているぶん扱いやすい）。

## 注意点・落とし穴

1. **"full" という名前に反して全文は入っていない**。ルートの `llms-full.txt` を「これを1回読めばAWS全ドキュメントを読んだことになる」と誤解しないこと。中身は索引。
2. サードパーティのAWS関連プロジェクト（`docs.aws.amazon.com` 配下でホストされているが実体は別チーム管理、例: [AWS Powertools](https://docs.aws.amazon.com/powertools/typescript/latest/llms-full.txt)）は、**独自に本文入りの `llms-full.txt` を用意している場合がある**。これは AWS 全体の慣習ではなく、そのプロジェクトが個別に対応している例。存在確認は個別に必要。
3. AWS公式ブログ（`aws.amazon.com/blogs/...`）や re:Post（`repost.aws`）など、`docs.aws.amazon.com` 以外のAWSコンテンツには今回 `llms.txt` の存在を確認していない（未調査）。

## 出典

- [llms.txt / llms-full.txt 標準の説明（llmstxt.org）](https://llmstxt.org)
- 実測: `curl -sI https://docs.aws.amazon.com/llms.txt`, `curl -sI https://docs.aws.amazon.com/AmazonS3/latest/userguide/llms.txt`, `curl -sI https://docs.aws.amazon.com/AmazonS3/latest/userguide/llms-full.txt`（本メモ作成時に直接検証）
