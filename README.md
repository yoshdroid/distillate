# Distillate

Pyxel で作られた、水の流れを一時ブロックで誘導するグリッド型パズルゲームです。  
青い水と赤い水が異なる挙動で流れ、ステージごとの水源・排水・ゴール排水を使ってクリアを目指します。

## 現在の実装内容

- タイトル画面
  - ステージ選択
  - ゲーム開始
  - サウンドテストモード
- ゲーム画面
  - 水シミュレーション
  - ユーザブロック設置
  - 固定壁 / ユーザブロックの破壊
  - ステージクリア / True Clear 判定
- サウンド
  - 効果音
  - BGM
  - サウンドテストモードでの確認
- ステージ
  - 外部 `stage_*.dat` 読み込み
  - ステージごとのパラメータ上書き

## 動作環境

- Python 3.11 以降を推奨
- `pyxel`

インストール例:

```bash
pip install pyxel
```

## 起動方法

リポジトリ直下で実行します。

```bash
python main.py
```

## 操作方法

### タイトル画面

- `Left` / `Right`: ステージ選択
- `S`: サウンドテストモードへ移動
- `左クリック`: ゲーム開始
- `Q`: 終了

### ゲーム画面

- `左クリック`: 空マスならユーザブロック設置、壁や既存ユーザブロックなら破壊
- `左ドラッグ`: ユーザブロックを連続設置
- `W`: リスタート
  - 水を消去
  - ユーザブロックを消去
  - 破壊した固定壁を初期状態に戻す
- `Q`: タイトルへ戻る

### サウンドテスト

- `Up` / `Down`: 効果音選択
- `Enter` / `Space`: 選択中の効果音を 1 回再生
- `Left` / `Right`: BGM 選択
- `B`: BGM ON / OFF
- `Q`: タイトルへ戻る

## ゲームルール概要

- 水は各ステージの `2` タイルから生成されます
- 通常排水 `3` の近傍に入った水は消えます
- ゴール排水 `4` の近傍に入った水はクリア判定に使われます
- 青い水は停滞すると `stress` が蓄積し、一定値で赤い水に変化します
- 赤い水は青い水と位置交換しながら上昇しやすい特殊挙動を持ちます
- ステージ境界は上下左右でループ接続されています

## ステージファイル

ステージは [`distillate_stages/`](./distillate_stages) 配下の `stage_*.dat` として管理します。

### マップ記号

- `0`: 空白
- `1`: 壁
- `2`: 水源
- `3`: 通常排水
- `4`: ゴール排水

### サイズ

- 31 列 x 23 行

### 上書き可能なパラメータ

- `MAX_WATER`
- `MAX_STRESS`
- `BLOCK_LIFE`
  - `-1` を指定すると、ユーザ設置ブロックは消えません
- `STAGE_GOAL`
- `CLEAR_RATE`
- `INITIAL_RED_CHANCE`

### 記述例

```text
1000000000000000000000000000001
0111111111111111111111111111110
0100000000000002000000000000010
...
MAX_WATER=400
MAX_STRESS=100
BLOCK_LIFE=300
STAGE_GOAL=200
CLEAR_RATE=0.5
INITIAL_RED_CHANCE=0.05
```

## 主要な設定

[`distillate/config.py`](./distillate/config.py) で全体設定を管理しています。

- `WATER_SPEED`
- `MAX_WATER`
- `MAX_STRESS`
- `BLOCK_LIFE`
- `LATERAL_FLOW_SEARCH_DEPTH`
- `ENABLE_DIAGONAL_FALL`
- `UPWARD_SPLASH_CHANCE`
- `INITIAL_RED_CHANCE`
- `RESET_COOLDOWN_FRAMES`

## ディレクトリ構成

```text
main.py
distillate/
  app.py
  config.py
  input.py
  models.py
  renderer.py
  simulation.py
  sound.py
  stage.py
distillate_stages/
  stage_1.dat
  ...
```

## モジュール概要

- `main.py`
  - 起動入口
- `distillate/app.py`
  - シーン管理、入力処理、アプリ全体の統合
- `distillate/simulation.py`
  - 水 / ブロック / クリア判定のシミュレーション本体
- `distillate/stage.py`
  - ステージ読み込みとパラメータ解析
- `distillate/renderer.py`
  - タイトル / ゲーム / サウンドテストの描画
- `distillate/sound.py`
  - 効果音 / BGM の管理
- `distillate/models.py`
  - 水粒子とユーザブロックのデータモデル
- `distillate/input.py`
  - ドラッグ設置用の補助処理

## 補足

- 詳細な開発履歴は [`ChangeLog.md`](./ChangeLog.md) にあります
- 元の試作コードは [`original/distillate.py`](./original/distillate.py) に残しています
