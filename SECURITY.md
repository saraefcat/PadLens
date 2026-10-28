# Security / セキュリティ

[日本語](#日本語)

## English

PadLens uses OBS Studio and the Input Overlay plugin, which are separate software. The two PadLens components use different OBS sources:

| Component | OBS source | Input Overlay WebSocket server |
| --- | --- | --- |
| Controller Overlay | Input Overlay source | Not required |
| Input History | Browser source | Required |

Input History does not require adding an Input Overlay source. Both components require the Input Overlay plugin.

### Safe setup

- Input History connects to `ws://127.0.0.1:16899/` by default. For the usual setup, configure the **server's bind address in the Input Overlay plugin settings** to use `127.0.0.1` as well. The client's URL alone does not restrict where the server listens.
- Input Overlay sends WebSocket input data without encryption. Avoid all-interface bind addresses such as `0.0.0.0` and `::`, and do not expose or forward the WebSocket port to other machines.
- Enable the gamepad hook when needed for gamepad input. Disable keyboard and mouse hooks if they are unnecessary. Consider the effect on existing OBS settings before changing plugin options.
- Neither component requires OBS to run as administrator. Do not disable browser sandboxing to troubleshoot Input History.

### Data and limitations

- Input History keeps input rows in browser memory; reloading the browser source clears them. It saves display preferences in `localStorage`.
- In the reviewed PadLens code, no intentional transfer of input history to an external service was found. This finding does not cover logging or storage by OBS Studio or Input Overlay.
- A loopback listener does not authenticate other processes on the same PC. Input Overlay server authentication and Origin restrictions have not been verified.

### Reporting vulnerabilities

To report a vulnerability privately, open the [Security Advisories page](https://github.com/saraefcat/PadLens/security/advisories) and select **Report a vulnerability**. Do not post secrets or specific exploit steps in a public issue.

## 日本語

PadLensが使用するOBS StudioとInput Overlayプラグインは、PadLensとは別のソフトウェアです。2つの機能は異なるOBSソースを使用します。

| 機能 | OBSソース | Input OverlayのWebSocketサーバー |
| --- | --- | --- |
| Controller Overlay | Input Overlayソース | 不要 |
| Input History | ブラウザソース | 必要 |

History単独利用ではInput Overlayソースの追加は不要です。どちらの機能にもInput Overlayプラグイン自体は必要です。

### 安全な設定

- Historyの既定接続先は`ws://127.0.0.1:16899/`です。通常の導入では、**サーバーの待受アドレスもInput Overlayプラグインの設定**で`127.0.0.1`にしてください。クライアントの接続先だけでは、サーバーの待受範囲は制限できません。
- Input OverlayはWebSocketの入力データを暗号化せずに送信します。`0.0.0.0`や`::`による全インターフェース待受を避け、WebSocketポートを外部へ公開・転送しないでください。
- ゲームパッド入力に必要な場合はゲームパッドフックを有効にし、不要なキーボード・マウスフックは無効にしてください。プラグインの設定変更前に、既存のOBS環境への影響を確認してください。
- どちらの機能にもOBSの管理者権限起動は不要です。Historyの問題解決のためにブラウザのサンドボックスを無効化しないでください。

### データと制約

- Historyの入力履歴はブラウザ内メモリに保持され、ブラウザソースの再読み込みで消えます。表示設定は`localStorage`に保存されます。
- PadLens独自のコードに、入力履歴を外部サービスへ意図的に送信する処理は確認されていません。OBS StudioやInput Overlay自身のログ・保存処理については、この確認結果から判断できません。
- ループバック待受でも、同じPC上の別プロセスが自動的に認証されるわけではありません。Input Overlayサーバーの認証方式やOrigin制限は未検証です。

### 脆弱性の報告

脆弱性を非公開で報告する場合は、[Security Advisoriesページ](https://github.com/saraefcat/PadLens/security/advisories)の**Report a vulnerability**を選択してください。秘密情報や具体的な悪用手順を公開Issueへ投稿しないでください。
