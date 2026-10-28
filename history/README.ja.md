# Input History

[English](README.md) · [PadLens](../README.ja.md)

## 概要

直近のゲームパッド入力を、OBSのブラウザソースに履歴表示します。Input OverlayプラグインのWebSocketを利用し、Controller OverlayやInput Overlayソースを追加せずに使用できます。OBS StudioとInput Overlayプラグインは別途必要です。

## 表示例

<p><a href="../docs/images/history-preview.png"><img src="../docs/images/history-preview.png" alt="入力履歴の表示例" width="200"></a> <a href="../docs/images/history-settings.png"><img src="../docs/images/history-settings.png" alt="設定画面の表示例" width="200"></a></p>

合成・模擬入力によるプレビューです。左は保存済み設定がない場合の既定表示（ヘッダーON・Δt OFF）、右は設定画面の例です。画像をクリックすると元画像を開けます。

## 動作確認済み環境・推奨設定

| 項目 | 内容 |
| --- | --- |
| 開発に使用したOS | Windows 10 / Windows 11 |
| 新規利用の推奨OS | Windows 11 |
| 動作確認に使用したOBS Studio | 33.0.0（ポータブル版） |
| 動作確認に使用したInput Overlay | 5.1.2 |
| History用ブラウザソースの推奨サイズ | 幅200px × 高さ400px |
| WebSocketの既定接続先 | `127.0.0.1:16899` |

[Windows 10の通常サポートは終了](https://support.microsoft.com/en-us/windows/deployment/updates-lifecycle/windows-10-support-has-ended-on-october-14-2025)しているため、新規利用者向けの推奨OSには含めません。OBSのブラウザソースの200×400pxは表示領域のサイズで、History内部の幅設定240／260／300pxとは別です。他のOBS・Input Overlayのバージョンでの動作は未確認です。

## ファイル構成

| ファイル | 用途 | 配布ZIP |
| --- | --- | --- |
| `input_history.html` | OBSのブラウザソースで開くページ | 含む |
| `user_config.js` | 接続先と表示設定の既定値 | 含む |
| `history_core.js` | 入力イベントと履歴の処理 | 含む |
| `overlay.js` | WebSocket接続、描画、設定画面 | 含む |
| `check_websocket.ps1` | Windowsで待受アドレスとポートを確認する任意の診断ツール | 含む |

履歴表示には上のHTMLと3つのJavaScriptが必要です。`check_websocket.ps1`は必須ではありません。Python・Node.js・Playwrightは通常利用には不要です。

## 導入方法

詳しくは[導入手順](../docs/installation.ja.md)を参照してください。

1. OBS StudioとInput Overlayプラグインを導入します。
2. OBSの「ツール」からInput Overlayプラグインの設定を開き、「WebSocket Server」を有効にします。
3. WebSocketサーバーの待受を`127.0.0.1:16899`に限定します。設定の反映にはOBSの再起動が必要です。
4. ダウンロード・展開した`history/`のフォルダー構成を維持します。
5. OBSに「ブラウザ」ソースを追加し、ローカルファイルとして`history/input_history.html`を指定します。
6. ブラウザソースの幅を200px、高さを400pxにします。
7. OBSの「対話（操作）」から設定画面を開き、ゲームパッド入力が履歴に表示されるか確認します。

History単独利用ではInput Overlayソースの追加は不要です。入力が表示されない場合は、プラグイン側のゲームパッドフックとWindowsでのゲームパッド認識を確認してください。

## 表示設定

「対話（操作）」で右上にポインターを移動すると設定ボタンが現れます。

| 設定項目 | 内容 | `user_config.js`の既定値 |
| --- | --- | --- |
| 履歴の順序 | 新しい入力を上／下に表示 | 上 |
| 入力間隔Δt | 履歴行の間隔を表示 | OFF |
| ヘッダー | タイトルと接続状態を表示 | ON |
| 自動消去 | 古い履歴を一定時間後に消去 | ON（9秒） |
| 履歴内部の幅 | 240／260／300pxから選択 | 260px |

消去ボタンを押すと、現在の履歴を削除できます。

表示設定は変更時にブラウザの`localStorage`へ保存され、保存済み設定がある場合は`user_config.js`の既定値より優先されます。旧設定キーしかない場合は読み込んで現行キーへ移行し、旧キーは削除しません。ブラウザ側が保存できない場合は変更が保持されません。既定の接続URLは`ws://127.0.0.1:16899/`です。

## 主な機能

- 直近のゲームパッド入力を履歴表示し、近接した同時押しを1行にまとめます。
- 履歴に01から999までの連番を付け、999の次は01に戻ります。
- 履歴件数には上限があり、不正なイベントは表示処理から除外します。

## 問題解決

| 症状 | 最初に確認すること |
| --- | --- |
| History画面が表示されない | ブラウザソースのローカルファイル指定と、HTML・3つのJavaScriptの配置を確認します。 |
| WebSocketが接続されない | Input Overlayプラグインの「WebSocket Server」が有効で、ループバックの`127.0.0.1:16899`で待ち受けているか確認します。Windowsでは`check_websocket.ps1`で読み取り専用の確認ができます。 |
| 接続されるが入力が表示されない | プラグインのゲームパッドフックと、Windowsでのゲームパッド認識を確認します。 |
| 設定画面を開けない | OBSの「対話（操作）」を開き、右上へポインターを移動して設定ボタンを確認します。 |
| 設定が保存されない | そのブラウザソースで`localStorage`が利用できるか確認します。OBS再起動後の保持は未検証です。 |
| 表示幅や履歴の配置が想定と異なる | OBSブラウザソースの200×400pxと、History内部の幅240／260／300pxをそれぞれ確認します。 |

詳しい確認方法は[導入手順](../docs/installation.ja.md)を参照してください。

## セキュリティ

- WebSocketサーバーは`127.0.0.1`などのループバックアドレスで待ち受けるよう設定します。Historyの接続先だけを`127.0.0.1`にしても、サーバーの待受範囲は制限できません。
- `0.0.0.0`や`::`の全インターフェース待受を避け、ポートを外部へ公開しないでください。
- 不要なキーボード・マウスフックは無効にしてください。
- OBSを管理者権限で起動する必要はありません。
- ブラウザのサンドボックスを無効にする必要はありません。

詳しくは[セキュリティ情報](../SECURITY.md)を参照してください。

## 制約

- 履歴はブラウザ内メモリにあり、再読み込みで消えます。表示設定は`localStorage`へ保存します。
- Δtは入力イベントの時刻から計算し、ゲームが入力を受け付けた時刻ではありません。
- ブラウザテストは模擬WebSocketイベントを使用します。OBSでの全入力、切断・再接続、OBS再起動後の設定保持は未検証です。

## ライセンス

PadLens独自のHTMLとJavaScriptには[MIT License](../LICENSE)を適用します。著作権表示は`Copyright (c) 2026 saraefcat`です。OBS StudioとInput Overlayは別プロジェクトで、それぞれのライセンスに従います。
