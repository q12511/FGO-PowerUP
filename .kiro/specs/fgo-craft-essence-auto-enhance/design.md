# Design Document

## Overview

FGO概念礼装自動強化ツールは、Pythonベースの画像認識とADB（Android Debug Bridge）を組み合わせたAndroidデバイス制御アプリケーションです。OpenCVを使用した画像認識でゲーム画面の状態を判定し、ADBコマンドを使用してAndroidデバイス上のタッチ操作を自動実行します。安全性を重視し、人間らしい操作パターンを実装することで検出リスクを最小化します。

## Architecture

### システム構成

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Main App      │    │  ADB Manager    │    │  Image Analysis │
│                 │───▶│                 │───▶│                 │
│ - 設定管理       │    │ - デバイス接続   │    │ - テンプレート   │
│ - 実行制御       │    │ - スクリーン     │    │   マッチング     │
│ - ログ出力       │    │   キャプチャ     │    │ - 状態判定       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                              │
         ▼                                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Touch Controller│    │  Safety Manager │    │  Config Manager │
│                 │    │                 │    │                 │
│ - タッチ実行     │    │ - 待機時間制御   │    │ - 設定保存       │
│ - 座標計算       │    │ - オフセット     │    │ - デバイス設定   │
│ - ランダム化     │    │ - 異常検出       │    │ - テンプレート   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### データフロー

1. **初期化**: ADBデバイス接続確認、設定ファイル読み込み、テンプレート画像ロード
2. **画面監視**: ADB screencapコマンドによる定期的なスクリーンキャプチャと状態判定
3. **操作実行**: 認識結果に基づくADB inputコマンドでのタッチ操作
4. **安全制御**: ランダム待機とタッチ座標オフセット適用
5. **ログ記録**: 全操作の詳細ログ出力

## Components and Interfaces

### 1. ADBManager クラス

```python
class ADBManager:
    def __init__(self, device_id: Optional[str] = None)
    def connect_device(self) -> bool
    def get_connected_devices(self) -> List[str]
    def capture_screen(self) -> np.ndarray
    def execute_command(self, command: str) -> str
    def is_device_connected(self) -> bool
```

**責任**: ADBデバイス接続管理とコマンド実行

### 2. ImageAnalyzer クラス

```python
class ImageAnalyzer:
    def __init__(self, template_dir: str)
    def load_templates(self) -> Dict[str, np.ndarray]
    def find_template(self, screen: np.ndarray, template_name: str, threshold: float = 0.8) -> Optional[Tuple[int, int]]
    def detect_game_state(self, screen: np.ndarray) -> GameState
    def find_enhancement_materials(self, screen: np.ndarray) -> List[Tuple[int, int]]
```

**責任**: 画像認識とゲーム状態の判定

### 3. TouchController クラス

```python
class TouchController:
    def __init__(self, adb_manager: ADBManager, safety_manager: SafetyManager)
    def tap_at(self, x: int, y: int, randomize: bool = True) -> None
    def swipe(self, start: Tuple[int, int], end: Tuple[int, int], duration: int = 300) -> None
    def long_press(self, x: int, y: int, duration: int = 1000) -> None
    def wait_random(self, min_sec: float = 0.5, max_sec: float = 2.0) -> None
```

**責任**: ADBを使用したタッチ操作の実行とランダム化

### 4. SafetyManager クラス

```python
class SafetyManager:
    def __init__(self, config: SafetyConfig)
    def get_random_offset(self, max_offset: int = 10) -> Tuple[int, int]
    def get_random_wait_time(self, base_time: float, variance: float = 0.3) -> float
    def is_safe_to_continue(self) -> bool
    def detect_anomaly(self, screen: np.ndarray) -> bool
```

**責任**: 安全な操作パターンの生成と異常検出

### 5. EnhancementController クラス

```python
class EnhancementController:
    def __init__(self, config: EnhancementConfig)
    def start_enhancement(self, target_level: int, max_attempts: int) -> None
    def select_materials(self) -> bool
    def execute_enhancement(self) -> EnhancementResult
    def check_completion_conditions(self) -> bool
```

**責任**: 強化プロセス全体の制御と管理

## Data Models

### GameState 列挙型

```python
class GameState(Enum):
    UNKNOWN = "unknown"
    MAIN_MENU = "main_menu"
    CRAFT_ESSENCE_LIST = "craft_essence_list"
    ENHANCEMENT_SCREEN = "enhancement_screen"
    MATERIAL_SELECTION = "material_selection"
    ENHANCEMENT_CONFIRM = "enhancement_confirm"
    ENHANCEMENT_RESULT = "enhancement_result"
    ERROR_STATE = "error_state"
```

### EnhancementConfig データクラス

```python
@dataclass
class EnhancementConfig:
    target_craft_essence: str
    target_level: int
    max_attempts: int
    material_priority: List[str]
    safety_settings: SafetyConfig
    device_id: Optional[str]
    screen_resolution: Tuple[int, int]
```

### SafetyConfig データクラス

```python
@dataclass
class SafetyConfig:
    min_wait_time: float = 0.5
    max_wait_time: float = 2.0
    tap_offset_range: int = 10
    operation_variance: float = 0.3
    anomaly_detection: bool = True
    emergency_stop_key: str = "F12"
    swipe_duration_range: Tuple[int, int] = (200, 500)
```

### EnhancementResult データクラス

```python
@dataclass
class EnhancementResult:
    success: bool
    current_level: int
    exp_gained: int
    materials_used: List[str]
    error_message: Optional[str]
    timestamp: datetime
```

## Error Handling

### エラー分類と対処

1. **画像認識エラー**
   - テンプレートマッチング失敗
   - 対処: 複数解像度テンプレートの試行、閾値調整

2. **操作実行エラー**
   - ADBコマンド実行失敗、タッチ座標の計算失敗
   - 対処: デバイス接続確認、座標の再計算、安全範囲内での再試行

3. **ゲーム状態エラー**
   - 予期しない画面遷移
   - 対処: 状態リセット、メイン画面への復帰

4. **システムエラー**
   - ADBデバイス接続失敗、権限不足、メモリ不足
   - 対処: デバイス再接続、USB デバッグ確認、リソース解放

### ログ出力仕様

```python
# ログレベル設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fgo_enhancement.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
```

## Testing Strategy

### 単体テスト

- **ADBManager**: デバイス接続とコマンド実行
- **ImageAnalyzer**: モックスクリーンショットでのテンプレートマッチング
- **TouchController**: 座標計算とランダム化ロジック
- **SafetyManager**: 待機時間とオフセット生成
- **EnhancementController**: 状態遷移ロジック

### 統合テスト

- **ADB接続フロー**: デバイス検出→接続→スクリーンキャプチャ
- **画面認識フロー**: キャプチャ→解析→判定の一連の流れ
- **操作実行フロー**: 認識→タッチ→待機の自動化サイクル
- **エラーハンドリング**: デバイス切断や異常状態での適切な処理

### 実機テスト

- **複数デバイス対応**: 異なるAndroidデバイスでの動作確認
- **複数解像度対応**: 1920x1080, 1440x2560, 1080x2340での動作確認
- **長時間動作**: 連続1時間以上の安定動作
- **安全性検証**: 人間らしいタッチ操作パターンの確認

### テストデータ

- **テンプレート画像**: 各ゲーム状態のスクリーンショット
- **モック設定**: 様々な強化条件の設定ファイル
- **エラーケース**: 異常画面や接続エラーのシミュレーション