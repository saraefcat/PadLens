# Controller Overlay

[English](README.md) · [PadLens](../README.ja.md)

## 概要

OBS StudioのInput Overlayソースで、ゲームパッドの現在の入力を透過画像に表示します。PadLens独自のコンポーネントであり、メーカーやプラグインの公式スキンではありません。

## 表示例

<a href="../docs/images/controller-preview.png"><img src="../docs/images/controller-preview.png" alt="合成背景上のController表示" width="600"></a>

これは合成プレビューであり、実際の配信画面の撮影ではありません。画像を選ぶと元画像を開けます。

## 動作確認済み環境・推奨設定

OBS StudioとInput Overlayは別途導入してください。OBS Studio 33.0.0（ポータブル版）とInput Overlay 5.1.2の組み合わせで表示を確認しました。開発に使用したOSと、動作確認に使用した組み合わせは区別しています。ほかのバージョンや全物理操作の動作は未確認です。

| 項目 | 内容 |
| --- | --- |
| 開発に使用したOS | Windows 10 / Windows 11 |
| 新規利用の推奨OS | Windows 11 |
| 動作確認に使用したOBS Studio | 33.0.0（ポータブル版） |
| 動作確認に使用したInput Overlay | 5.1.2 |

[Windows 10の通常サポートは終了](https://support.microsoft.com/en-us/windows/deployment/updates-lifecycle/windows-10-support-has-ended-on-october-14-2025)しているため、新規利用者向けの推奨OSには含めません。

## ファイル構成

いずれも`controller/`以下のファイルです。通常利用にはPython、Pillow、CairoSVGは不要です。

| ファイル | 用途 | 配布ZIP |
| --- | --- | --- |
| `controller_atlas.png` | 標準版の画像 | 含む |
| `controller_atlas_light.png` | 高透過版の画像 | 含む |
| `controller_layout.json` | 両画像で共通のInput Overlay配置 | 含む |
| `controller_atlas_sara.png` | Sara通常版の画像 | 含む |
| `controller_atlas_sara_rta.png` | Sara RTA版の画像 | 含む |
| `controller_layout_sara.json` | Sara版2画像で共通の配置 | 含む |
| `build_controller_overlay.py` | 開発者向けの画像生成 | 含まない |
| `verify_layout.py` | 開発者向けの画像・配置検査 | 含まない |
| `build_sara_overlay.py` | 開発者向けSara画像生成。PillowとCairoSVGが必要 | 含まない |
| `verify_sara_layout.py` | 開発者向けSara画像・配置検査。Pillowが必要 | 含まない |

## 導入方法

[詳しい導入手順](../docs/installation.ja.md)も参照してください。GitHubのソースまたはPadLens配布ZIPを取得したら、`controller/`のフォルダー構成を維持してください。最初はOBSのテスト用シーンで確認します。

1. OBSに**Input Overlayソース**を追加します。
2. ソースのプロパティで、`controller/`以下のPNGとJSONを次の組み合わせで指定します。

   | 表示 | PNG | JSON |
   | --- | --- | --- |
   | 標準版 | `controller_atlas.png` | `controller_layout.json` |
   | 高透過版 | `controller_atlas_light.png` | `controller_layout.json` |
   | Sara通常版 | `controller_atlas_sara.png` | `controller_layout_sara.json` |
   | Sara RTA版 | `controller_atlas_sara_rta.png` | `controller_layout_sara.json` |

3. Input Overlayソース側でゲームパッドを選び、入力に応じて表示が変わるか確認します。反応しない場合は、Input Overlayプラグインの設定でゲームパッドフックを確認してください。

各テーマのPNG2種類は、それぞれのテーマ用JSONを共用します。Sara版には猫耳のLB/RB、長円形のLT/RT、肉球スティック、猫目風のView/Menu、鼻と口のHOMEがあります。Sara版のOBS実機表示は未確認です。Controllerだけを使う場合、Input OverlayプラグインのWebSocketサーバーは不要です。

## 対応する入力

以下は配置JSONに定義された入力です。OBS上で全入力を網羅的に操作した結果ではありません。

| 入力 | 表示 |
| --- | --- |
| ABXY | 各ボタンの押下 |
| 十字キー | 上・下・左・右 |
| LB / RB | 左右のショルダーボタン |
| LT / RT | 左右のアナログトリガー |
| 左右スティック | 移動と位置 |
| L3 / R3 | 左右スティックの押し込み |
| View / Menu | 各ボタンの押下 |
| HOME | SDL GUIDEコード5の入力 |

## 問題解決

| 症状 | 最初に確認すること |
| --- | --- |
| Controller画像が表示されない | Input Overlayソースが追加され、PNGとJSONのパスが正しいか |
| ボタンを押しても表示が変化しない | ソース側のゲームパッド選択と、プラグイン設定側のゲームパッドフック |
| 一部のボタンが反応しない | 上の対応入力と、選んだデバイスの論理入力。背面追加ボタンには下記の制約がある |
| 表示位置がずれる | PNGに対応するテーマ用JSONを指定しているか |
| 透過版を切り替えたい | 同じテーマのもう一方のPNGに変更する。JSONはそのテーマ用を維持 |

詳しい確認方法は[導入手順](../docs/installation.ja.md)を参照してください。

## セキュリティ

- ゲームパッド表示に不要なキーボード・マウスフックは無効にしてください。
- OBSを管理者権限で起動する必要はありません。

詳しくは[セキュリティ情報](../SECURITY.md)を参照してください。

## 制約

背面追加ボタンは、対応する論理入力にリマップされた場合にのみ表示されます。OBSで全ボタン・トリガー・スティックを網羅的に操作する検証は、利用者による実施が必要です。合成プレビューは実配信での表示品質を証明しません。

## 開発者向け情報

画像を再生成する場合は、ソース一式でPython、Pillow、CairoSVGを用意し、`python controller/build_controller_overlay.py --output-dir PATH`で**新規または空の出力先**を明示します。スクリプトは配布済みPNG・JSONとREADMEの上書きを拒否します。フォント描画は生成環境によって異なるため、配布画像を置き換える前に表示を比較してください。

`controller/verify_layout.py`はPythonとPillowで配布PNGとJSONの寸法・配置を検査します。実行例は`python -X utf8 controller/verify_layout.py`です。この静的検査はOBS上での全入力の動作確認には代わりません。

Sara版の再生成は`python controller/build_sara_overlay.py --output-dir PATH`で新規または空の出力先を指定します。Sara版の静的検査は`python -X utf8 controller/verify_sara_layout.py`で実行できます。再生成時のフォント差異によって、完成版PNGとバイト一致しない場合があります。

## ライセンス

PadLens独自のコード、配置、PNG画像、HOME図形には[MIT License](../LICENSE)を適用します。著作権表示は`Copyright (c) 2026 saraefcat`です。OBS StudioとInput Overlayは別のソフトウェアです。
