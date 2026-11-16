---
type: Research Notes
title: "ブラウザ引き渡し（handoff）調査メモ"
description: "Records measurements of handing a playwright-cli browser session to the user and back (headed Chrome, persistent profiles, who types credentials, how the agent learns login finished) that the sharing-browser-with-user skill is built on. Use when changing that skill's handoff phases or checking why a handoff rule exists."
tags: [tools]
status: stable
step: Step1 (sharing-browser-with-user)
verified-on: 2026-09-14
verified-with: "@playwright/cli 0.1.19 (playwright-core 1.63.0-alpha-2026-08-31), Google Chrome 152, Windows 11"
---

# ブラウザ引き渡し（handoff）調査メモ

sharing-browser-with-user プラン Step1（完了プラン。このリポジトリには持ち込んでいない） の実測結果。
スキル本文（Step2）はこのファイルの「決定事項」だけを前提にしてよい。

検証は `@playwright/cli` を **0.1.17 → 0.1.19（latest）に更新してから**再実施している。
`pnpm add -g @playwright/cli@latest` でグローバル更新。

## 決定事項

| 論点               | 決定                                                                                                                                                                          | 根拠                                                                                                                                                                                                                             |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 方式               | **A（`open --headed --persistent` でエージェントが起動、ユーザーが同じ窓で認証）を既定**。B（`attach --cdp=chrome`）は Google アカウント等で A が弾かれた場合のフォールバック | A は 1 コマンドで完結し、実測で `navigator.webdriver === false`（下記）。B はユーザーに `chrome://inspect` の手動有効化を強いる                                                                                                  |
| ブラウザ           | `--browser` 省略でよい（このマシンの既定が実 Chrome チャネル）。明示するなら `--browser=chrome`                                                                               | `navigator.userAgentData.brands` に `Google Chrome / 152` が入る = バンドル Chromium ではなく実 Chrome                                                                                                                           |
| プロファイル保存先 | **`--profile=%LOCALAPPDATA%\claude-browser-profiles\<name>` を明示する**（`--persistent` の自動生成先には任せない）                                                           | 自動生成先のルートは CLI を更新すると変わり、**過去のログインが丸ごと参照できなくなる**（下記「CLI 更新でプロファイルが切り替わる」）。要件は「スキル/プロセスをまたいで再ログイン不要」なので、CLI 更新で壊れる置き場は使えない |
| 認証完了の検知     | **ユーザーの「終わった」宣言を待つ**。エージェントはポーリングしない                                                                                                          | 「認証画面を読まない」要件と両立するのは宣言待ちだけ                                                                                                                                                                             |
| セッションの寿命   | headed は放置しても落ちない（実測で数十分維持）。`open` 自体がフォアグラウンドを占有するので**バックグラウンド起動が必須**                                                    | 下記「落とし穴」参照                                                                                                                                                                                                             |

## 実測で確定した仕様（0.1.19）

### プロファイルの実体

`--persistent` の自動生成先は次の形：

```
%LOCALAPPDATA%\ms-playwright\daemon\<daemon-hash>\ud-<session>-<browser>
```

- 実測値: `...\ms-playwright\daemon\a633ec1654693694\ud-probe19-chrome`
- 中身は本物の Chrome プロファイル（`Default/`, `Local State`, `Safe Browsing` ほか）
- `<daemon-hash>` は **cwd に依存しない**（別ディレクトリから `playwright-cli list` しても同一パス・同一セッションが見える）
- 現在のパスは `playwright-cli list` の `user-data-dir` 行で常に確認できる。**パスを推測せず `list` で読む**

**ディレクトリ名はセッション名とブラウザ名から決まる。** `-s=<name>` を変える、または `--browser` を変えると別プロファイルになり再ログインが必要。→ スキルでは**サイトごとに固定のセッション名**を規約化する。

### CLI 更新でプロファイルが切り替わる（`--profile` 明示の理由）

`<daemon-hash>` は CLI のインストール実体に紐づく。0.1.17 → 0.1.19 の更新で：

```
0.1.17: ...\daemon\bb19e51bd1e3db03\ud-<session>-chrome
0.1.19: ...\daemon\a633ec1654693694\ud-<session>-chrome
```

同じ `-s` / `--persistent` でもルートが変わり、**旧プロファイルは移行されず取り残される**（旧ディレクトリはそのまま残存）。ハッシュは同一バージョン内では安定（close → 再 open で同一パス・データ保持を確認済み）。

→ 認証状態を長期保持するのが目的なので、**`--profile` で固定パスを指定する**。

### `--persistent` / `--profile` は毎回付ける必要がある

`-s` が同じでも、`--persistent`（または `--profile`）を付けずに `open` すると `user-data-dir: <in-memory>` になり、前回のログイン状態は**見えない**（消えるのではなく、別の一時プロファイルになる）。

実測:

| 操作                                                                                        | 結果                                         |
| ------------------------------------------------------------------------------------------- | -------------------------------------------- |
| `-s=X open --headed --persistent` → localStorage 書き込み → `close` → 同じフラグで再 `open` | 値が**残っている**                           |
| 同じ `-s=X` で `--persistent` **なし**に `open`                                             | `<in-memory>`、`No localStorage items found` |

### 1 プロファイル = 1 インスタンス

同じ `--profile` を指す 2 つ目のセッションを開くと daemon が exit code 1 で落ちる：

```
Error: Browser is already in use for <dir>, use --isolated to run multiple instances of the same browser
```

（`--isolated` は `open --help` には出てこない内部フラグ。使わない。）
ユーザーの普段使い Chrome プロファイルとの共用も同じ理由で不可。加えて公式ドキュメントが既定プロファイルの自動化を非サポートと明記している（`docs/src/api/class-browsertype.md` の `launchPersistentContext.userDataDir` warning → https://developer.chrome.com/blog/remote-debugging-port ）。

### 自動化フィンガープリント

Playwright が起動した headed 実 Chrome での実測値：

```json
{ "webdriver": false, "plugins": 5, "lang": ["en-GB", "en-US", "en"] }
```

`navigator.webdriver` は **false**。一般的な IdP の webdriver 判定は素通りする見込み。
ただし Google は headless 指紋・自動化フラグ・IP/タイミングなど複数シグナルで判定しており、自動化起動のブラウザからのサインインを `This browser or app may not be secure` で弾く事例が現在も報告されている
（https://getautonoma.com/blog/how-to-test-google-oauth-login 、https://stackoverflow.com/questions/76603386/ 、https://support.google.com/chrome/thread/224353947 ）。
**Google アカウントでのログインは A が弾かれうる前提で、B（`attach --cdp=chrome`）をフォールバックとして SKILL.md に書く。**
`--disable-blink-features=AutomationControlled` 等の検知回避には踏み込まない（方針: 人が本物のブラウザで正規にログインする）。

### スナップショット（upstream main）と 0.1.19 の差分

| 項目                                              | スナップショット記述 | 0.1.19 実測                                                                             |
| ------------------------------------------------- | -------------------- | --------------------------------------------------------------------------------------- |
| `open --idle-timeout=<ms>`                        | あり                 | **`open --help` に無い**（0.1.17 / 0.1.19 とも）。headed は元々落ちないので当面影響なし |
| `attach --cdp=<channel>`                          | あり                 | あり（`--cdp` / `--endpoint` / `--extension` / `--session`）                            |
| `list` / `close-all` / `kill-all` / `delete-data` | あり                 | あり                                                                                    |

`open --help` の実オプションは `--browser` / `--config` / `--device` / `--headed` / `--mobile` / `--persistent` / `--profile` のみ（0.1.17 から変化なし）。

同梱 SKILL.md のパスは 0.1.19 で移動している。スナップショット同期時は新しい方を見る：

```
0.1.17: playwright-core/lib/tools/cli-client/skill/SKILL.md
0.1.19: playwright-core/lib/tools/skills/playwright-cli/SKILL.md
```

## 落とし穴

- **`open --headed` は戻ってこない。** ブラウザが閉じるまでフォアグラウンドを占有する。エージェントは必ずバックグラウンドで起動し、`playwright-cli list` で `status: open` を確認してから次のコマンドを出す。
- **`delete-data` は認証状態も消す。** トラブルシュートとして書くときは「再ログインが必要になる」を必ず併記する。0.1.19 の挙動: 開いているセッションに対しても成功し（ブラウザは閉じる）`Deleted user data for browser '<name>'.`、対象が無ければ `No user data found for browser '<name>'.` で exit 0。
  （0.1.17 では対象が無いとき Node の uncaught exception を吐いていた。更新で解消。）
- **Windows ではプロファイルディレクトリの手動削除がしばしば失敗する。** `close` / `close-all` / `kill-all` 直後でも一部ファイル（`Default/WebStorage/QuotaManager` 等）が掴まれたままで `Permission denied` になる。手動 `rm -rf` ではなく `delete-data` を使い、掃除はベストエフォート扱いにする。
- `cookie-set` に `--domain` / `--path` を渡すと `Protocol error (Storage.setCookies): Invalid cookie fields` になることがある（0.1.17 で観測）。認証状態の投入には使わない。

## Step2 への申し送り

- コマンド雛形（既定＝方式 A）:
  ```bash
  # 0. プロファイルは固定パス。セッション名はサイトごとに固定
  PROFILE="$LOCALAPPDATA/claude-browser-profiles/<site>"

  # 1. バックグラウンドで起動（open --headed はブロックする）
  playwright-cli -s=<site> open <url> --headed --profile="$PROFILE" &

  # 2. status: open を確認
  playwright-cli list

  # 3. ここでユーザーに手動ログインを依頼し、「終わった」宣言を待つ。
  #    この間エージェントは snapshot / screenshot / state-save / cookie-* / localstorage-* を実行しない

  # 4. 宣言後、通常操作に入る
  ```
- SKILL.md に明文ルールとして入れるもの: 固定セッション名、`--profile` 固定パス必須（毎回指定）、認証中の読み取り禁止コマンド一覧、Google 用の B フォールバック、`delete-data` の副作用。
