# Beers / EvoGarden v0.1

トーラス世界上で、栄養フィールド・雌雄繁殖・遺伝・密度依存を扱う最小シミュレーション実装です。

## 実行

```bash
python simulation.py
```

実行後、ログCSVが `outputs/sim_log.csv` に生成されます。

## モジュール構成

- `world.py`: トーラス距離・座標wrap
- `terrain.py`: 高低マップ、生産性、傾斜
- `nutrition.py`: ロジスティック成長 + 拡散
- `spatial_hash.py`: 近傍探索用の空間ハッシュ
- `creature.py`: 個体状態、遺伝子→表現型
- `behaviors.py`: 行動、捕食、繁殖、代謝
- `simulation.py`: 更新ループ
- `logging.py`: ログ収集とCSV出力
- `ui.py`: 神の介入（栄養注入・疫病・隕石）
