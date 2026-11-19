---
type: Research Notes
title: "サイト偵察（site recon）実測メモ"
description: "Records measurements of cheap site reconnaissance before opening a browser (curl for robots/sitemap/llms.txt, link extraction, coverage against the local test sites, Tavily map cost) behind the using-playwright-cli site-recon reference. Use when changing that reference or deciding whether to use pwq or a search API for recon."
tags: [tools]
status: stable
step: site recon 実測（調査 plan 04 の退避）
verified-on: 2026-09-15
verified-with: "@playwright/cli 0.1.19, Windows 11 Pro 26200, Git Bash, python tools/browser/test-sites/serve.py (SimpleHTTP/0.6 Python/3.13.9)"
---

# サイト偵察（site recon）実測メモ

手順としての結論は `site-recon.md`（`using-playwright-cli` スキル） にまとめてある（このファイルはその根拠）。
調査 plan `site-recon-research` の 04 を、plan 削除にあたり原データとして退避したもの。**§9 の「05 への引継ぎ」は
すべてリファレンス側に反映済み**なので、参照用に残してあるだけ。

## 測定条件（これが無いと再現できない）

| 項目                  | 値                                                                                                                |
| --------------------- | ----------------------------------------------------------------------------------------------------------------- |
| 日付                  | 2026-09-15                                                                                                        |
| OS / シェル           | Windows 11 Pro 26200 / Git Bash                                                                                   |
| `playwright-cli`      | 0.1.19（グローバル pnpm 導入、`PLAYWRIGHT_CLI_SESSION=recon04`）                                                  |
| `pwq`                 | `pwq`、既定モデル `flash-lite`（`google/gemini-2.5-flash-lite`）                                                  |
| ローカルサーバ        | **`python tools/browser/test-sites/serve.py`**（`SimpleHTTP/0.6 Python/3.13.9`）。nginx は未導入                  |
| 単位                  | 会話に流れる stdout のバイト数（`wc -c`）。生出力はスクラッチパッドへ落として測り、本文には出していない           |
| 外部アクセス          | 02 §7 の R1〜R7 の範囲内。docs.tavily.com 9 リクエスト / playwright.dev 3 リクエスト、いずれも 1 秒以上あけて直列 |
| Tavily クレジット消費 | 約 25（`map` 3 回）。無料枠 1,000/月 に対して 2.5%                                                                |

比較の形式は `context-saving-explore.md §2`（`browser-context-tools` スキル） に揃えた。

---

## 0. 結論サマリ（05 が前提にしてよい事実）

| #   | 事実                                                                                                                                                                                                                                | 根拠    |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| 1   | **リンク収集は、同じ網羅率をベースラインの 5% のバイト数で出す。** `/catalog/` で 6,200 B → 331 B、LLM 呼び出し 3 回 → 0 回                                                                                                         | §1      |
| 2   | **`a[href]` だけでは足りない。`iframe[src]` を足すと `/frames/` の網羅率が 40% → 80% に跳ねる。** セレクタ 1 個の差で 2 倍                                                                                                          | §3      |
| 3   | **深さ 1 のクロールで `/frames/` は 100%、`/catalog/` は 80% で頭打ち。** 残り 1 枚は `location.href = 'complete.html'` で遷移するため**リンクグラフには原理的に出ない**                                                            | §1 / §3 |
| 4   | **`/tables/` は URL 網羅率 100%・コンテンツ網羅率 23%。** 43 行中 DOM にあるのは常に 10 行だけで、ページ送りでも URL が変わらない。**偵察の対象外**と判定するのが正しい                                                             | §2      |
| 5   | **ローカル `tools/browser/test-sites/` には robots / sitemap / llms.txt が 1 つも無い（3 連続 404）。** シグナル経路の空振りコストは GET 3 回・約 15 B。**安いので先に撃ってよい**                                                  | §4      |
| 6   | **sitemap はヒストグラムに畳むと 20 倍圧縮。** docs.tavily.com で 15,145 B → locs 6,219 B → **745 B**。02 の playwright.dev（440 分の 1）と同じ性質                                                                                 | §5      |
| 7   | **`llms.txt` は sitemap の代わりにならない。** URL 集合は 98 重複／sitemap 側のみ 8／llms.txt 側のみ 4。**llms.txt のほうが古い**。加えて `example.com` などのプレースホルダを含む                                                  | §5      |
| 8   | **`llms-full.txt` は 854,745 B。** 会話に入れてはならない桁。存在確認だけして本文は取らない                                                                                                                                         | §5      |
| 9   | **Tavily `map` は sitemap の上積みとして割に合わなかった。** docs.tavily.com で 150 URL / 15 クレジットを使って、sitemap に無い**生きた新規ページは 1 枚だけ**。残りは 404 が 5 件・リダイレクト 3 件・`.md` 重複・別ドメイン 34 件 | §6      |
| 10  | **playwright.dev では map は sitemap の部分集合だった**（72/359 をカバー、新規 3 件はすべて別言語サイトへの 301）。**map ⊂ sitemap は 1 サイト固有の癖ではない**                                                                    | §6      |

**一行でいうと**: 偵察の主役は `sitemap.xml`（無ければ `iframe[src]` 込みの深さ 1 リンクグラフ）。
`llms.txt` は補助、Tavily `map` は基本不要。**LLM に読ませるのは最後**。

---

## 1. `/catalog/` — ページ遷移のあるサイト

正解集合は `tools/browser/test-sites/catalog/*.html` の 5 枚（`index` / `item` / `cart` / `checkout` / `complete`）。

| #   | 経路             | コマンド                                 |      stdout | 往復 | LLM | 発見ページ          |        網羅率 |
| --- | ---------------- | ---------------------------------------- | ----------: | ---: | --: | ------------------- | ------------: |
| 1   | ベースライン     | `pwq explore` + `ask` ×2                 | **6,200 B** |    1 |   3 | index / cart / item |     3/5 = 60% |
| 2   | リンク収集       | `playwright-cli --raw eval` の `a[href]` |   **331 B** |   0※ |   0 | index / cart / item |     3/5 = 60% |
| 3   | 深さ 1 クロール  | 上を各リンクで反復                       |   **378 B** |    7 |   0 | + checkout          | **4/5 = 80%** |
| 4   | サイト側シグナル | `curl` ×3                                |     約 15 B |    3 |   0 | なし（全 404）      |            0% |

※ 経路 2 は開いているページに対する `eval` なので追加のナビゲーションが 0。単独で使うなら `goto` 1 回が乗る。

ベースラインの内訳: `explore` 3,835 B ＋ `ask`「どんなページがあるか」1,222 B ＋ `ask`「遷移先の URL」1,143 B。
**2 回の `ask` は経路 2 と同じ URL 集合しか出さなかった**（`item.html?id=p1`〜`p5` と `cart.html`）。
つまり **6,200 B 払って 331 B と同じ答えを買っている**。

### 80% で止まる理由（重要）

```
tools/browser/test-sites/catalog/checkout.html:41:    location.href = 'complete.html';
```

`complete.html` を指す `<a href>` はサイト内に 1 つも無い。
**深さを増やしても、JS を実行しても、リンクグラフでは到達できない。**
「クロールの深さが足りない」のではなく**リンクグラフという表現の限界**で、
05 の判断表では「フォーム送信・`location.href` の先は別手段（実際に操作する）」と分けて書く必要がある。

---

## 2. `/tables/` — URL が増えないのにコンテンツが変わる

正解集合は `tools/browser/test-sites/tables/index.html` の 1 枚。プラン側は「ここで網羅率が破綻することを期待して測る」と書いた。**破綻した。ただし期待とは逆向きに。**

| #   | 経路            |      stdout | 発見 URL             | URL 網羅率 | コンテンツ網羅率 |
| --- | --------------- | ----------: | -------------------- | ---------: | ---------------: |
| 1   | ベースライン    | **4,834 B** | `/` のみ             | 1/1 = 100% |   10/43 行 = 23% |
| 2   | リンク収集      |   **142 B** | `/` + `#a` `#b` `#c` | 1/1 = 100% |   10/43 行 = 23% |
| 3   | 深さ 1 クロール |           — | 新規 0               |          — |         変わらず |

実測（`--raw eval`）:

```json
{ "visibleRows": 10, "allRows": 10, "url": "http://localhost:8080/tables/" }
```

ソース側は `DATA = Array.from({ length: 43 })` / `PER_PAGE = 10` / 総ページ数 5。
**DOM には常に 10 行しか無く、ページ送りでも URL は変わらない。**

読み取れること 3 つ。

1. **URL 網羅率 100% は「調べ終わった」を意味しない。** 偵察の出力に「このページは URL に現れない状態を持つ」という
   フラグが要る。判定は安い — `#` だけのリンク、`button` によるページ送り、`aria-label="ページ送り"` の有無で分かる
2. 逆に **リンク収集は 142 B で「このサイトは 1 枚しか無い」と即答した**。ベースラインの 4,834 B と同じ結論。34 分の 1
3. **ここはリンクグラフではなく操作（`click` + 再 `snapshot`）の領分**。偵察フェーズは「1 枚・状態あり」と判定して
   早く抜け、`pwq explore` → `ask` に渡すのが正しい使い分け

---

## 3. `/frames/` — リンクグラフが素直でないケース

正解集合は `tools/browser/test-sites/frames/*.html` の 5 枚（`index` / `inner-form` / `inner-frame` / `outer-frame` / `popup`）。

| #   | 経路            | セレクタ                         |      stdout | 往復 | 発見                                              |         網羅率 |
| --- | --------------- | -------------------------------- | ----------: | ---: | ------------------------------------------------- | -------------: |
| 1   | ベースライン    | —                                | **5,189 B** |    1 | index / popup（他は「URL は記載されていません」） |      2/5 = 40% |
| 2a  | リンク収集      | `a[href]`                        |    **76 B** |    0 | index / popup                                     |      2/5 = 40% |
| 2b  | リンク収集      | `a[href],iframe[src],frame[src]` |   **177 B** |    0 | + inner-form / outer-frame                        |  **4/5 = 80%** |
| 3   | 深さ 1 クロール | 2b と同じ                        |   **200 B** |    4 | + inner-frame                                     | **5/5 = 100%** |

**この表がこのステップでいちばん効く結果。**

- `iframe[src]` を足すコストは **101 B**。網羅率は **40% → 80%**。**セレクタを 2 つ足すだけの話**なので、
  リンク収集のセレクタは最初からこれを既定にすべき
- `inner-frame.html` は `outer-frame.html` の中の iframe。**入れ子は深さ 1 のクロールで拾える**
  （トップの iframe を「ページ」として辿るため）
- ベースラインの `ask` は frame の存在は挙げたが **URL は 1 つも出せなかった**。
  snapshot には frame の src が載らないため。**LLM の読解力の問題ではなく入力に情報が無い**。
  5,189 B 払っても出ないものは出ない

---

## 4. ローカルにサイト側シグナルは無い（空振りのコスト測定）

```
robots.txt          404 text/html 335B
sitemap.xml         404 text/html 335B
llms.txt            404 text/html 335B
catalog/sitemap.xml 404
catalog/llms.txt    404
```

`serve.py` は静的配信のみなので当然だが、**空振りが安いことの実測値**として意味がある。

- 会話に流れるのは `-o` でボディを捨てた**ステータス行だけ＝約 15 B**（3 行）
- 404 ボディの 335 B は `text/html` のエラーページ。**`-w '%{http_code} %{content_type}'` を見ずに
  ボディを読むと「サイトマップが取れた」と誤認する**（02 のソフト 404 判定がここで効く）
- 結論: **シグナル 3 連射は常に先に撃ってよい。** 外れても 15 B。当たれば §5 のとおり本命

---

## 5. 外部実サイト① docs.tavily.com — シグナルが全部揃っている例

R1 に従い `robots.txt` から。

```
User-agent: *
Content-Signal: ai-train=yes, search=yes, ai-input=yes
Disallow: /cdn-cgi/
Allow: /_next/image
Disallow: /_next/
Sitemap: https://docs.tavily.com/sitemap.xml
```

**02 の playwright.dev（`UserAgent:` のタイポで群が成立しない・`Sitemap:` 行なし）とは真逆の優等生。**
`Content-Signal:`（`ai-input=yes` ＝ AI からの参照を許可）が付いているのも初見で、
**robots.txt は RFC 9309 の枠を超えて拡張が入り続けている**ことの実例。パーサは未知フィールドを黙って無視する必要がある。

### 取得結果と圧縮率

| 対象            |            生 |           URL だけ | パス接頭辞ヒストグラム |             圧縮比 |
| --------------- | ------------: | -----------------: | ---------------------: | -----------------: |
| `sitemap.xml`   |      15,145 B | 6,219 B（106 URL） |     **745 B**（25 行） | **20.3 倍 / 4.9%** |
| `llms.txt`      |      17,513 B | 6,463 B（110 URL） |                      — |                  — |
| `llms-full.txt` | **854,745 B** |                  — |                      — | **会話に入れない** |

ヒストグラム（745 B）だけで「このサイトは 106 ページ、うち 41 が integrations、10 が api-reference」が分かる。
**LLM 呼び出し 0 回。**

### `llms.txt` と `sitemap.xml` は別物だった

素朴に集合比較すると **重複 0**。理由は llms.txt 側の URL が全部 `.md` 付き（Mintlify の慣習）だから。
`.md` を落として自ドメインだけに絞ると:

|                   |                                                                                                                                                           件数 |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| 両方にある        |                                                                                                                                                             98 |
| **sitemap のみ**  | **8** — `integrations/langfuse`, `integrations/nanoclaw`, `integrations/pi`, `integrations/portkey`, `examples/use-cases/slack-research-agent`, `welcome` ほか |
| **llms.txt のみ** |                                                                        **4** — `api-reference/openapi.json`, `documentation/help`, `llms.txt`, `llms-full.txt` |

- **sitemap のほうが新しい。** llms.txt に無い 8 件は新規追加ページに見える。
  llms.txt は**手動 or 別パイプラインで生成され、遅れる**
- llms.txt の独自価値は `openapi.json` のような**ページではない資産**を指すこと
- **llms.txt には `https://docs.example.com` / `https://example.com` が混ざっている**（本文中のサンプル由来）。
  URL を機械抽出すると**存在しないサイトを実在扱いする**。R6（untrusted）はここで具体的に効く

---

## 6. Tavily `map` は sitemap の上積みになるか → **ならなかった**

### docs.tavily.com

| 設定                                     | 返却 URL |   所要 |    JSON | クレジット |
| ---------------------------------------- | -------: | -----: | ------: | ---------: |
| `limit=50, max_depth=1`                  |       20 |  1.0 s | 1,048 B |          2 |
| `limit=150, max_depth=2, max_breadth=50` |      150 | 13.0 s | 8,236 B |         15 |

`max_depth` を 1 → 2 にすると**所要が 13 倍**（公式の「レイテンシは指数的」の注意書きどおり）。

150 URL の内訳:

|                                               |                                     件数 |
| --------------------------------------------- | ---------------------------------------: |
| 別ドメイン（app./community./discord/mcp. 等） |                                   **34** |
| 自ドメイン（`.md` 正規化後、ユニーク）        |                                      109 |
| うち sitemap に無い                           |                                       14 |
| **うち実在する新規ページ**                    | **1**（`/documentation/search-crawler`） |
| 同時に、sitemap にあるのに map が落とした URL |                                   **11** |

sitemap に無い 14 件を `curl` で検証した内訳:

| URL                                                                       | 結果                                                    |
| ------------------------------------------------------------------------- | ------------------------------------------------------- |
| `/articles/*` ×5（`student-account`, `how-can-i-create-an-api-key` ほか） | **404**                                                 |
| `/guides/quickstart`                                                      | 308 → `/documentation/quickstart`（sitemap にある）     |
| `/integrations/langchain`, `/integrations/llamaindex`                     | 308 → `/documentation/integrations/*`（sitemap にある） |
| `/documentation/help`                                                     | 307 → `https://help.tavily.com/`（**別ホスト**）        |
| `/documentation/search-crawler`                                           | **200 — これだけが本物の新規**                          |
| ルート・`llms.txt`・`llms-full.txt`・`/index`                             | 実質重複                                                |

**15 クレジットと 13 秒を払って、得たのは 1 ページ。** しかも**死 URL を 5 件掴まされた**。
02 の R6 は「テキストが untrusted」だったが、ここでは **URL 集合そのものが検証を要する**ことが分かった。

唯一まともな収穫は `/documentation/help` → `help.tavily.com` という**別ホストへの越境を見つけたこと**。
sitemap は自ホストしか書かないので、ここは map の構造的な強み。

### playwright.dev（02 で robots が壊れていたサイト）

R2 に従い「群が 1 つも成立しない」ため上限を半分（`limit=75`）にして実行。

|                                  |                                                                       値 |
| -------------------------------- | -----------------------------------------------------------------------: |
| `sitemap.xml`                    |                            44,496 B / **359 URL**（URL だけで 16,877 B） |
| `llms.txt`                       |                                                                  **404** |
| `map`（`limit=75, max_depth=2`） |                         75 URL / 16.5 s / 約 8 クレジット / 別ドメイン 0 |
| map が sitemap をカバーした割合  |                                                       **72 / 359 = 20%** |
| map のみ                         | **3** — `/python` `/java` `/dotnet`（いずれも **301** で別言語サイトへ） |

**map は sitemap のほぼ部分集合。** しかも `limit` を上げないと 359 には届かず、上げればクレジットは線形に増える。

2 サイトで同じ向きの結果が出たので、**「map が sitemap を超える」は起きない**と扱ってよい。
map を使う理由が残るのは次の 2 つだけ:

1. **sitemap が存在しない**（llms.txt も無い）サイト
2. **別ホストへの越境を知りたい**とき（`help.tavily.com` のケース）

なお sitemap のヒストグラム圧縮は playwright.dev でも効く（359 URL → 上位 12 行で `/docs/next` 147、`/docs/api` 73、`/mcp/tools` 18…）。

---

## 7. 経路別の総括表（05 の判断表の素材）

| 経路                                                     |                                   典型コスト | 強い対象                               | 効かない対象                             | LLM |
| -------------------------------------------------------- | -------------------------------------------: | -------------------------------------- | ---------------------------------------- | --: |
| シグナル 3 連射（`robots`→`sitemap`→`llms.txt`）         |               **空振り 15 B / 当たり 745 B** | 公開サイト全般。ページ数が多いほど効く | ローカル・社内・SPA                      |   0 |
| リンク収集（`a[href],iframe[src],frame[src]`、1 ページ） |                                **76〜331 B** | 小さいサイト、sitemap の無いサイト     | JS 遷移、URL を持たない状態              |   0 |
| 深さ 1 クロール（同セレクタ）                            |                   **178〜378 B / 4〜7 往復** | iframe 入れ子、2 階層のサイト          | `location.href` の先                     |   0 |
| Tavily `map`                                             | **8〜15 クレジット / 1〜17 s / 死 URL 混入** | sitemap が無いサイト、別ホストへの越境 | sitemap があるサイト（部分集合になる）   |   0 |
| `pwq explore` + `ask`                                    |                           **4,800〜6,200 B** | 1 枚のページの中身・操作方法           | サイト全体の一覧（そもそも見えていない） |   3 |

**ベースラインは「サイト全体を知る」用途では一番高くて一番当たらない。**
ただし `/tables/` のように**1 枚しか無いサイトでは唯一の手段**でもある（§2）。置き換えではなく**前段**。

---

## 8. 未測定・測らなかったもの（理由つき）

| 項目                                              | 理由                                                                                                                                                                                                     |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 外部サイトへの多段クロール                        | R3（1 サイト 10 リクエスト）を超える。プランどおり測らない                                                                                                                                               |
| Firecrawl `/v2/map` との突き合わせ                | **鍵を頼む前提が崩れた。** 04 のプランは「Tavily map が sitemap を超えたら別実装で癖か本質かを切り分ける」としていたが、**超えなかった**（2 サイトとも部分集合）。切り分ける差分が存在しないので鍵は不要 |
| 認証壁のあるサイト                                | 偵察は認証前に効くことに価値がある。対象外（プランどおり）                                                                                                                                               |
| `/slow/` の巨大 DOM                               | `context-saving-explore.md` に実測済み。測り直さない（プランどおり）                                                                                                                                     |
| `tools/browser/test-sites/` に対する Tavily `map` | `localhost` は外部サービスから到達不能（03 で判明済み）                                                                                                                                                  |
| sitemap index（子 sitemap を持つサイト）          | 今回の 2 サイトはどちらも単一 sitemap だった。**サンプルが無く未測定**。R3 の「子は先頭 3 つまで」は未検証のまま 05 へ送る                                                                               |

---

## 9. 05 への引継ぎ

1. **判断表の第 1 行は「`robots.txt` → `sitemap.xml` を 2 GET」で固定してよい。** 空振り 15 B、当たれば 745 B。
   これを飛ばす理由が無い
2. **リンク収集のセレクタは `a[href],iframe[src],frame[src]` を既定にする。** `a[href]` だけだと `/frames/` で半分落ちる（101 B の差で 40%→80%）
3. **「URL に現れない状態を持つページ」の判定を偵察の出力に入れる。** `/tables/` 型。
   判定材料は `#` のみのリンク・ページ送りボタン。**ここで偵察を打ち切って `pwq` に渡す**のが正しい分岐
4. **`location.href` / フォーム送信の先はリンクグラフの外。** 網羅率 100% を目標にしない。
   `/catalog/` の 80% が**リンクグラフの上限**であることを判断表に明記する
5. **Tavily `map` は必須経路から外す。** 条件付きの退避路（sitemap 無し／別ホスト越境）に格下げ。
   `tav.md` の文言修正（03 の指摘）は「API には存在するが偵察では推奨しない」と書くのが実測に合う
6. **`llms-full.txt` は存在確認だけして開かない**を明文のルールにする（854 KB）
7. **取得した URL 集合は検証が要る。** map の 14 件中 5 件が 404、3 件がリダイレクト。
   R6 を「テキストは untrusted」から **「URL 集合も untrusted」** に拡張する
