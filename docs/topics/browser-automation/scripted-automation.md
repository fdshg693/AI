---
type: Research Notes
title: "ブラウザ作業のスクリプト化 調査メモ"
description: "Records measurements of scripting authenticated browser work (storage state, wait-for-user with timeout, resume after login) behind the sharing-browser-with-user scripted-automation reference. Use when changing how scripts wait for the user or reuse a logged-in profile."
tags: [tools]
status: stable
step: Step1 (browser-automation-scripting)
verified-on: 2026-09-15
verified-with: "@playwright/cli 0.1.19, Google Chrome (実チャネル), Windows 11 Pro 26200, Node.js v26.5.0, pwsh 7.6.6 / Windows PowerShell 5.1"
---

# ブラウザ作業のスクリプト化 調査メモ

browser-automation-scripting プラン Step1（完了プラン。このリポジトリには持ち込んでいない） の実測結果。
Step2（`references/scripted-automation.md` の執筆）はこのファイルの「決定事項」だけを前提にしてよい。

[browser-handoff.md](browser-handoff.md) は handoff スキル Step1 時点の凍結記録。こちらとは混ぜない
（ただし後述の「既存メモとの差分」節で 1 点だけ訂正している）。

## 決定事項

| 論点                               | 決定                                                                                                                                                        | 根拠（下の実測節）                                                                                                                                                             |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 実行モデル                         | **`playwright-cli -s=<site> run-code --filename=<file>` を既定**。独立した Node / `@playwright/test` スクリプトは採らない                                   | `run-code` は既存セッションの**同じページ・同じログイン状態**でそのまま動く。一方、独立スクリプトはこのマシンに `playwright` モジュールが無く**追加インストールが必要**（A-3） |
| `-s` の指定                        | **必須**。省略すると `default` セッションを見に行き `The browser 'default' is not open` で失敗する（勝手に既存セッションへフォールバックしない）            | A-1                                                                                                                                                                            |
| 長時間待機                         | **スクリプト内で待てる。CLI 側のコマンドタイムアウトは無い**（65s / 300s / 600s いずれも完走）。待ち時間は Playwright の `timeout` オプションだけが支配する | A-2                                                                                                                                                                            |
| 手動ログイン待ちの既定タイムアウト | **10 分（600000ms）**。MFA・SSO の画面遷移を含めて現実的な上限                                                                                              | A-2                                                                                                                                                                            |
| 認証壁の検知                       | **`page.url()` の正規表現判定**（必要なら `page.evaluate(() => location.host)`）。ページ本文は読まない・返さない                                            | B-1                                                                                                                                                                            |
| ログイン完了の検知                 | **`page.waitForURL(<ログイン後にだけ成立する述語>)`**。タイムアウトはスクリプト内で `catch` し、`{ loggedIn: false, timedOut: true }` を返す                | B-2                                                                                                                                                                            |
| タイムアウト時の後始末             | **何もしない（窓もセッションも閉じない）**。`catch` して戻れば `status: open` のまま残る                                                                    | B-2                                                                                                                                                                            |
| ユーザーへの通知                   | **`page.bringToFront()`（スクリプト内）＋ Windows トースト（エージェントのシェルから別プロセスで）** の 2 本立て                                            | C-1 / C-2                                                                                                                                                                      |
| 通知の実行主体                     | **必ずエージェント側のシェルから撃つ。スクリプト内からは撃てない**                                                                                          | run-code サンドボックスに `process` / `require` が無い（A-4）                                                                                                                  |
| storageState                       | **使わない**。使う場合も**保存先を明示し、リポジトリ外に置く**                                                                                              | 引数なし `state-save` は**カレントの `.playwright-cli/` に書く**（A-5）                                                                                                        |

## A. スクリプトの実行モデル

### A-1. `run-code` は既存セッションをそのまま引き継ぐ

`open --profile=...` で開いた headed セッションに対し、別プロセスの `run-code` が同じページで動く。

```bash
playwright-cli -s=probe run-code --filename=./write.js   # localStorage に書く
playwright-cli -s=probe run-code --filename=./read.js    # → {"marker":"set-by-run-code"} 別呼び出しでも読める
```

- `-s=<site>` を**省略すると失敗する**: `The browser 'default' is not open, please run open first`
- `page` は **`open` が開いた既存のタブ**。新しいコンテキストは作られないので、ログイン状態・Cookie・localStorage はすべてそのまま

### A-2. 長時間待機は可能。CLI 側のタイムアウトは無い

| 待機                                      | 結果                                                                              |
| ----------------------------------------- | --------------------------------------------------------------------------------- |
| `page.waitForTimeout(65000)`              | `{"waitedMs":65012}` exit 0                                                       |
| `page.waitForURL(..., {timeout: 300000})` | 300007ms 後に `TimeoutError2: page.waitForURL: Timeout 300000ms exceeded.` exit 0 |
| `page.waitForURL(..., {timeout: 600000})` | 600006ms 後に `Timeout 600000ms exceeded.` exit 0。**10 分の待機がそのまま通る**  |

→ **「認証壁に当たったらタイムアウト付きでユーザーの手動ログインを待つ」はスクリプト内で実装できる。**
エージェント側のポーリングループは不要。

**待機中にユーザーが窓を閉じた場合**（実測。1 回目の 10 分テストはユーザーが手で Chrome を閉じたため中断した）:

```
{"ok":false,"waitedMs":475155,"first":"page.waitForURL: Target page, context or browser has been closed"}
```

- タイムアウトとは**別のメッセージ**で返る。`catch` の中で
  `/has been closed/` を見れば「ユーザーが窓を閉じた」と「時間切れ」を区別できる
- セッションは消える（`playwright-cli list` が `(no browsers)`）。この場合だけは再 `open` が必要
- → Step2 の `wait-for-login.js` は `{ loggedIn:false, timedOut:true }` と
  `{ loggedIn:false, windowClosed:true }` を区別して返す

注意: **待機中も同じセッションに別コマンドを発行できてしまう**（実測: 300s の `run-code` 実行中に
`find` が 2 秒で成功し、`list` も通る）。CLI は待機中のセッションをロックしない。
→ 「スクリプトが待っている間、エージェントは `snapshot` / `find` を撃たない」は**仕組みで守られない。文章で禁止するしかない。**

### A-3. 独立スクリプトはこのマシンでは動かない（＝採らない理由）

- `require('playwright')` — **解決できない**（グローバルには `@playwright/cli` しか無く、`playwright` / `playwright-core` は同梱の内部依存として畳まれている）
- `require('./packages/playwright')` — **`Cannot find module 'playwright-core'`**（このリポジトリは `node_modules` を持たない）

→ 独立した `@playwright/test` スクリプトを書くには `npm i playwright` 相当の追加インストールが要る。
Step1 の方針（追加インストールをしない）と、既存の「1 プロファイル = 1 インスタンス」制約
（[browser-handoff.md](browser-handoff.md)）の両方から、**`run-code` 一本でよい**。

**「1 プロファイル = 1 インスタンス」は 0.1.19 でも健在。0.1.19 での挙動を 1 点追記する:**
同じ `--profile` を指す 2 つ目のセッションを `open` すると、

```
Error: Daemon pid=27140: Daemon process exited with code 1
Error: Browser is already in use for <dir>, use --isolated to run multiple instances of the same browser
```

**落ちるのは新しく起動した側の daemon だけで、既に開いているセッションは無傷**（`list` で `status: open` のまま）。
シェルの exit code も 0 で返る（stderr にだけ出る）ので、**スクリプトから起動する場合は exit code で失敗を判定できない**。

### A-4. `run-code` のサンドボックスは非常に狭い

実測した global の有無:

| あり                                                    | 無し                                                                                        |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `console`(object) / `JSON` / `Date`（標準 JS 組み込み） | `URL` / `process` / `require` / `fetch` / `setTimeout` / `Buffer` / `expect` / `playwright` |

帰結（Step2 でそのまま制約として書く）:

- **URL のパースに `new URL()` は使えない。** 文字列の正規表現、または `page.evaluate(() => location.host)`（ブラウザ側の `location`）を使う
- **`setTimeout` が無い。** スリープは `page.waitForTimeout(ms)`
- **`process` / `require` が無い＝スクリプトから OS 通知を出せない。** 通知は必ずエージェントのシェルから別プロセスで撃つ
- `import` / `export` / `require` は構文としても非対応（公式リファレンス `running-code.md`（`using-playwright-cli` スキルの `output/playwright-cli/references/`） 記載どおり）
- **`console.log` の出力は CLI に出てこない**（握り潰される）。進捗をスクリプトから報告する手段は無く、
  **返り値だけが唯一の出力**

### A-5. `state-save` の保存先（引数を省略しない）

```bash
playwright-cli -s=X state-save                     # → .playwright-cli\storage-state-<timestamp>.json （カレント = リポジトリ内）
playwright-cli -s=X state-save /abs/outside/x.json  # → 指定どおり
```

- **引数なしはリポジトリ内に認証状態を書く。** このリポジトリでは `.playwright-cli` が `.gitignore` の 22 行目にあるので
  コミットはされないが、他リポジトリで同じ前提は置けない。**常に明示パス・リポジトリ外**
- 未ログインの GitHub でも 2135 bytes（Cookie が入る）。「ログインしていないから空」ではない
- 出力は `page.context().storageState({ path })` そのもの。`run-code` からも同じことができる

## B. 認証壁の検知と待機

対象は **GitHub の未ログインリダイレクト**（`github.com/settings/profile` → `github.com/login`）。
資格情報を一切使わずに「認証壁に当たった状態」を再現できるため採用した。

### B-1. 検知は URL だけで足りる

```js
async (page) => {
  const url = page.url();
  const onAuthWall =
    /\/login|\/signin|\/sso\/|accounts\.google\.com|login\.microsoftonline\.com/i.test(
      url,
    );
  const loc = await page.evaluate(() => ({
    host: location.host,
    path: location.pathname,
  }));
  return { onAuthWall, host: loc.host, path: loc.path };
};
```

実測結果: `{"onAuthWall":true,"host":"github.com","path":"/login"}`

**返り値に入るのは `host` / `path` / boolean だけで、ページ本文は一切含まれない。**
→ 既存ルール「認証画面を読まない」と両立する。

### B-2. ログイン完了待ち＋タイムアウト

```js
async (page) => {
  const t0 = Date.now();
  await page.bringToFront();
  try {
    await page.waitForURL((u) => !/\/login|\/signin/i.test(u.toString()), {
      timeout: 600000,
    });
    return { loggedIn: true, waitedMs: Date.now() - t0 };
  } catch (e) {
    return { loggedIn: false, timedOut: true, waitedMs: Date.now() - t0 };
  }
};
```

実測（timeout 40000 で検証）: `{"loggedIn":false,"timedOut":true,"waitedMs":40044,"err":"page.waitForURL: Timeout 40000ms exceeded."}`

- **タイムアウトしても CLI は exit 0**（`catch` しているため）。エラー出力にページ内容は載らない
- **タイムアウト後もセッションは `status: open` のまま。** 窓は開いている＝プランの要件どおり
- `waitForURL` は**述語関数**を受けられる。「認証ドメインから離れたら成功」という否定形で書けるので、
  ログイン後 URL を事前に知らなくてよい

**成功パスも実証済み。** `/login` に留めたページに対して待機スクリプトを走らせ、8 秒後に別プロセスから
`goto https://github.com/about`（＝ユーザーが手でログインを終えて遷移した状況の代替）を撃つと、
待機側は約 1.5 秒で検知して `{"loggedIn":true,"waitedMs":9453,"host":"github.com/about"}` を返した。

- 待機スクリプトが走っている最中にユーザーがブラウザを操作しても問題ない（待機は受動的）
- ユーザーの「終わった」宣言を待たずに**スクリプトが自力で再開できる**。ただしこれは
  「エージェントが認証画面を読む」ことにはならない（返り値は host/path と boolean だけ）

### B-3. 既存ルールとの線引き（Step2 で明文化すること）

既存の禁止は**エージェントがページ内容を会話に持ち込むこと**を止めるためのもの。実測で分かった線引き:

|                                             | 会話にページ内容が入るか                                             |
| ------------------------------------------- | -------------------------------------------------------------------- |
| `snapshot` / `find`                         | **入る**（本文が stdout に出る）→ 認証中は従来どおり禁止             |
| `run-code`（返り値を URL / boolean に限る） | **入らない**（`### Result` に返した JSON のみ。snapshot 節は出ない） |

→ **「`run-code` は禁止コマンド一覧から外してよい」ではない。**
「返り値をページ内容にしない」という条件付きでのみ許す、と書く必要がある。
`page.evaluate(() => document.body.innerText)` を返せば当然アウト。

## C. ユーザーへの通知

### C-1. `page.bringToFront()` — 動くが、フォーカスを奪う

ユーザー確認済み: **Chrome ウィンドウが最前面に出てきた**（タスクバー点滅にとどまらず、作業中のウィンドウからフォーカスを奪う）。

→ 気づかせる効果は確実。ただし**ユーザーが別作業中なら邪魔**。
Step2 では「ログイン待ちに入る瞬間に 1 回だけ」と回数を縛る。ポーリングのたびに撃たない。

### C-2. Windows トースト通知

| 手段                                                             | 結果                                                                                                                         |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **Windows PowerShell 5.1 + WinRT**（`Windows.UI.Notifications`） | **動く**。ユーザー確認済みで画面にトースト表示。**これを採る**                                                               |
| pwsh 7.6.6 + 同コード                                            | **動かない**: `Unable to find type [Windows.UI.Notifications.ToastNotificationManager,...]`（.NET Core に WinRT 射影が無い） |
| BurntToast モジュール                                            | **未インストール**。方針どおりインストールせず、可否の記録のみ                                                               |
| `[console]::beep(880,300)`                                       | **動く**（ユーザー確認済み）。最小フォールバック                                                                             |
| `msg.exe`                                                        | 存在する（`C:\Windows\System32\msg.exe`）。トーストが動くので使わない                                                        |

確定した呼び出し形:

```bash
powershell.exe -NoProfile -File <toast.ps1> -Title "..." -Body "..."
```

- **`pwsh` ではなく `powershell.exe`（5.1）を明示する**こと。ここを間違えると必ず失敗する
- `-ExecutionPolicy Bypass` は**不要**（LocalMachine が `RemoteSigned` でローカルの未署名スクリプトは通る）。
  他マシンへの移植性のために付けておくのは無害
- `.ps1` ファイル無しのインライン `-Command` 形でも動くが、bash からのクォートが極端に読みにくい。**同梱スクリプト方式にする**
- **非ブロッキング**: `Show()` は即座に戻る（実測 1 秒未満）。`Start-Process -WindowStyle Hidden` で切り離せばさらに確実。
  モーダル（`MessageBox`）は不要なので試していない＝**応答待ちで固まる手段は採らない**

AppUserModelID は `{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe`（スタートメニューの
Windows PowerShell ショートカット）を借用。専用 AUMID の登録はしない。

未確認の条件: **集中モード（Do Not Disturb）が ON のとき**はトーストがポップアップせず通知センターに入るはず。
このため**トーストだけに頼らず `bringToFront()` と併用する**。

### C-3. Claude Code 側の通知との使い分け

Claude Code には `PushNotification` ツールがある（deferred tool。`ToolSearch` で読み込んで確認）。
ただし**ツール自身の仕様として「ユーザーが端末を見ているときは送信をスキップする」**（重複を避ける設計）。
つまり**在席中のユーザーをブラウザに呼ぶ用途には使えない**。まさにその場面で黙る。
→ OS トーストをシェルから撃つ方式が必要なのはこのため。Step2 では次で固定する:

- **スクリプトがログイン待ちに入る瞬間** → OS トースト（＋ `bringToFront()`）。ユーザーはブラウザを見る必要があるため、
  ブラウザ側の通知が正しい
- **タイムアウトして作業を中断したとき** → 会話に報告するだけ。通知の二重撃ちはしない

## 既存メモとの差分

### snapshot ファイルを書くのは「ページを動かすコマンド」だけ

[browser-handoff.md](browser-handoff.md) と SKILL.md は
「**CLI がページに触れるたびに snapshot を自動保存する**」（`find` も 0.1.19 実測でファイルを書く）と書いているが、
0.1.19 の今回の実測では**書き出しの有無はコマンドの種類で決まり、出力サイズとは無関係**だった。

| コマンド                                                        | `.playwright-cli/page-*.yml` が増えるか |
| --------------------------------------------------------------- | --------------------------------------- |
| `open` / `goto` / `reload`（ページを動かす系）                  | **増える**                              |
| `snapshot` / `find` / `screenshot` / `run-code`（読むだけの系） | **増えない**（stdout に出るだけ）       |

サイズ非依存であることの確認: playwright.dev の巨大ページで `snapshot` の stdout は **736,151 bytes** だったが
ファイルは増えず、同じページの `goto` は 715,748 bytes のファイルを書いた。

**この差分はルールを緩める理由にはならない。** 認証中にコマンドを打ってはいけない本当の理由は
「ファイルに残るから」ではなく「**stdout がエージェントの会話に入るから**」であり、そちらは変わっていない。
むしろ `goto` / `reload` がファイルを書く側だと分かったので、
handoff-protocol.md がナビゲーション系を禁止側に置いているのは実測とも整合する。
→ Step2 で SKILL.md / handoff-protocol.md の根拠文を触る場合は、この 1 点だけ表現を直す（禁止自体は維持）。

## 落とし穴

- **`run-code` は `-s` を勝手に補わない。** 省略すると `default` を探して失敗する。スクリプト実行の雛形には必ず `-s=<site>` を入れる
- **待機中のセッションはロックされない。** スクリプトが 10 分待っている間に `snapshot` が通ってしまう。禁止は文章で担保する
- **`console.log` は消える。** 長い待機の途中経過は一切見えない。返り値の設計で全部を賄う
- **`state-save` の引数省略＝リポジトリ内書き出し。** 必ず明示パス
- **`bringToFront()` はフォーカスを奪う。** 連打しない
- **通知は `powershell.exe`（5.1）。`pwsh`（7）では WinRT 型が見つからず失敗する**
- run-code のサンドボックスに `URL` が無い。`new URL(page.url())` は `ReferenceError: URL is not defined`
- **ユーザーが窓を閉じると待機は `Target page, context or browser has been closed` で中断し、セッションごと消える。**
  タイムアウトと同じ扱いにしないこと（こちらは再 `open` が必要）
- **プロファイル衝突は stderr にしか出ず exit code は 0。** スクリプトから `open` する場合、成功判定は `list` で行う
- **スクラッチパッドに作った使い捨てプロファイルは `close-all` 後も削除できないことがある**
  （`Permission denied`。今回も `Default/Account Web Data` 等が残った）。
  [browser-handoff.md](browser-handoff.md) の既知事象そのままで、掃除はベストエフォート扱いにする

## Step2 への申し送り

雛形（`references/scripted-automation.md` にそのまま載せられる形）:

```bash
# 1. 認証壁に当たったか検知する（URL だけ・本文は返さない）
playwright-cli -s=<site> run-code --filename=.../detect-auth-wall.js

# 2. 壁だったら: ユーザーに気づかせてから待つ
powershell.exe -NoProfile -File .../notify-user.ps1 \
  -Title "ログインをお願いします" -Body "<site> の窓で認証を完了してください"
playwright-cli -s=<site> run-code --filename=.../wait-for-login.js   # 内部で bringToFront + waitForURL(600s)

# 3. 返り値で分岐
#    {"loggedIn":true}                        → 本来の作業スクリプトを続行
#    {"loggedIn":false,"timedOut":true}       → 窓は開いたまま中断し、会話で報告して終わる
```

- 同梱するのは `scripts/notify-user.ps1`（トースト。C-2 の形をそのまま）。ビープはフォールバックとして本文に 1 行
- `detect-auth-wall.js` / `wait-for-login.js` は**同梱せず reference 内のコード片にする**。
  認証ドメインのパターンはサイトごとに変わるので、固定スクリプトにすると必ず合わなくなる
- 禁止事項として書き下すこと: 返り値にページ本文を入れない / 待機中に `snapshot`・`find` を撃たない /
  資格情報をスクリプト・ファイル・環境変数に置かない / `state-save` をリポジトリ内に出さない
