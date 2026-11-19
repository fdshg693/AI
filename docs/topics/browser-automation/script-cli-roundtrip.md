---
type: Research Notes
title: "スクリプト ⇄ CLI 往復 調査メモ"
description: "Records measurements of moving browser work between playwright-cli interactive commands and run-code scripts (recording, replaying from the current page, init chunks, idempotent guards) that the script-cli-roundtrip reference is built on. Use when changing that workflow or pwdo's script recovery."
tags: [tools]
status: stable
step: Step1-4 完了（script-cli-roundtrip）
verified-on: 2026-09-15
verified-with: "@playwright/cli 0.1.19, Chrome (in-memory profile; Step1-2 headless / Step3 headed), Windows 11 Pro 26200, Node.js v26.5.0, Git Bash"
---

# スクリプト ⇄ CLI 往復 調査メモ

スクリプト ⇄ CLI 往復ワークフローの実測結果。手順としての結論は
`script-cli-roundtrip.md`（`using-playwright-cli` スキル） にまとめてある（このファイルはその根拠）。

Step1（スクリプト → CLI の引き継ぎ）と Step2（CLI → スクリプトの回収）の分。Step3 以降はこのファイルに追記する。
[scripted-automation.md](scripted-automation.md) の A-1 / A-4 を前提にしており、そこで確定済みの論点は再実測していない。

検証対象は TodoMVC デモ（`https://demo.playwright.dev/todomvc/`）。使い捨てセッション `-s=roundtrip`、
カレントはスクラッチパッドに置いた（`.playwright-cli/` をリポジトリ内に作らないため）。

## 決定事項（Step1）

| 論点                             | 決定                                                                                                                                                                                                                                              | 根拠      |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| 観点1 現在地の可視性             | **成立する。** `run-code` は成功時に自分の出力へ `### Page`（URL / Title）を出し、次の CLI コマンドも新しい URL を出す。古い状態は残らない                                                                                                        | D-1       |
| 観点2 ref の失効                 | **誤爆しない。失効は必ず明示エラー** `Error: Ref <r> not found in the current page snapshot. Try capturing new snapshot.` で落ちる。黙って別要素を掴む挙動は再現できなかった                                                                      | D-2       |
| 観点2' ref の寿命                | ref は**位置ではなく DOM 要素の同一性**に紐づく。スクリプトが要素を追加・削除してリストがズレても、生き残った要素は同じ ref のまま正しく解決される。**ナビゲーションすると全部失効**し、ref の名前空間自体が変わる（`e3` → `f2e12`）              | D-2 / D-3 |
| 観点3 引き継ぎ手順               | **`run-code` の後は full `snapshot` を撮り直すことを手順として固定する。** 技術的には必須でない場合もあるが、「どの ref が生き残ったか」はエージェント側から判別できず、スクリプトが**新しく作った要素の ref は snapshot なしでは一切得られない** | D-2 / D-3 |
| 観点4 snapshot ファイル          | **`run-code` はナビゲーションを含んでも `.playwright-cli/page-*.yml` を書かない**（3 回反復して 0 で安定）。スクリプト実行後に読める成果物ファイルは残らない                                                                                      | D-4       |
| 観点5 逆方向（CLI → スクリプト） | **成立する。** CLI の `fill` / `press` / `check`（ref 指定含む）の結果を、後続の `run-code` がそのまま読む                                                                                                                                        | D-5       |
| 観点6 失敗の見え方               | **途中まで の副作用は残り、セッションは `status: open` のまま、CLI から続きを触れる。** ただし失敗時の出力は `### Error` だけで **`### Page` が出ない**（現在地が分からない）                                                                     | D-6       |
| 失敗の判定                       | **`run-code` 内で catch しない例外は exit code 1**。`scripted-automation-notes.md` A-2 の exit 0 は「スクリプト内で catch している」ケース。両者を混同しない                                                                                      | D-6       |

→ **Step3（往復リハーサル）の前提は崩れていない。両方向とも成立する。**

## D. 実測

### D-1. `run-code` は自分で現在地を報告する

`page.goto('.../#/active')` + todo を 2 件追加するスクリプトの出力:

````
### Result
{"url":"https://demo.playwright.dev/todomvc/#/active","title":"React • TodoMVC"}
### Ran Playwright code
```js
await (async page => { ... })(page);
````

### Page

- Page URL: https://demo.playwright.dev/todomvc/#/active
- Page Title: React • TodoMVC

````

- 成功時は `### Result` / `### Ran Playwright code` / `### Page` の 3 節。**`### Snapshot` 節は出ない**（＝ ref は得られない）
- `### Ran Playwright code` にスクリプト本文がそのまま echo される（Step2 で使える可能性がある。ここでは記録だけ）
- 後続の CLI コマンドの page status も同じ新 URL を出す。古い URL が残ることはなかった

### D-2. ref は要素の同一性に紐づく。失効は明示エラー

todo 5 件（`from-script-1` / `from-script-2` / `alpha` / `beta` / `gamma`）の状態で full snapshot を撮り、
その後 `run-code` で**先頭の `from-script-1` を削除**してリストを 1 つ上へズラした。

| 使った ref | 撮影時の中身 | 削除後の `eval` 結果 |
|---|---|---|
| `f2e16` | `from-script-1`（削除された要素） | **`Error: Ref f2e16 not found in the current page snapshot.`** |
| `f2e40` | `alpha`（1 つ上へズレた） | `"alpha"` — **正しい要素のまま** |
| `f2e20` | `from-script-2`（先頭へ繰り上がった） | `"from-script-2"` — **正しい要素のまま** |

→ **位置がズレても誤爆しない。**「スクリプト実行後は必ず snapshot を撮り直す」を強制する根拠は
「誤爆するから」ではなく「**新規要素の ref が取れないから**」である（下の D-3 も参照）。

`eval` の `### Ran Playwright code` は ref を意味的ロケータに解決して見せる:

```js
await page.getByText('alpha').evaluate('el => el.textContent');
await page.getByText('from-script-').evaluate('el => el.textContent');   // ← 前方一致で切り詰められている
````

2 つ目は `from-script-1` / `from-script-2` の共通接頭辞になっており、**生成ロケータがそのままでは一意でない**。
Step2（CLI 操作のスクリプトへの回収）で必ず問題になるので、ここに記録しておく。

### D-3. ナビゲーションは ref を全部失効させる

full snapshot（`e3` = `real TodoMVC app.` リンク）を撮ってから `run-code` で `page.goto('https://example.com/')`:

```
$ playwright-cli -s=roundtrip eval "el => el.tagName + '|' + el.textContent" e3   # 遷移前
### Result
"A|real TodoMVC app."

$ playwright-cli -s=roundtrip eval "el => el.tagName + '|' + el.textContent" e3   # run-code で遷移した後
### Error
Error: Ref e3 not found in the current page snapshot. Try capturing new snapshot.
```

さらに、遷移後の snapshot では ref の名前空間自体が変わっていた（`e12` ではなく **`f2e12`**）。
→ 遷移を跨いだ ref の番号衝突は構造的に起きない。

**スクリプトが新しく作った要素の ref は、snapshot を撮るまで存在しない。**
todo を 3 件足した後に撮った snapshot で `f2e37` / `f2e41` / `f2e45` が初めて現れた。
これが「`run-code` の後は snapshot を撮り直す」を手順にする実際の理由。

### D-4. どのコマンドが `.playwright-cli/page-*.yml` を書くか

`page-*.yml` の個数を前後で数えた実測（`fill` / `press` / `run-code` は 3 回反復して同じ結果）:

| コマンド                                                       | ファイルが増えるか |
| -------------------------------------------------------------- | ------------------ |
| `open` / `goto` / `reload` / `click` / `press` / `hover`       | **増える**         |
| `snapshot` / `find` / `eval` / `screenshot` / `fill` / `check` | 増えない           |
| **`run-code`（ナビゲーションを含む場合も）**                   | **増えない**       |

- **観点4 の答えは「増えない」。** `scripted-automation-notes.md`（読むだけの系は増えない）はスクリプト内の
  ページ遷移についても当てはまる
- 一方で `fill` / `check` が増えない・`hover` が増える点は、既存メモの「ページを動かす系は増える」という
  説明では割り切れない。**決定に影響しないのでここでは分類を追わない**（`run-code` の行だけが往復の前提に効く）
- 観点1（stdout の page status）とは別物。`run-code` は page status を**出す**がファイルは**書かない**

### D-5. CLI → スクリプトの引き継ぎ（逆方向の下準備）

CLI で 3 手操作（`fill` でテキスト投入 → `press Enter` → ref 指定の `check f2e39` で `alpha` を完了）した後、
`run-code` で状態を読む:

```
### Result
{"items":["from-script-2","alpha","beta","gamma","typed-by-cli"],"completed":["alpha"],"left":"4 items left"}
```

- CLI の操作結果（追加した `typed-by-cli`、完了にした `alpha`）が**すべてスクリプトから見える**
- ここで使った `f2e39` は、間に `run-code` を何度も挟んだ**古い snapshot の ref**だが、そのまま通った（D-2 と整合）

### D-6. スクリプトが途中で落ちた場合

前半で todo を 1 件足し、存在しないセレクタを `click({timeout:2000})` して落ちるスクリプト:

```
### Error
TimeoutError: locator.click: Timeout 2000ms exceeded.
Call log:
  - waiting for locator('#definitely-not-here')

exit code: 1
```

- **エラー文にページ本文は載らない**（call log にセレクタ文字列が出るだけ）。既存の「認証画面を読まない」ルールと両立する
- **`### Page` 節が出ない。** 成功時と違い、落ちた後の現在地は出力から分からない
- ブラウザは `status: open` のまま。**前半の副作用（`before-crash` の追加）は残る**。後半（`after-crash`）は実行されない
- 直後の `run-code` も `find` も通る。**CLI から続きを触れる**

落ちた後に現在地だけを安く確かめる手段（ページ本文を会話に入れない）:

```bash
playwright-cli --raw -s=<site> eval "() => location.href"
# → "https://demo.playwright.dev/todomvc/#/active"
```

## 落とし穴

- **`snapshot <ref>` は ref テーブルをその部分木だけに置き換える。** 直後は部分木の外側の ref が
  全部 `not found` になる。実測: full snapshot 後に `snapshot e8`（textbox 単体）を撮ると、
  `e13` も `e22` も `not found`。**`run-code` のせいだと誤診しかけた実際の落とし穴。**
  スコープ付き snapshot の後に別の場所を触るなら、full `snapshot` を撮り直す
- **`playwright-cli open` は `--persistent` / `--profile` なしだと、セッションを `close` するまで戻ってこない。**
  今回 120 秒でバックグラウンドへ回された。バックグラウンドで起動し、**初期 ref は自分で `snapshot` を撃って取る**
  （`open` の出力＝初期 snapshot へのリンクは終了時まで読めない）
- **`run-code` の失敗と「スクリプト内で catch したタイムアウト」は exit code が違う**（1 / 0）。
  `scripted-automation-notes.md` A-2 の「exit 0」を一般則として読まない
- **`run-code` は snapshot ファイルを残さない。** スクリプトの後に状態を残したいなら
  `snapshot --filename=...` を明示的に撃つ
- ref を意味的ロケータへ逆変換した結果は**一意とは限らない**（`getByText('from-script-')`）。Step2 の主要リスク

## このステップで確かめていないこと（Step3 が前提にしないこと）

Step1 の測定はすべて **headless・in-memory プロファイル**（`open` に `--persistent` / `--profile` を付けない形）で行った。
以下は未検証なので、Step3 で headed / 永続プロファイルを使うなら**そこで改めて見る**:

- headed + 永続プロファイルでも ref の寿命・snapshot ファイルの挙動が同じか（同じだと想定しているが未測定）
- 複数タブ（`tab-new` / `tab-select`）を跨いだときの ref の扱い。**今回は 1 タブのみ**
- SPA でない普通のページ遷移、`go-back` / `go-forward` 後の ref。**今回のナビゲーションは `goto` だけ**
- D-4 の分類が割り切れない件（`fill` / `check` は増えず `hover` は増える）。**`run-code` の行だけ確定させて追っていない**
- 長いチャンク（数十手）を 1 回の `run-code` に入れた場合の挙動。今回のスクリプトは最大 6 手

## Step1 から Step2 / Step3 への申し送り

- 往復の最小手順は次で固定できる見込み（Step3 で検証する）:

  ```bash
  playwright-cli -s=<site> run-code --filename=./chunk-N.js   # 少し進める（### Page で現在地が出る）
  playwright-cli -s=<site> snapshot                            # ★必須。新しい要素の ref はここで初めて得られる
  playwright-cli -s=<site> click <ref>                         # 手で探索する
  # → 効いた操作を chunk-N+1.js に書き写す
  ```

- `### Ran Playwright code` 節が CLI 操作・`run-code` の両方に出る。Step2 の「生成コード節の取り出し」は
  この節を拾えばよい。ただし **ref → ロケータの変換が一意でない**問題（D-2）をどう塞ぐかが論点
- Step3 の冪等性検証では、**落ちたスクリプトの前半の副作用が残る**（D-6）ことが効く。
  チャンクを再実行できるようにするなら、追加系の操作は「既にあるならスキップ」を書く必要がある

## Step1 から Step4（リファレンス執筆）への申し送り

Step1 の実測から、リファレンスに**手順として書き下すべきもの**が 3 つ確定している。Step4 で拾い漏らさないこと:

1. **`run-code` の直後に full `snapshot` を撃つ**を手順に含める。理由は「ref が誤爆するから」ではなく
   「**スクリプトが新しく作った要素の ref は snapshot を撮るまで存在しないから**」と書く。
   理由を取り違えると「ref が生きているなら省いてよい」と読まれて壊れる（D-2 / D-3）
2. **`run-code` が exit 1 で落ちたら、次に撃つのは `--raw eval "() => location.href"`**。
   失敗時の出力には `### Page` が無く現在地が分からないため（D-6）。
   ページ本文を会話に入れずに現在地だけ取れる唯一の安い手段なので、コード片ごと載せる
3. **スコープ付き `snapshot <ref>` を往復の途中で使わない**、使うなら直後に full `snapshot` を撮り直す、
   と禁止側に書く。ref テーブルを部分木に置き換えるという挙動は公式ドキュメントに記述が無く、
   エラーメッセージ（`Try capturing new snapshot.`）からも原因が分からない（落とし穴の節）

また、**`scripted-automation-notes.md` の A-2「exit 0」を一般則として引用しない**こと。
あれは「スクリプト内で catch している」前提の値で、catch しない例外は exit 1（D-6）。
Step4 で両メモを参照するリファレンスを書くなら、この違いを 1 行で明示する。

---

# Step2: CLI → スクリプトの回収

検証は Step1 と同じ構成（`@playwright/cli` 0.1.19、Chrome、in-memory プロファイル、headless、
TodoMVC デモ、使い捨てセッション `-s=rt2`、カレントはスクラッチパッド）。

## 決定事項（Step2）

| 論点                                | 決定                                                                                                                                                                                                                                                                                                         | 根拠      |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------- |
| **既定の回収経路**                  | **経路 B（`recording-start` / `recording-stop`）を既定にする。** 記録は**操作の出所を問わない** — CLI コマンド・`run-code` 内の locator 操作・座標指定の生入力の 3 種すべてを拾い、意味的ロケータへ正規化して出す                                                                                            | E-1       |
| 記録される操作の範囲                | **状態を変える操作だけ。** `snapshot` / `find` / `eval` は記録されない。ナビゲーションは CLI `goto` も `run-code` 内の `page.goto` も**両方記録される**                                                                                                                                                      | E-1 / E-2 |
| 経路 A（生成コード節）              | **補助に落とす。** `### Ran Playwright code` は stdout のテキストにしか出ず、**`--json` には入らない**（アクションの `--json` は `{}` を返す）。切り出すには stdout のフェンスを sed で削るしかない                                                                                                          | E-3       |
| 経路 C（手書き）                    | **使わない。** B が全経路を拾うので穴が無い。B が取りこぼした操作に気づいたら、記録し直す方が安い                                                                                                                                                                                                            | E-1       |
| 回収コードの機械抽出                | **`recording-stop --json` の `.result` から jq + sed で取り出せる。** アクションと違い recording-stop は回収物が `result` 文字列に入るため、**`--raw` を付けても消えない**                                                                                                                                   | E-3 / E-4 |
| **生成 TS → `run-code` 形への変換** | **無変換。** `async page => {` … `}` で包み、末尾に `return {...}` を足すだけで動く。`import` も `test()` も出てこない                                                                                                                                                                                       | E-5       |
| アサーション                        | **`expect` はサンドボックスに無い**（`ReferenceError: expect is not defined`）。かつ **CLI にアサーション系コマンドが無い**ので、記録にも生成コードにも `expect` は最初から現れない。代替形は `locator.waitFor({state})` / `count()` / `page.waitForURL()` / `throw new Error(...)` で、**全部そのまま動く** | E-6       |
| アサーション失敗の見え方            | `throw` は `### Error` + **exit code 1**。Step1 D-6 の「catch しない例外は exit 1」と同じ                                                                                                                                                                                                                    | E-6       |
| ref の混入                          | **記録・生成コードのどちらにも ref は出ない。** ただし**意味的なアンカーを持たないコンテナ要素の ref** からロケータを生成させると、兄弟のテキストを連結して切り詰めた壊れやすい `getByText(...)` になる（Step1 D-2 が記録した現象の正体）                                                                    | E-7       |
| `--raw` の使い分け                  | **アクションに `--raw` を付けると出力が空になる**（生成コードごと消える）。回収目的のコマンドには付けない。`eval` で値だけ欲しいとき・`recording-stop` の 2 つは付けてよい                                                                                                                                   | E-4       |

→ **往復の戻り側は成立する。Step3 の前提は崩れていない。**

## E. 実測

### E-1. 記録は操作の出所を問わない（分岐点の答え）

1 回の記録区間に 3 種類の操作を混ぜた。

| #   | 出所                         | 撃ったもの                                                               |
| --- | ---------------------------- | ------------------------------------------------------------------------ |
| (2) | CLI コマンド                 | `fill e8 "aaa-cli"` → `press Enter`                                      |
| (3) | `run-code` 内の locator 操作 | `getByPlaceholder(...).fill('bbb-runcode')` → `.press('Enter')`          |
| (1) | 生の入力（座標指定）         | `run-code` 内で `page.mouse.click(x, y)`（`aaa-cli` のチェックボックス） |

`recording-stop` の出力:

```js
await page
  .getByRole("textbox", { name: "What needs to be done?" })
  .fill("aaa-cli");
await page
  .getByRole("textbox", { name: "What needs to be done?" })
  .press("Enter");
await page
  .getByRole("textbox", { name: "What needs to be done?" })
  .fill("bbb-runcode");
await page
  .getByRole("textbox", { name: "What needs to be done?" })
  .press("Enter");
await page
  .getByRole("listitem")
  .filter({ hasText: "aaa-cli" })
  .getByLabel("Toggle Todo")
  .check();
```

- **3 種すべてが出た。**
- **座標クリックが `.getByLabel('Toggle Todo').check()` に正規化されている。** 座標は残らない
- 記録は**自分のコードを echo しない。** `getByPlaceholder(...)` と書いたのに
  `getByRole('textbox', { name: ... })` で出た。記録はページ側から独立にロケータを導出している

→ **これが Step2 の分岐点の答え。** 記録がユーザーの手操作専用でない以上、
**回収経路は B 一本でよく、経路 A を回収の主役にする必要がない。**

**（未検証）生身の人間のクリック。** headless では人間のクリックを発生させられないため、
(1) は `page.mouse.click(x, y)`（ロケータを介さない CDP 入力）を代理に使った。
**headed の窓でユーザーが実際にクリックした場合は未測定。**（代理が拾われた以上は拾われると想定しているが、根拠はこれだけ）

### E-2. 読み取り系は記録されない。ナビゲーションは両経路とも記録される

別の記録区間で `snapshot` / `find` / `eval` / CLI `goto` / `run-code` 内の `page.goto` を撃った結果:

```js
await page.goto("https://demo.playwright.dev/todomvc/#/active"); // ← CLI goto
await page.goto("https://demo.playwright.dev/todomvc/#/completed"); // ← run-code 内の page.goto
```

`snapshot` / `find` / `eval` は 1 行も出ない。**記録の粒度は「状態を変えたか」であって「どのコマンドか」ではない。**

**スクリプトが途中で落ちても、そこまでに成功した操作は記録に残る。** Step1 D-6 と同じ形のスクリプト
（2 手成功 → 存在しないセレクタで TimeoutError）を記録中に走らせると、記録には成功した 2 手だけが入った。
→ **記録の内容は「実際に起きたこと」と一致する**（残った副作用と一致するので、落ちた後の回収でも信用できる）。

### E-3. `--json` は生成コードを落とす。`recording-stop` だけは落とさない

```bash
$ playwright-cli --json -s=rt2 fill e8 "json-test"
{}
```

- **アクションの `--json` は空オブジェクト。** 生成コードのフィールドは無い。**fill 自体は成功している**
  （直後の `eval` で値が `"json-test"` になっている）。つまり `--json` は
  **「成功したが何も返さない」と「失敗した」が区別できない**
- **`run-code --json` は `{"result": "..."}` だけ**で、やはり生成コードは入らない
- **`recording-stop --json` は回収物が `result` に入る:**

````json
{
  "result": "Recording stopped. Recorded actions:\n\n```js\nawait page.getByRole(...)...;\n```",
  "snapshot": { "file": ".playwright-cli\\page-....yml" }
}
````

→ **経路 A は機械抽出できず、経路 B は機械抽出できる。** これも B を既定にする理由。

機械抽出のレシピ（実測で通したもの）:

````bash
playwright-cli --json -s=<site> recording-stop > rec.json
jq -r '.result' rec.json | sed -n '/```js/,/```/p' | sed '1d;$d' > recorded.txt
````

### E-4. `--raw` の効き方はコマンドで違う

| コマンド                         | `--raw` を付けると                                                        |
| -------------------------------- | ------------------------------------------------------------------------- |
| アクション（`fill` / `click` …） | **出力が完全に空になる**（生成コードごと消える）。成功も失敗も見えない    |
| `eval`                           | 値だけが出る（Step1 と同じ。使ってよい）                                  |
| **`recording-stop`**             | **記録されたコードは残る**（`### Result` の飾りが落ちるだけ）。付けてよい |

→ 「`--raw` は生成コードを落とす」は**アクションについては正しいが、`recording-stop` には当てはまらない。**
回収物が「生成コード節」ではなく「結果値」だから。

### E-5. 回収したコードは無変換で `run-code` に載る

E-1 と同じ手順で記録 → jq で抽出 → 機械的に包んだだけのファイル:

```js
async (page) => {
  await page
    .getByRole("textbox", { name: "What needs to be done?" })
    .fill("task-A");
  await page
    .getByRole("textbox", { name: "What needs to be done?" })
    .press("Enter");
  await page
    .getByRole("textbox", { name: "What needs to be done?" })
    .fill("task-B");
  await page
    .getByRole("textbox", { name: "What needs to be done?" })
    .press("Enter");
  await page
    .getByRole("listitem")
    .filter({ hasText: "task-A" })
    .getByLabel("Toggle Todo")
    .check();
  return {
    items: await page.getByTestId("todo-title").allTextContents(),
    left: await page.getByTestId("todo-count").textContent(),
  };
};
```

状態をリセットしてから実行 → `{"items":["task-A","task-B"],"left":"1 item left"}`。**記録時と同じ結果。**

- **書き換えは 1 行も要らなかった。** `import` / `test()` / `expect` は記録に現れないので、
  サンドボックスの制約（A-4）に最初から当たらない
- 包む処理はシェルで完結する:

  ```bash
  { echo "async page => {"; sed 's/^/  /' recorded.txt; echo "  return { /* 確認したい値 */ };"; echo "}"; } > chunk-N.js
  ```

**`press` の記録はフォーカス中の要素に束縛される。** CLI 自身の生成コードは
`await page.keyboard.press('Enter')`（周囲のフォーカスに依存）だが、記録側は
`await page.getByRole('textbox', ...).press('Enter')` と**要素に結び付けて**出す。
再実行の観点では記録側の形の方が安全。ただし**意図しない要素にフォーカスがあるまま `press` を撃つと、
その要素に束縛された行が記録に残る**（チェックボックスに束縛された `.press('Enter')` を実測した）。

### E-6. アサーションの代替形

`expect` はサンドボックスに無い（A-4 の再確認）:

```
### Error
ReferenceError: expect is not defined
```

そもそも **CLI にアサーション系のコマンドが無い**（`--help` の全コマンドを確認）。
よって**記録にも生成コードにも `expect` は現れず**、「生成 TS の `expect` をどう書き換えるか」という問題自体が起きない。
アサーションは回収物ではなく**こちらが足すもの**。以下は 1 ファイルにまとめて実行し、全部通ることを確認した:

| やりたいこと                     | `run-code` での書き方                                                |
| -------------------------------- | -------------------------------------------------------------------- |
| `expect(locator).toBeVisible()`  | `await locator.waitFor({ state: 'visible', timeout: 3000 })`         |
| `expect(locator).toHaveCount(n)` | `const n = await locator.count();` → 返り値に入れる／`if` で `throw` |
| `expect(page).toHaveURL(re)`     | `await page.waitForURL(re, { timeout: 3000 })`                       |
| 明示的な失敗                     | `throw new Error('expected 2 todos, got ' + n)`                      |

`throw` した場合:

```
### Error
Error: assertion failed: expected 99 todos, got 2
exit code: 1
```

→ **チャンクの自己検証は「返り値に観測値を入れる」＋「前提が崩れたら throw」の 2 段で書く。**
前者はエージェントが読む用、後者はチャンクを止める用。

### E-7. ref から生成されるロケータが壊れるのは「アンカーの無いコンテナ」のとき

Step1 D-2 の `getByText('from-script-')`（共通接頭辞に切り詰められた形）を再現した。
**原因は「テキストが似た項目が並んでいるから」ではない。**

似た項目を並べただけでは壊れない — 生成側が `exact` を付けて一意にしてくる:

| ref                        | 中身                                            | 生成されたロケータ                         | 解決数 |
| -------------------------- | ----------------------------------------------- | ------------------------------------------ | ------ |
| todo テキスト `dup-item-1` | 兄弟に `dup-item-2`                             | `getByText('dup-item-1')`                  | 1      |
| todo テキスト `shared`     | 兄弟に `shared-extra`（**部分一致してしまう**） | **`getByText('shared', { exact: true })`** | 1      |

壊れるのは**意味的なアンカー（role / label / テキスト）を持たない `generic` なコンテナ**の ref:

| ref                         | 生成されたロケータ                                                                             |
| --------------------------- | ---------------------------------------------------------------------------------------------- |
| ルートの `generic`          | `getByText('This is just a demo of TodoMVC for testing, not the real TodoMVC app. todosMark')` |
| その子の `generic`          | `getByText('This is just a demo of')`                                                          |
| `header` 相当               | `locator('header')`                                                                            |
| todo リストを含む `generic` | **`getByText('Mark all as completetask-')`** ← Step1 で見たのと同じ形                          |

最後のものは「toggle-all のラベル + **リストの中身の先頭**」を連結して切り詰めた文字列で、
**ページのデータをロケータに埋め込んでいる。** 壊れることを実測した:

```js
// localStorage をクリアして別の todo を 1 件入れた後
{ "markAll": 0 }   // ← さっきまで 1 件に解決していたロケータが 0 件になる
```

→ **回収してよいのは、操作対象＝インタラクティブな要素に対する生成コードだけ。**
コンテナ要素の ref に対して `eval` / `generate-locator` した結果のロケータは**スクリプトに持ち込まない。**
なお**記録（経路 B）にはこの問題が無い**：記録されるのは実際に操作した要素だけで、コンテナを操作することはない。
これも B を既定にする理由の 1 つ。

## 落とし穴（Step2）

- **記録の開始・停止は排他で、覗く手段が無い。** `recording-start` を二重に撃つと
  `Error: Recording is already in progress.`、開始せずに `recording-stop` を撃つと
  `Error: No recording in progress, use browser_start_recording to start one.`。
  **バッファを停止せずに確認するコマンドは存在しない**（`--help` の全コマンドを確認）。
  → **止め忘れると次の区間と混ざる。**「1 チャンク = 1 記録区間」を手順として固定し、
  探索を始める前に必ず `recording-start`、チャンクに落とした直後に必ず `recording-stop` を撃つ
- **エラーメッセージが CLI のコマンド名ではなく MCP のツール名（`browser_start_recording`）を指す。**
  そのままユーザーに見せると混乱するので、CLI 名（`recording-start`）に読み替えて伝える
- **`--json` や `--raw` でアクションを撃つと、失敗が見えなくなる。** `--json fill` は成功でも `{}`、
  `--raw fill` は成功でも空。実測中に `fill e8` が ref 失効で失敗しているのを
  `>/dev/null 2>&1` で握り潰し、後続が空振りした（Step1 D-3 の「`run-code` の後は snapshot を撮り直す」を
  守っていれば起きなかった）。**回収作業中のアクションは素の出力で撃つ**
- **記録は ref を一切残さないが、「記録していない操作」は当然残らない。** 記録開始前に撃った操作は
  チャンクから抜け落ちる。**`recording-start` はチャンクの最初の一手より前に撃つ**

## このステップで確かめていないこと

- **headed の窓でユーザーが実際に手でクリックした場合**が記録されるか（E-1 の代理は座標クリック）。
  Step3 を headed でやるなら、そこで 1 回だけ確認する
- 記録区間を**ナビゲーションや複数タブをまたがせた**場合の挙動。ナビゲーションは `goto` のみ実測、タブは 1 枚のみ
- 記録が**セッションの `close` をまたいで残るか**（残らないと想定。未測定）
- 長い記録区間（数十手）での重複・待機の挿入。**今回の最大は 5 手**
- `select` / `upload` / `drag` / `dialog-*` の記録形。**今回記録したのは `fill` / `press` / `check` / `goto` のみ**

## Step2 から Step3 への申し送り

- 往復の最小手順は次で固定できる（Step1 の見込みに記録の 2 コマンドが挟まる形）:

  ````bash
  playwright-cli -s=<site> run-code --filename=./chunk-N.js   # 少し進める
  playwright-cli -s=<site> snapshot                            # ★必須（Step1 D-3）
  playwright-cli -s=<site> recording-start                     # ★探索の一手目より前
  playwright-cli -s=<site> click <ref>                         # 手で探索する
  playwright-cli --json -s=<site> recording-stop > rec.json    # ★探索が終わったら必ず
  jq -r '.result' rec.json | sed -n '/```js/,/```/p' | sed '1d;$d' > recorded.txt
  { echo "async page => {"; sed 's/^/  /' recorded.txt; echo "  return { /* 観測値 */ };"; echo "}"; } > chunk-N+1.js
  ````

- **回収は無変換で通る**（E-5）ので、Step3 の争点は変換ではなく**チャンクの切り方と冪等性**に絞れる
- Step1 が挙げた「ロケータの一意性」リスクは、**記録経由なら発生しない**（E-7）。
  Step3 で `eval` / `generate-locator` の出力をスクリプトに写す運用を取らなければ、この論点は消える
- 記録は**成功した操作だけ**を持つ（E-2）ので、チャンクが途中で落ちたときの
  「どこまで進んだか」は記録からも取れる。Step3 の冪等性検証で使える

## Step2 から Step4（リファレンス執筆）への申し送り

1. **回収経路は `recording-*` 一本に決め打ちして書く。** 「3 つの経路があり…」と選択肢を並べない。
   経路 A は「recording を張り忘れた区間の救済」として 1 行だけ触れる（stdout から目で写す、と明記）
2. **「1 チャンク = 1 記録区間」を手順として書く。** 覗く手段が無く、止め忘れが混線として現れるため（落とし穴）。
   `recording-start` は「探索の一手目より前」、`recording-stop` は「チャンクに落とす直前」と位置で書く
3. **`--raw` / `--json` の使い分けを表で書く。** 「`--raw` は生成コードを落とす」だけだと
   `recording-stop` に誤適用される（E-4）。**アクションには付けない / `eval` と `recording-stop` には付けてよい**の形で書く
4. **アサーションは「書き換える」ではなく「足す」と書く。** 記録にも生成コードにも `expect` は現れない（E-6）。
   代替形の表（E-6）をそのまま載せる
5. **`eval` / `generate-locator` の出力をスクリプトに写すのは禁止側に書く。** コンテナ要素の ref からは
   ページのデータを埋め込んだロケータが出る（E-7）。**操作は記録から回収する、が唯一の道筋**

---

# Step3: 往復リハーサル

往復を実サイトで 2 周回したリハーサルの実測。
Step1 / Step2 と違い **headed + in-memory プロファイル**（`open --headed`、`--persistent` なし）で回した。
対象は同じ TodoMVC デモ、セッション `-s=rt3`、カレントはスクラッチパッド。

## 1 周目（読み取り主体・冪等なシナリオ）

シナリオ: 「TodoMVC に 3 件を投入し、All / Active / Completed の各フィルタで件数を読む」。

チャンクは `chunk0-init.js`（通し実行専用の初期化） / `chunk1.js`（投入） / `chunk2.js`（フィルタ巡回）の 3 本。

### F-1. 「育てる」の 3 条件はすべて満たされた

| 条件                                                 | 結果                                                                                         |
| ---------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| (a) 引き継ぎに snapshot 撮り直し以上の儀式が要らない | **満たす。** `run-code` → `snapshot` → CLI 操作 だけで次の探索に入れた                       |
| (b) 回収が写経にならない                             | **満たす。** `recording-stop --json` → jq + sed で 3 行が機械的に取れた。手で写した行は 0    |
| (c) 追記後の再実行が最初からやり直しにならない       | **満たす。** `chunk2.js` を単独で 2 回叩いて同じ結果。`chunk1.js` も冪等ガード付きで再実行可 |

→ **1 周目は成立。**

### F-2. 記録は正しい。壊れたのは「自分で書き足した集計ロケータ」

`chunk1.js` の返り値に件数を入れるつもりで `page.getByRole('listitem').count()` と書いたら **6** が返った。

```
{"chunk":1,"ok":true,"added":3,"total":6,...}   ← 投入したのは 3 件
```

snapshot を見ると TodoMVC のフッタ（All / Active / Completed）も `list > listitem` で、
**3 件の todo + 3 件のフィルタ = 6** だった。`getByTestId('todo-title')` なら 3。

- **記録から回収した行（`getByRole('listitem').filter({ hasText: ... })`）は正しかった。**
  壊れたのは記録に含まれない「集計」を自分で書いた部分
- → **観点 6 の「ロケータの回収ミス」は、実際には回収経路では起きず、回収できない部分（読み取り・集計）で起きる。**
  Step2 E-7 の結論（記録経由なら ref 混入もロケータ崩れも起きない）はここでも保たれている

### F-3. 記録には待機が入らない — 連続クリック後の即時読み取りは前のレンダリングを拾う

回収した 3 行をそのまま繋ぎ、各クリックの直後に `count()` を置いたら **1 手ずれた値**が返った。

```
Error: filter mismatch: {"active":3,"completed":3,"all":0}
                                     ^^^^^^^^^^^^^  ^^^^^^^  どちらも前の画面の値
```

- `await page.waitForURL(/#\/completed$/)` を挟んでも **直らない**。ハッシュは再レンダリングより先に変わる
- クリックとクリックの間に別の待ち（`waitForTimeout(300)` や DOM 読み）が挟まると**たまたま直る**。
  この「たまたま直る」性質が一番たちが悪い
- 直った形は**選択中フィルタの DOM を待つ**こと:

  ```js
  const tour = async (name) => {
    await page.getByRole("link", { name }).click();
    await page.locator(".filters .selected", { hasText: name }).waitFor(); // ← 手で足す一手
    return page.getByTestId("todo-title").count();
  };
  ```

→ **回収コードは「操作」しか持っていない。「その操作が効いたことの確認」は毎回手で足す**（Step2 E-6 の
「アサーションは足す」の実践形）。`count()` / `innerText()` には auto-wait が無いことが効いている。

### F-4. `--raw` はアクションの生成コードを消すが、記録は消さない

探索の 3 クリックは `--raw` を付けて撃った（出力は snapshot リンク 1 行だけになる）。
それでも `recording-stop` は 3 行すべてを返した。

→ **`--raw` と記録は独立。** Step2 E-4 の「アクションに `--raw` を付けると出力が空になる」は
**stdout の話であって、回収可能性の話ではない**。記録を張っているなら `--raw` で探索してよい（出力が短くなる分むしろ安い）。

### F-5. SPA のハッシュ遷移では ref が失効しない

`#/` → `#/active` → `#/completed` → `#/` と 3 回移動したが、
最初の full snapshot で得た `e38` / `e40` / `e36` は**最後まで使えた**。

→ Step1 D-3 の「ナビゲーションすると全部失効し名前空間が変わる（`e3` → `f2e12`）」は
**document を作り直す遷移の話**。ハッシュ遷移・SPA 内遷移は含まれない。
ただし**どちらが起きたかはエージェント側から判別できない**ので、手順としては Step1 D-3 の
「`run-code` の後は snapshot を撮り直す」を崩さない。

### F-6. 入口ガードは「前提不一致」と「本当の失敗」を返り値だけで切り分けられる（観点 6）

`chunk2.js` の冒頭に URL チェックと件数チェックを置き、意図的に外して撃った。

| 状況                               | 出力                                                                             | exit  |
| ---------------------------------- | -------------------------------------------------------------------------------- | ----- |
| `example.com` にいる               | `{"chunk":2,"ok":false,"reason":"entry-guard:url","url":"https://example.com/"}` | 0     |
| TodoMVC にいるが todo 0 件         | `{"chunk":2,"ok":false,"reason":"entry-guard:no-todos",...}`                     | 0     |
| 前提は合っているがアサーション失敗 | `### Error` のみ（`### Page` は出ない）                                          | **1** |

→ **前提不一致 = `ok:false` + `reason` + exit 0 / 本当の失敗 = `### Error` + exit 1**、と
**exit code だけで一次切り分けができる**。ガードを `throw` で書くとこの区別が消えるので、**ガードは return で書く**。

### F-7. 再実行の 2 モードは両方必要で、初期化は別ファイルに出す（観点 3）

- **続きだけ実行**: `chunk2.js` 単独で 2 回 → どちらも `{"active":3,"completed":0,"all":3}`。成立
- **最初から通し実行**: `chunk0-init.js` → `chunk1.js` → `chunk2.js` → `{"total":0}` → `{"added":3}` → 件数一致。成立

初期化（`goto` + `localStorage.clear()` + `reload()`）を `chunk1.js` に入れると、
続きだけ実行するときに毎回状態が消える。**初期化は必ず別ファイル**（`scripted-automation.md` 3-5 の
「認証壁の検知 + 待機を独立したファイルにする」と同じ理由）。

### F-8. 冪等性は「既にあるならスキップ」で作れる（観点 4）

`chunk1.js` の投入ループに `count() > 0` のスキップを入れた。

```
1 回目: {"added":3,"total":3}
2 回目: {"added":0,"total":3}    ← 増えない
```

→ 追加系の操作でも、**記録から回収した行を `if (await <同じロケータ>.count() === 0)` で包むだけ**で冪等になる。
ロケータは記録が既に意味的な形で持っているので、ガード用に別途書き起こす必要が無い。

### F-9. `open --headed` は即座に戻る

Step1 の落とし穴「`playwright-cli open` は `--persistent` / `--profile` なしだと `close` まで戻ってこない」は
**headed では再現しなかった**（exit 0 で即返り、`### Browser rt3 opened with pid 8320.` + 初期 snapshot まで出た）。
headless のときだけの挙動か、版差か。**headed で往復するなら `open` をバックグラウンドへ回す必要は無い。**

## 2 周目（状態を変えるシナリオ + 手操作区間）

シナリオ: 「3 件投入 → 2 件を完了にする → Clear completed で消す」。
`chunk3.js`（完了にする） / `chunk4.js`（Clear completed = **非冪等**）を足し、途中に**ユーザーの手操作区間**を挟んだ。

### G-1. ユーザーが手でやった操作も記録される（Step2 の未検証項目の答え）

headed の窓で、**エージェントが一切コマンドを撃たない区間**を作り、ユーザーに手で
「`by-hand` と入力して Enter → そのチェックボックスをクリック」をしてもらった。`recording-stop` の出力:

```js
await page.getByRole("textbox", { name: "What needs to be done?" }).click();
await page
  .getByRole("textbox", { name: "What needs to be done?" })
  .fill("by-hand");
await page
  .getByRole("textbox", { name: "What needs to be done?" })
  .press("Enter");
await page
  .getByRole("listitem")
  .filter({ hasText: "by-hand" })
  .getByLabel("Toggle Todo")
  .check();
```

- **人間の実操作がそのまま意味的ロケータで出た。** Step2 E-1 の座標クリックは代理として妥当だった
- **ただし人間の記録にはノイズが混じる。** 1 行目の `.click()` は入力欄へフォーカスするためのクリックで、
  エージェントが `fill` を撃ったときには出なかった行。**手操作区間の記録は、回収前に不要な `click` を落とす**
- → **手操作区間は「エージェントが操作しない」を守ったまま、成果だけスクリプトに回収できる。**
  往復ワークフローの中で、認証に限らず「人がやった方が早い区間」を丸ごと取り込める

### G-2. 非冪等な操作の再実行は「30 秒待ってから本当の失敗と同じ顔で落ちる」

回収したままの `chunk4-naive.js`（ガード無し）を、既に Clear 済みの状態で撃った:

```
TimeoutError: locator.click: Timeout 30000ms exceeded.
  - waiting for getByRole('button', { name: 'Clear completed' })
elapsed=33s  exit=1
```

- **これは「前提状態の不一致」なのに、F-6 の「本当の失敗」と見分けがつかない**（`### Error` + exit 1）。
  非冪等チャンクをガード無しで置くと、**F-6 で作った切り分けが壊れる**
- さらに 1 回あたり 30 秒。チャンクを並べて通し実行すると固定費として積み上がる

ガードを足した `chunk4.js` を同じ状態で撃つと:

```
{"chunk":4,"ok":true,"skipped":true,"reason":"nothing-completed","cleared":0}
elapsed=4s  exit=0
```

→ **非冪等チャンクのガードは「入口の現在地」ではなく「やることが残っているか」で書く。**
形は `const before = await <対象>.count(); if (before === 0) return { ok: true, skipped: true, reason: ... };`。
**`ok: false` ではなく `ok: true, skipped: true`** にするのが要点で、「やることが無い」は失敗ではない。

### G-3. 冪等化のパターンは 3 つに収まった

| 操作の型 | 例                      | 冪等化                                                                                             |
| -------- | ----------------------- | -------------------------------------------------------------------------------------------------- |
| 追加系   | todo の投入             | **既にあるならスキップ**。`if (await <記録のロケータ>.count() === 0)` で記録の行を包む（F-8）      |
| トグル系 | `check()` / `uncheck()` | **何もしなくてよい。** `check()` は既にチェック済みなら no-op。2 回撃って同じ結果（`completed:2`） |
| 破壊系   | Clear completed         | **「やることが残っているか」で先に return**（G-2）                                                 |

→ 3 つとも**記録から回収したロケータをそのまま使い回せる**。ガード用に別のロケータを書き起こす必要は無い。

### G-4. 通し実行は 2 回とも同じ結果（観点 3・4 の合格判定）

`chunk0-init` → `chunk1` → `chunk3` → `chunk4` を 2 回連続:

```
1 回目: {"total":0} / {"added":3,"total":3} / {"completed":2,"left":"1"} / {"cleared":2,"total":1}
2 回目: {"total":0} / {"added":3,"total":3} / {"completed":2,"left":"1"} / {"cleared":2,"total":1}
```

全チャンクの ref 混入チェック（`grep -nE "\b(f[0-9]+)?e[0-9]+\b" chunk*.js`）も clean。

## H. 観点 7 — 本当に一括スクリプト化より軽いのか

### H-1. 1 チャンクあたりの固定費は 5 コマンド

往復 1 チャンクの最小手順は次で、**探索の N 手を除いた 5 コマンドが固定費**:

```bash
playwright-cli -s=<site> snapshot                             # 1  ★必須（Step1 D-3）
playwright-cli -s=<site> recording-start                      # 2  ★探索の一手目より前
playwright-cli --raw -s=<site> <action> <ref>                 #    探索 N 手（--raw でよい = F-4）
playwright-cli --json -s=<site> recording-stop > rec.json     # 3
jq/sed で chunk-N.js に落とす                                  # 4
playwright-cli -s=<site> run-code --filename=./chunk-N.js     # 5  検証実行
```

実測: chunk2 = 3 手で 9 コマンド、chunk3 = 2 手で 8 コマンド、chunk4 = 1 手で 7 コマンド。

→ **チャンクが 2〜3 手しかないと固定費が支配する。** 目安は **1 チャンク 5 手以上**。
それ未満なら往復せず `run-code` に直接書いた方が安い。

### H-2. 手戻りは 1 周目 3 回 → 2 周目 1 回

| 周  | 手戻り | 中身                                                                  | 出所                            |
| --- | ------ | --------------------------------------------------------------------- | ------------------------------- |
| 1   | 1      | `getByRole('listitem').count()` が 6 を返した                         | **自分で書いた集計**（F-2）     |
| 1   | 2      | 連続クリック後の即時 `count()` が 1 手ずれた。`waitForURL` でも直らず | **自分で書いた読み取り**（F-3） |
| 2   | 1      | 非冪等チャンクが 30 秒待って落ちた                                    | **ガードの書き忘れ**（G-2）     |

- **手戻り 3 回はすべて「記録に含まれない部分」で起きた。回収した行が原因の手戻りは 0。**
  Step2 E-7 / F-2 の結論がコスト面でも裏付けられた
- 2 周目の 1 回は**既知パターン（G-3 の破壊系）の適用漏れ**であって、新しい発見ではない。
  → **手順として書けている**（2 周目を回した目的は達成）

### H-3. 判断: 往復が得なのは「切り分けコスト」の方

往復のコマンド数は一括スクリプト化より**多い**。得になるのは次の 1 点に尽きる:

> **手戻りの原因が、チャンク 1 つ分の範囲に閉じる。**

一括スクリプト化では、F-2 / F-3 のような「記録に含まれない部分の誤り」が全チャンク分まとめて
1 回の `### Error` として出る。しかも F-3 は**待ちが挟まるとたまたま直る**ので、まとめて書くと再現性の無い失敗になる。

| 状況                                                    | 推す形                                                                                                |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| ロケータが事前に分かっていて、手順が 5 手未満           | **往復しない。** `run-code` に直接書く                                                                |
| 初見のサイト / 手順が長い（10 手以上）                  | **往復する。** 5 手前後で切る                                                                         |
| 人がやった方が早い区間がある（認証・CAPTCHA・目視判断） | **往復する。** その区間を手操作区間にして記録で回収（G-1）                                            |
| 読み取り・集計・アサーションが多い                      | **往復する。ただし回収だけでは足りない**（F-3）。チャンクごとに「効いたことの確認」を足す手間を見込む |

## Step3 の結論

**往復ワークフローは成立する。** 03 が挙げた 3 条件はすべて満たされた（F-1）。不成立ではない。

ただし Step4 で書くリファレンスは、**「回収すれば動く」と書いてはいけない**。実測された手戻りは
100% が「記録に含まれない部分」だったので、リファレンスの重心は回収手順ではなく
**回収した行に何を足すか**（待機・確認・ガード）に置く。

## このステップで確かめていないこと

- **複数タブ**をまたぐ往復。今回も 1 タブのみ（Step1 / Step2 と同じ穴が残っている）
- **`--persistent` / `--profile` 付き**の往復。今回は headed だが in-memory
- 非 SPA（document を作り直す）サイトでの往復。F-5 の ref 失効の切り分けは TodoMVC のハッシュ遷移でしか見ていない
- 10 手を超える長いチャンク。今回の最大は 3 手（H-1 の「5 手以上が得」は**固定費からの逆算であって実測ではない**）
- 手操作区間が**長時間**（数分）に及んだ場合に記録が保つか。今回は十数秒

## Step3 から Step4（リファレンス執筆）への申し送り

1. **手順の骨は H-1 の 5 コマンド。** そのまま載せる。`--raw` は探索アクションに付けてよい（F-4）
2. **「回収した行に足すもの」を独立した節にする。** ①効いたことの確認（F-3）②冪等ガード（G-3 の 3 パターン表）
   ③入口ガード（F-6）。この 3 つが手戻りの全量だった（H-2）
3. **ガードは `throw` ではなく `return` で書く**と明記（F-6）。`ok:false`+`reason` / `ok:true,skipped:true` の
   2 形を使い分ける（G-2）
4. **初期化は別ファイル**（F-7）。`chunk0-init.js` の形をそのまま例として載せる
5. **手操作区間を正式な構成要素として書く**（G-1）。認証の話ではない。「人がやった方が早い区間」一般。
   ノイズの `click` を落とす注意も 1 行
6. **往復しない条件を先に書く**（H-3 の表）。手順より前に置く。5 手未満なら往復しない
7. **`waitForURL` では足りない**ケース（F-3）を落とし穴として必ず書く。「たまたま直る」ので気づけない

## 付録: リハーサルで使ったチャンク（最終形）

スクラッチパッドは消えるので、Step4 が例として使えるよう全文を残す。

### `chunk0-init.js`

```js
async (page) => {
  // 通し実行専用の初期化。現在地に関わらず既知の状態へ戻す
  await page.goto("https://demo.playwright.dev/todomvc/");
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  return {
    chunk: 0,
    ok: true,
    total: await page.getByTestId("todo-title").count(),
    url: page.url(),
  };
};
```

### `chunk1.js`

```js
async (page) => {
  // --- 入口ガード: 想定の現在地にいるか ---
  if (!page.url().startsWith("https://demo.playwright.dev/todomvc/"))
    return { chunk: 1, ok: false, reason: "entry-guard", url: page.url() };

  // --- 本体: デモ用の 3 件を投入する（既にあるならスキップ = 冪等ガード） ---
  const SEED = ["read-alpha", "read-beta", "read-gamma"];
  const input = page.getByRole("textbox", { name: "What needs to be done?" });
  let added = 0;
  for (const t of SEED) {
    if ((await page.getByRole("listitem").filter({ hasText: t }).count()) > 0)
      continue;
    await input.fill(t);
    await input.press("Enter");
    added++;
  }

  return {
    chunk: 1,
    ok: true,
    added,
    total: await page.getByTestId("todo-title").count(),
    url: page.url(),
  };
};
```

### `chunk2.js`

```js
async (page) => {
  // --- 入口ガード: chunk1 の終了状態にいるか ---
  if (!page.url().startsWith("https://demo.playwright.dev/todomvc/"))
    return { chunk: 2, ok: false, reason: "entry-guard:url", url: page.url() };
  if ((await page.getByTestId("todo-title").count()) === 0)
    return {
      chunk: 2,
      ok: false,
      reason: "entry-guard:no-todos",
      url: page.url(),
    };

  // --- 本体: 記録から回収した 3 行 + 「安定を待つ」一手を手で足す ---
  // 記録には待機が入らない。クリックを連続で撃つと count() が前のレンダリングを読む（実測）。
  // URL は先に変わるので waitForURL では足りない。選択中フィルタの DOM を待つ
  const tour = async (name) => {
    await page.getByRole("link", { name }).click();
    await page.locator(".filters .selected", { hasText: name }).waitFor();
    return page.getByTestId("todo-title").count();
  };
  const counts = {
    active: await tour("Active"),
    completed: await tour("Completed"),
    all: await tour("All"),
  };

  // --- アサーションは expect ではなく throw で足す（Step2 E-6） ---
  if (counts.active + counts.completed !== counts.all)
    throw new Error(`filter mismatch: ${JSON.stringify(counts)}`);

  return { chunk: 2, ok: true, counts, url: page.url() };
};
```

### `chunk3.js`

```js
async (page) => {
  // --- 入口ガード ---
  if (!page.url().startsWith("https://demo.playwright.dev/todomvc/"))
    return { chunk: 3, ok: false, reason: "entry-guard:url", url: page.url() };
  if ((await page.getByTestId("todo-title").count()) < 2)
    return {
      chunk: 3,
      ok: false,
      reason: "entry-guard:need-2-todos",
      url: page.url(),
    };

  // --- 本体: 記録から回収（無変換） ---
  await page
    .getByRole("listitem")
    .filter({ hasText: "read-alpha" })
    .getByLabel("Toggle Todo")
    .check();
  await page
    .getByRole("listitem")
    .filter({ hasText: "read-beta" })
    .getByLabel("Toggle Todo")
    .check();

  // --- 効いたことの確認を手で足す（F-3） ---
  await page.locator(".todo-list li.completed").nth(1).waitFor();
  const completed = await page.locator(".todo-list li.completed").count();
  if (completed < 2) throw new Error(`expected 2 completed, got ${completed}`);

  return {
    chunk: 3,
    ok: true,
    completed,
    left: await page.locator(".todo-count strong").innerText(),
  };
};
```

### `chunk4.js`

```js
async (page) => {
  // --- 入口ガード ---
  if (!page.url().startsWith("https://demo.playwright.dev/todomvc/"))
    return { chunk: 4, ok: false, reason: "entry-guard:url", url: page.url() };

  // --- 冪等ガード: 非冪等な操作は「やることが残っているか」を先に見る ---
  const before = await page.locator(".todo-list li.completed").count();
  if (before === 0)
    return {
      chunk: 4,
      ok: true,
      skipped: true,
      reason: "nothing-completed",
      cleared: 0,
    };

  // --- 本体: 記録から回収（無変換） ---
  await page.getByRole("button", { name: "Clear completed" }).click();

  // --- 効いたことの確認を手で足す（F-3） ---
  await page
    .getByRole("button", { name: "Clear completed" })
    .waitFor({ state: "detached" });
  const after = await page.locator(".todo-list li.completed").count();
  if (after !== 0) throw new Error(`clear failed: ${after} completed remain`);

  return {
    chunk: 4,
    ok: true,
    skipped: false,
    cleared: before,
    total: await page.getByTestId("todo-title").count(),
  };
};
```
