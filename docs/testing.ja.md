# テストと検証

[English](testing.md) · [PadLens](../README.ja.md)

この文書は、ソース一式から実行できるテストと、その確認範囲を示します。PadLensの通常利用にテスト用ツールは不要です。構成は[システム構成](architecture.ja.md)、利用時の注意は[セキュリティ情報](../SECURITY.md)を参照してください。

## テスト一覧

| 検証 | 目的 | 必要環境・実行方法 | 確認できる範囲 |
| --- | --- | --- | --- |
| HistoryのNode.jsテスト | 入力処理と表示設定のロジックを確認 | Node.jsで下記の`node --test`を実行 | 30件。イベント検証、順序、同時押し、入力制限、連番など |
| JavaScript構文検査 | 実行用スクリプトの構文を確認 | Node.jsで下記の`node --check`を実行 | 構文のみ。OBSでの表示や通信は確認しない |
| Chromiumブラウザテスト | Historyの表示・操作をブラウザで確認 | Python PlaywrightとChromiumで下記5ファイルを個別実行 | 画面幅、設定、模擬入力、連番、負荷、旧設定移行。OBS実機の動作は確認しない |
| Controller画像・配置検査 | 配布PNGとJSONの整合を確認 | PythonとPillowで`controller/verify_layout.py`を実行 | 両PNGの寸法・透過度と配置JSONの18要素。実際のボタン操作は確認しない |
| 配布ZIP検査 | 配布ファイルの構成と参照を確認 | Python標準ライブラリで`scripts/package_release.py`を実行 | 安定版ハッシュ、HTML・Markdown参照、CRC、2回生成時の再現性 |
| 公開スナップショット検査 | 公開候補の抽出を確認 | Python標準ライブラリで`scripts/build_public_snapshot.py`を実行 | 許可リスト、リンク、機密情報の静的検査、正本とのハッシュ照合、再現性 |

## 必要な環境

- **通常利用**：OBS StudioとInput Overlayプラグインが必要です。Node.js、Python、Playwrightは不要です。
- **Node.jsテスト・構文検査**：Node.jsを使用します。
- **Controller配置検査**：PythonとPillowを使用します。CairoSVGは既存PNGの検査には不要で、画像を再生成する場合にのみ必要です。
- **ブラウザテスト**：Python Playwrightと対応するChromiumを使用します。検証時はPython 3.12.14、Playwright 1.64.1とPlaywright管理版Chromiumを使用しました。これは最低対応バージョンの指定ではありません。
- **ZIP・公開スナップショット**：Python標準ライブラリを使用します。

## 実行方法

以下のコマンドはWindows PowerShellでPadLensの**ソースルート**から実行します。`python`は実際に導入したPythonを指します。テストスクリプトや公開スナップショット生成ツールは、配布ZIPには含まれません。

### Node.jsとJavaScript構文

```powershell
node --test history/tests/branding.test.js history/tests/hardening.test.js history/tests/history_core.test.js history/tests/layout_policy.test.js history/tests/test_sequence.test.js

node --check history/user_config.js
node --check history/history_core.js
node --check history/overlay.js
```

### Controllerの画像・配置

```powershell
python -X utf8 controller/verify_layout.py
```

この検査にはPillowが必要ですが、OBSの起動や画像の再生成は不要です。

### Chromiumブラウザテスト

初回は、PadLensのソースルートで次の隔離環境を用意します。Pythonがインストールされていることが前提です。Playwright 1.64.1は検証に使用したバージョンで、最低必要バージョンを示すものではありません。仮想環境とブラウザは`.local/`内に置き、普段使うブラウザのプロファイルやグローバルPython環境は変更しません。

```powershell
python -m venv .local/venv-playwright
New-Item -ItemType Directory -Force .local/playwright-browsers | Out-Null
$env:PLAYWRIGHT_BROWSERS_PATH = (Resolve-Path '.local/playwright-browsers').Path
$browserPython = (Resolve-Path '.local/venv-playwright/Scripts/python.exe').Path
& $browserPython -m pip install 'playwright==1.64.1'
& $browserPython -m playwright install chromium
```

準備済みの環境では、次のように5ファイルのうち最初の4ファイルを個別に実行します。仮想環境を有効化する必要はありません。

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = (Resolve-Path '.local/playwright-browsers').Path
$browserPython = (Resolve-Path '.local/venv-playwright/Scripts/python.exe').Path

$browserTests = @(
    'history/tests/test_browser.py'
    'history/tests/test_websocket_browser.py'
    'history/tests/test_stress_browser.py'
    'history/tests/test_sequence_browser.py'
)
foreach ($test in $browserTests) {
    & $browserPython $test
    if ($LASTEXITCODE -ne 0) {
        throw "$test failed (exit code $LASTEXITCODE)"
    }
}
```

最初の4ファイルはデモ入力または模擬WebSocketを使います。**5つ目の`test_branding_migration.py`はWebSocketを模擬しておらず、既定の`127.0.0.1:16899`への接続を試みます。** 次の読み取り専用の待受確認に失敗した場合や待受がある場合は、5つ目を実行しないでください。

```powershell
$checked = $false
$listeners = @()
try {
    $listeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
        Where-Object { $_.LocalPort -eq 16899 })
    $checked = $true
} catch {
    $checked = $false
}
if (-not $checked) {
    Write-Warning 'NOT RUN: 待受一覧を取得できないため、旧設定移行テストを見送ります。'
} elseif ($listeners.Count -gt 0) {
    Write-Warning 'NOT RUN: ポート16899で待受中のため、旧設定移行テストを見送ります。'
} else {
    & $browserPython history/tests/test_branding_migration.py
    if ($LASTEXITCODE -ne 0) {
        throw "history/tests/test_branding_migration.py failed (exit code $LASTEXITCODE)"
    }
}
```

ブラウザ起動ヘルパーはChromiumのサンドボックスを有効にします。スクリーンショットなどの生成物は`.local/browser-tests/`に保存されます。

### 配布ZIPと公開スナップショット

```powershell
python scripts/package_release.py
python scripts/build_public_snapshot.py
```

ZIPは`dist/PadLens-local-preview.zip`、公開スナップショットは`.local/public-staging/PadLens/`に生成されます。両スクリプトは内容を検査し、SHA-256を表示します。同じ入力でそれぞれ2回実行し、表示されたSHA-256が一致することを確認してください。公開スナップショットに手作業の変更がある場合、生成スクリプトは上書きを拒否します。

## 確認済みの範囲

- HistoryのNode.jsテスト30件とChromiumブラウザテスト5ファイルは、既存の検証環境で成功しています。上記のNode.jsコマンドも30件成功することを再確認しました。
- Chromiumでは、模擬入力を使った表示、設定操作、200×400pxを含むレイアウト、999の次に01へ戻る連番などを確認しています。WebSocket模擬試験はブラウザ側の処理を確認するもので、本番Input Overlayサーバーの接続や再接続を保証しません。
- OBS Studio 33.0.0（ポータブル版）とInput Overlay 5.1.2で、PadLensのファイルを使った表示のスモークテストが行われています。網羅的な実機試験とは区別します。

## 未検証事項・制約

- Controllerの全ボタンをOBS上で網羅的に操作する試験は未実施です。
- OBS再起動後のHistory表示設定の保持と、実環境でのWebSocket切断・再接続は未検証です。
- ブラウザテストの`localStorage`はメモリ内の模擬実装です。ブラウザ終了後やOBS再起動後の永続化は確認しません。
- 自動消去の設定操作はテスト対象ですが、時間経過による消去を実ブラウザで確認した結果ではありません。
- 静的検査や模擬イベントの成功は、すべてのOBS環境での動作を保証しません。

## 安全にテストするために

- OBSの本番シーンや配信設定を変更せず、実機確認が必要な場合はテスト用シーンを使用してください。
- 本番Input Overlayサーバーを無断でテスト対象にしないでください。日常利用のブラウザプロファイルも使用しません。
- Chromiumのサンドボックスを無効にする起動オプションを追加しないでください。
- テスト生成物は`.local/`や`dist/`など公開対象外に置き、認証情報や実際のキー入力内容をログへ保存しないでください。
