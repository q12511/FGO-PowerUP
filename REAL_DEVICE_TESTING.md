# FGO自動強化ツール - 実機テスト手順

## 概要
このガイドでは、実際のAndroidデバイスでFGO自動強化ツールをテストする手順を説明します。

## 前提条件チェックリスト

### ✅ ハードウェア要件
- [ ] Androidデバイス（実機またはエミュレータ）
- [ ] USBケーブル（データ転送対応）
- [ ] PC（Windows/Mac/Linux）

### ✅ ソフトウェア要件
- [ ] FGOアプリがインストール済み
- [ ] ADB（Android Debug Bridge）がインストール済み
- [ ] Python 3.8以上
- [ ] 本ツールの依存関係インストール済み

### ✅ 設定要件
- [ ] Androidの開発者オプション有効化
- [ ] USBデバッグ有効化
- [ ] デバイス認証完了

## Phase 1: 環境セットアップ

### Step 1: 依存関係のインストール
```bash
# 必要なライブラリをインストール
pip install -r requirements.txt

# インストール確認
python -c "import cv2, numpy, PIL; print('Dependencies OK')"
```

### Step 2: ADB接続確認
```bash
# デバイス一覧確認
adb devices

# 期待される出力例:
# List of devices attached
# ABC123DEF456    device
```

**⚠️ 問題がある場合:**
- デバイスが表示されない → USBデバッグ設定を確認
- `unauthorized` → デバイスでPC認証を許可
- `adb command not found` → ADBをPATHに追加

### Step 3: 基本動作確認
```bash
# 画面キャプチャテスト
adb shell screencap -p /sdcard/test.png
adb pull /sdcard/test.png .

# 成功すればtest.pngが作成される
```

## Phase 2: テンプレート画像作成

### Step 1: FGOを起動
1. FGOアプリを起動
2. ログイン完了まで待機
3. ターミナル/メイン画面を表示

### Step 2: デバッグツールで現在状態を確認
```bash
# 現在の画面状態を分析
python debug_screen.py
```

**出力例:**
```
=== FGO Screen Debug Tool ===
✅ Connected to device: ABC123DEF456
✅ Screen captured: (2340, 1080, 3)
Detected state: MAIN_MENU
⚠️ No templates found in templates/ directory
```

### Step 3: 必要なテンプレート画像を段階的に作成

#### 優先度1: ナビゲーション用テンプレート

1. **main_menu.png** の作成
   ```bash
   # メイン画面でキャプチャ
   python debug_screen.py
   # debug_images/タイムスタンプ_current_screen.png を確認
   # 特徴的な部分を切り出してtemplates/main_menu.pngとして保存
   ```

2. **テンプレート検証**
   ```bash
   # 作成したテンプレートをテスト
   python debug_template.py main_menu
   ```

3. **enhancement_menu_button.png** の作成
   - メニューを開いて「強化」ボタンを表示
   - 同様の手順で作成・検証

#### 段階的な作成順序
1. `main_menu.png` → メイン画面識別
2. `enhancement_menu_button.png` → 強化メニューへの遷移
3. `enhancement_menu.png` → 強化メニュー画面識別
4. `ce_enhancement_button.png` → 概念礼装強化選択
5. 以降、ゲームフローに沿って順次作成

## Phase 3: 段階的テスト

### Step 1: テンプレート読み込みテスト
```bash
# テンプレートの読み込み状況確認
python main.py --test-templates
```

**成功例:**
```
Template validation summary: {'total': 15, 'existing': 8, 'missing': 7, 'required_missing': 0}
✅ Template test successful
```

### Step 2: デバイス接続テスト
```bash
# ADB接続とスクリーンキャプチャテスト
python main.py --test-connection
```

**成功例:**
```
Connected devices: ['ABC123DEF456']
✅ Device connection test successful
Screen capture test successful: (2340, 1080, 3)
```

### Step 3: 診断テスト
```bash
# 全体的なシステム診断
python main.py --diagnostics
```

**成功例:**
```
Diagnostics results: {
    'config_valid': True, 
    'device_connected': True, 
    'templates_loaded': True, 
    'safety_manager_active': True
}
✅ All diagnostics passed
```

## Phase 4: 段階的実行テスト

### Step 1: 画面遷移テストのみ
最初は強化を実行せず、画面遷移のみテスト

**安全なテスト設定:**
```json
// config.json
{
  "enhancement": {
    "target_level": 2,  // 低いレベルに設定
    "max_attempts": 1   // 1回のみに制限
  },
  "safety": {
    "emergency_stop_key": "f12",
    "test_mode": true     // テストモード（実際の強化を停止）
  }
}
```

### Step 2: ドライランテスト
```bash
# テストモードで実行（実際には強化しない）
python main.py --target-level 2 --max-attempts 1
```

**期待される動作:**
1. メイン画面認識
2. 強化メニューへの遷移
3. 概念礼装強化画面への遷移
4. （テストモードで停止）

### Step 3: 単一概念礼装での実際の強化テスト
⚠️ **重要**: 不要な概念礼装で最初はテスト

```bash
# 実際の強化テスト（慎重に）
python main.py --target-level 5 --max-attempts 1
```

## Phase 5: トラブルシューティング

### よくある問題と解決方法

#### 1. 画面状態の誤認識
**症状**: `UNKNOWN` 状態が続く
```bash
# 現在の画面を詳細分析
python debug_screen.py

# 特定テンプレートの精度確認
python debug_template.py main_menu --threshold 0.6
```

**解決方法**:
- テンプレート画像を再作成
- より特徴的な部分を含める
- 閾値を調整（0.6-0.8で試行）

#### 2. ボタン検出の失敗
**症状**: ボタンが見つからない
```bash
# ボタンテンプレートの詳細分析
python debug_template.py enhancement_menu_button
```

**解決方法**:
- ボタンの状態確認（有効/無効、色の変化）
- 周囲の背景を含めて再作成
- 複数の状態のテンプレートを作成

#### 3. 素材選択の問題
**症状**: 素材が検出されない、誤選択
```bash
# 素材選択画面で状態確認
python debug_screen.py
```

**解決方法**:
- `ce_material.png` と `ce_material_selected.png` を精密に作成
- 緑枠の色を正確に含める
- 複数の概念礼装タイプでテスト

#### 4. 強化実行の失敗
**症状**: 強化ボタンが押されない
- 確認ダイアログの検出失敗
- 結果画面の認識失敗

**解決方法**:
- 各段階でdebug_screen.pyを実行
- 画面遷移のタイミングを調整
- 待機時間を増やす

### デバッグ手順

#### 問題発生時の標準手順
1. **現在状態の確認**
   ```bash
   python debug_screen.py
   ```

2. **問題のテンプレートを特定**
   ```bash
   python debug_template.py [問題のテンプレート名]
   ```

3. **ログの確認**
   ```bash
   tail -f fgo_enhancement.log
   ```

4. **テンプレート再作成**
   - 問題の画面で新しいスクリーンショット
   - より適切な範囲で切り出し
   - 再テスト

## Phase 6: 運用テスト

### Step 1: 継続実行テスト
```bash
# 複数回の強化テスト
python main.py --target-level 10 --max-attempts 5
```

### Step 2: エラー回復テスト
- 意図的にエラー状況を作成
- 緊急停止機能の確認
- 回復処理の動作確認

### Step 3: 長時間実行テスト
```bash
# より長時間の安定性テスト
python main.py --target-level 50 --max-attempts 20
```

## 安全対策

### ⚠️ 重要な注意事項

1. **緊急停止**: F12キーで即座に停止可能
2. **テスト用アカウント**: 可能であればサブアカウントでテスト
3. **貴重な概念礼装**: 最初は不要なもので実験
4. **バックアップ**: 重要なデータは事前にバックアップ

### 推奨設定
```json
{
  "safety": {
    "emergency_stop_key": "f12",
    "min_wait_time": 1.0,    // 待機時間を長めに
    "max_wait_time": 3.0,
    "max_continuous_errors": 3  // エラー時の早期停止
  }
}
```

## 成功の指標

### ✅ テスト完了チェックリスト

#### Phase 1-2: セットアップ
- [ ] 全依存関係インストール完了
- [ ] ADB接続安定
- [ ] 必要なテンプレート画像作成完了

#### Phase 3: 基本テスト
- [ ] `--test-connection` 成功
- [ ] `--test-templates` 成功
- [ ] `--diagnostics` 全項目パス

#### Phase 4: 機能テスト
- [ ] 画面状態正常認識
- [ ] ナビゲーション正常動作
- [ ] 素材選択正常動作
- [ ] 強化実行正常完了

#### Phase 5: 安定性テスト
- [ ] 連続実行安定
- [ ] エラー回復正常
- [ ] 緊急停止正常動作

## 次のステップ

実機テスト完了後:
1. **設定の最適化**: 待機時間、閾値の調整
2. **運用ルール策定**: 使用時間、頻度の決定
3. **監視体制**: ログ監視、異常検知の準備
4. **継続的改善**: テンプレート精度向上、新機能追加

---

**⚠️ 最終確認**
このツールはゲームの利用規約に抵触する可能性があります。使用は自己責任で行い、適切な判断の下で利用してください。