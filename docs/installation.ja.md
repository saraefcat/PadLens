# 導入手順

[English](installation.md) · [PadLens](../README.ja.md)

## 概要

Controller Overlayは現在のゲームパッド入力を**Input Overlayソース**に表示します。Input Historyは直近の入力をOBSの**ブラウザソース**に表示します。2つは別々に導入できます。

## 必要環境

[OBS Studio](https://obsproject.com/)と[Input Overlay](https://github.com/univrsal/input-overlay)プラグインを別途導入してください。PadLensには同梱されません。プラグインの導入方法は[公式手順](https://github.com/univrsal/input-overlay/wiki/Installation)を参照してください。

| 項目 | 内容 |
| --- | --- |
| 開発に使用したOS | Windows 10 / Windows 11 |
| 新規利用の推奨OS | Windows 11 |
| 動作確認に使用したOBS Studio | 33.0.0（ポータブル版） |
| 動作確認に使用したInput Overlay | 5.1.2 |

- 表のOBS StudioとInput Overlayの組み合わせで表示を確認しています。開発に使用したOSは、両OSで全操作を検証したという意味ではありません。
- 全操作や、表以外のソフトウェアのバージョンでの動作は未確認です。
- [Windows 10の通常サポートは終了](https://support.microsoft.com/en-us/windows/deployment/updates-lifecycle/windows-10-support-has-ended-on-october-14-2025)しているため、新規利用にはWindows 11を推奨します。

## ファイルの取得・展開

GitHubのソースまたは配布ZIPなど、入手したPadLensのファイル一式を展開してください。

- `controller/`と`history/`のフォルダー構成を維持します。PNG・JSON・HTML・JavaScriptを個別に移動する必要はありません。
- 配布ZIPには開発者向けスクリプトは含まれません。
- 既存の配信シーンを保護するため、最初はOBSのテスト用シーンで確認してください。

## Controller Overlay

1. OBSのソース一覧から**Input Overlayソース**を追加します。[プラグインの公式使用方法](https://github.com/univrsal/input-overlay/wiki/Usage)も参照してください。
2. ソースのプロパティで、`controller/`以下のPNGとJSONを次の組み合わせで指定します。

   | 表示 | PNG | JSON |
   | --- | --- | --- |
   | 標準版 | `controller_atlas.png` | `controller_layout.json` |
   | 高透過版 | `controller_atlas_light.png` | `controller_layout.json` |
   | Sara通常版 | `controller_atlas_sara.png` | `controller_layout_sara.json` |
   | Sara RTA版 | `controller_atlas_sara_rta.png` | `controller_layout_sara.json` |

3. Input Overlayソース側でゲームパッドを選択します。
4. ゲームパッドを操作し、入力に応じて表示が変わるか確認します。

- 反応しない場合は、OBSの「ツール」から開くInput Overlayプラグインの設定でゲームパッドフックを確認してください。
- **Controller単独利用にはWebSocketサーバーは不要**です。
- Sara版には猫耳のLB/RB、長円形のLT/RT、肉球スティック、猫目風のView/Menu、鼻と口のHOMEがあります。Sara版のOBS実機表示は未確認です。

機能と制約は[Controllerの詳細](../controller/README.ja.md)を参照してください。

## Input History

Historyでは**ブラウザソース**を使用します。Input Overlayソースの追加は不要です。

1. OBSの「ツール」からInput Overlayプラグインの設定を開きます。
2. 「WebSocket Server」を有効にし、サーバーの待受アドレスを`127.0.0.1`、ポートを`16899`に設定します。
3. 設定を反映するため、配信・録画をしていないときにOBSを再起動します。
4. OBSのソース一覧から**ブラウザソース**を追加します。
5. **ローカルファイル**に`history/input_history.html`を指定します。
6. ブラウザソースの幅を200px、高さを400pxにします。
7. OBSの「対話（操作）」を開き、History画面の右上にポインターを移動して設定ボタンを表示します。
8. ゲームパッドを操作し、入力が履歴に表示されるか確認します。

- 200×400pxはOBSのHistory用ブラウザソースの推奨サイズです。
- 240／260／300pxはHistory内部の表示幅設定です。

表示設定と機能は[Historyの詳細](../history/README.ja.md)を参照してください。

## 問題解決

| 症状 | 最初に確認すること |
| --- | --- |
| Controller画像が表示されない | Input Overlayソースのプロパティで、対応するPNGとJSONの組を指定したか。 |
| Controllerのボタンが反応しない | Input Overlayソース側のゲームパッド選択と、プラグイン設定側のゲームパッドフックを確認します。 |
| History画面が表示されない | ブラウザソースのローカルファイル指定と、`history/`のフォルダー構成を確認します。 |
| HistoryのWebSocketが接続されない | プラグイン設定でサーバーの有効化と`127.0.0.1:16899`での待受を確認します。Windowsでは`history/check_websocket.ps1`で待受を読み取り専用で確認できます。 |
| WebSocketは接続されるが入力が表示されない | プラグイン設定側のゲームパッドフックと、Windowsでのゲームパッド認識を確認します。 |
| Historyの設定画面を開けない | OBSの「対話（操作）」を開き、History画面の右上にポインターを移動します。 |

詳しくは[Controllerの詳細](../controller/README.ja.md)と[Historyの詳細](../history/README.ja.md)を参照してください。

## セキュリティ

- WebSocketサーバーは`127.0.0.1`などのループバックアドレスで待ち受けるよう設定してください。History側の接続先をループバックにするだけでは、サーバーの待受範囲は制限できません。
- `0.0.0.0`や`::`の全インターフェース待受を避け、ポートを外部へ公開しないでください。
- 不要なキーボード・マウスフックは無効にしてください。
- OBSの管理者権限での起動や、ブラウザのサンドボックス無効化は必要ありません。

詳しくは[SECURITY.md](../SECURITY.md)を参照してください。
