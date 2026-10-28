# システム構成

[English](architecture.md) · [PadLens](../README.ja.md)

## 概要

PadLensには、Controller OverlayとInput Historyという独立した2種類の表示機能があります。OBS StudioとInput Overlayプラグインは別途導入が必要です。PadLens自身は常駐サービスを追加しません。

## コンポーネント比較

| 項目 | [Controller Overlay](../controller/README.ja.md) | [Input History](../history/README.ja.md) |
| --- | --- | --- |
| OBSソース | Input Overlay | ブラウザ |
| 入力の取得 | Input Overlayプラグイン | Input OverlayプラグインのWebSocketサーバー |
| 表示方式 | PNGアトラスとJSON配置 | HTML・JavaScript |
| WebSocketサーバー | 不要 | 必要 |

## 処理の流れ

```text
Controller: ゲームパッド → Input Overlayプラグイン → Input Overlayソース（PNG・JSON） → OBS表示
History:    ゲームパッド → Input Overlayプラグイン → WebSocket → HTML・JavaScript → OBSブラウザソース
```

## Controller Overlayの仕組み

| ファイル | 役割 |
| --- | --- |
| `controller/controller_atlas.png` | 標準版のPNGアトラス |
| `controller/controller_atlas_light.png` | 高透過版のPNGアトラス |
| `controller/controller_layout.json` | 論理入力と画像内の領域・表示位置の対応を定義 |

2種類のPNGはどちらも2048×1199pxで、同じJSONを使用します。

- `controller/build_controller_overlay.py`は画像を生成します。
- `controller/verify_layout.py`は画像内の領域と配置を検証します。

これらのツールは通常利用には不要です。

## Input Historyの仕組み

| ファイル | 役割 |
| --- | --- |
| `history/input_history.html` | OBSブラウザソースで開くページ。以下の3つのスクリプトを読み込みます。 |
| `history/user_config.js` | 接続先と表示設定の既定値 |
| `history/history_core.js` | イベントの検証と履歴状態の管理 |
| `history/overlay.js` | WebSocket接続、描画、設定画面 |

クライアントの既定接続先は`ws://127.0.0.1:16899/`です。HistoryはプラグインのWebSocketサーバーを利用するため、OBSにInput Overlayソースを追加しなくても使用できます。

## データ保存

| データ | 保存先 | ブラウザソースの再読み込み時 |
| --- | --- | --- |
| 入力履歴 | ブラウザ内メモリ | 消去される |
| 表示設定 | `localStorage` | 利用できる場合は保存済みの値を読み込む |

保存済みの表示設定は`user_config.js`の既定値より優先されます。旧設定キーも互換性のため読み込み、現行キーへ移行します。

表示するΔtは入力イベントの時刻に基づきます。ゲームが入力を受け付けた時刻ではありません。

## 通信とセキュリティ

クライアントの接続先とサーバーの待受アドレスは別の設定です。

- Historyの既定URLを使う場合、Input Overlayプラグインのサーバーは`127.0.0.1:16899`で待ち受けるよう設定します。
- WebSocketの入力データは暗号化されません。ポートをPCの外部へ公開・転送しないでください。

詳しくは[セキュリティ情報](../SECURITY.md)を参照してください。

## 検証上の制約

- すべてのOBS環境での動作を保証するものではありません。
- 模擬イベントを使うブラウザテストと、実際のゲームパッドを使うOBS実機確認は異なります。
- Controllerの全ボタンはOBS上で網羅的に検証されていません。
- HistoryのOBS再起動後の設定保持とOBS上でのWebSocket再接続は未検証です。

自動テストの実行方法と検証範囲は、[テスト手順](testing.ja.md)を参照してください。
