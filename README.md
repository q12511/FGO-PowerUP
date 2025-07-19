# FGO Craft Essence Auto Enhancement Tool

FGO（Fate/Grand Order）の概念礼装を自動で強化するPythonツールです。画像認識技術とADB（Android Debug Bridge）を使用して、ゲーム内の強化プロセスを自動化します。

## 機能

- **自動強化**: 概念礼装の自動強化プロセス
- **画像認識**: OpenCVを使用したゲーム画面の状態判定
- **安全操作**: 人間らしいランダムな操作パターンで検出リスクを最小化
- **エラー処理**: 包括的なエラーハンドリングと回復機能
- **ログ記録**: 詳細な操作ログと進行状況の追跡

## 必要条件

### システム要件

- Python 3.8以上
- Android Debug Bridge (ADB)
- Androidデバイス（USBデバッグ有効）

### Pythonライブラリ

```bash
pip install -r requirements.txt
```

必要なライブラリ：
- opencv-python>=4.5.0
- numpy>=1.21.0
- Pillow>=8.0.0
- pynput>=1.7.0

## セットアップ

### 1. ADBの設定

1. Android SDK Platform Toolsをインストール
2. Androidデバイスでデベロッパーオプションを有効化
3. USBデバッグを有効化
4. デバイスをPCに接続

デバイス接続確認：
```bash
adb devices
```

### 2. テンプレート画像の準備

`templates/` ディレクトリに以下のテンプレート画像を配置：

- `main_menu.png` - メイン画面
- `craft_essence_list.png` - 概念礼装一覧
- `enhancement_screen.png` - 強化画面
- `material_selection.png` - 素材選択画面
- `enhancement_confirm.png` - 強化確認画面
- `enhancement_result.png` - 強化結果画面
- `enhance_button.png` - 強化ボタン
- `confirm_button.png` - 確認ボタン
- その他必要なUI要素

### 3. 設定ファイルの編集

`config.json` ファイルを編集して環境に合わせて設定：

```json
{
  "device": {
    "device_id": null,
    "screen_resolution": [1080, 2340]
  },
  "safety": {
    "emergency_stop_key": "f12",
    "min_wait_time": 0.5,
    "max_wait_time": 2.0
  }
}
```

## 使用方法

### 基本的な使用方法

```bash
python main.py --target-level 100 --max-attempts 50
```

### コマンドラインオプション

- `--config, -c`: 設定ファイルのパス（デフォルト: config.json）
- `--device-id, -d`: 使用するADBデバイスID
- `--target-level, -l`: 目標レベル（デフォルト: 100）
- `--max-attempts, -a`: 最大試行回数（デフォルト: 50）
- `--target-ce`: 対象の概念礼装名
- `--test-connection`: デバイス接続テスト
- `--test-templates`: テンプレート読み込みテスト
- `--diagnostics`: 診断実行

### テストモード

デバイス接続テスト：
```bash
python main.py --test-connection
```

テンプレート読み込みテスト：
```bash
python main.py --test-templates
```

システム診断：
```bash
python main.py --diagnostics
```

## 安全機能

### 検出回避機能

- **ランダム待機**: 操作間にランダムな待機時間を挿入
- **座標ランダム化**: タッチ位置に±10px程度のオフセットを適用
- **操作間隔変動**: 連続操作の間隔にばらつきを持たせる
- **定期休憩**: 一定回数の操作後に自動休憩

### 緊急停止

- デフォルトキー: F12
- キーボード割り込み: Ctrl+C
- 異常検出時の自動停止

## ログとデバッグ

### ログファイル

- メインログ: `fgo_enhancement.log`
- デバッグ画像: `debug_images/` （設定で有効化）

### ログレベル

- DEBUG: 詳細なデバッグ情報
- INFO: 一般的な情報（デフォルト）
- WARNING: 警告メッセージ
- ERROR: エラーメッセージ

## トラブルシューティング

### よくある問題

1. **デバイスが見つからない**
   ```
   adb devices
   ```
   でデバイスが表示されることを確認

2. **画面キャプチャに失敗**
   - USBデバッグの権限を確認
   - デバイスのロックを解除

3. **テンプレートマッチングに失敗**
   - 画面解像度の確認
   - テンプレート画像の品質を確認
   - 閾値の調整

4. **権限エラー**
   - ADBの権限を確認
   - デバイスの認証状態を確認

### デバッグモード

詳細なデバッグ情報を取得するには：

```json
{
  "logging": {
    "log_level": "DEBUG"
  },
  "template": {
    "save_debug_images": true
  }
}
```

## 注意事項

### 利用規約

- 本ツールはゲームの利用規約に違反する可能性があります
- 使用は自己責任で行ってください
- アカウントBANのリスクがあります

### 推奨事項

- 長時間の連続使用は避ける
- 定期的な手動操作を混ぜる
- 異常を感じたら即座に停止

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能要望は、GitHubのIssuesにお願いします。

## 免責事項

このツールの使用により生じたいかなる損害についても、開発者は責任を負いません。ゲームの利用規約を遵守し、自己責任でご利用ください。