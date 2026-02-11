# Beers / EvoGarden v0.1

トーラス世界上で、栄養フィールド・雌雄繁殖・遺伝・密度依存を扱うシミュレーションです。

## 実行

### 1) ヘッドレス（CSV検証）

```bash
python simulation.py --ticks 1000
```

### 2) 描画あり（近未来デザイン）

```bash
python simulation.py --visualize --tick-per-frame 2 --width 1200 --height 900
```

- 栄養フィールド：ネオン調ヒートマップ
- 草食：シアン系、肉食：マゼンタ系
- HUD：個体数・tick・栄養総量
- 操作: `Space` で一時停止、`Q` or `Esc` で終了

実行後、ログCSVが `outputs/sim_log.csv` に生成されます。

## モジュール構成

- `world.py`: トーラス距離・座標wrap
- `terrain.py`: 高低マップ、生産性、傾斜
- `nutrition.py`: ロジスティック成長 + 拡散
- `spatial_hash.py`: 近傍探索用の空間ハッシュ
- `creature.py`: 個体状態、遺伝子→表現型
- `behaviors.py`: 行動、捕食、繁殖、代謝
- `simulation.py`: 更新ループとCLI
- `renderer.py`: Tkinter可視化（近未来UI）
- `logging.py`: ログ収集とCSV出力
- `ui.py`: 神の介入（栄養注入・疫病・隕石）
