# Beers / EvoGarden

現状は **2系統** で動きます。

1. **Python版**（ローカル向け）
   - `python simulation.py --ticks 1000` でCSV検証
   - `python simulation.py --render` でTkinter描画（GUI環境のみ）
2. **Web版**（GitHub Pages公開向け）
   - `web/` 配下の静的サイト（Canvas描画、近未来デザイン）

---

## ローカル実行

### Python（ヘッドレス）

```bash
python simulation.py --ticks 1000
```

### Python（GUI描画）

```bash
python simulation.py --render
```

### Webデモ

```bash
python -m http.server 8000
# ブラウザで http://localhost:8000/web/
```

---

## GitHub Pages でWeb公開

このリポジトリには `web/` を公開する workflow を追加済みです（`.github/workflows/pages.yml`）。

### 手順

1. GitHub の `Settings > Pages > Build and deployment` を開く
2. Source を **GitHub Actions** にする
3. `main`（または運用ブランチ）へ push
4. Actions の `Deploy GitHub Pages` が成功すると公開URLが発行される

---

## Web操作

- `Pause/Resume`: シミュレーション停止/再開
- `Inject Nutrition`: 栄養注入
- `Meteor`: 隕石イベント
- `Disease`: 疫病イベント

---

## モジュール構成（Python）

- `world.py`: トーラス距離・座標wrap
- `terrain.py`: 高低マップ、生産性、傾斜
- `nutrition.py`: ロジスティック成長 + 拡散
- `spatial_hash.py`: 近傍探索用の空間ハッシュ
- `creature.py`: 個体状態、遺伝子→表現型
- `behaviors.py`: 行動、捕食、繁殖、代謝
- `simulation.py`: 更新ループ + CLI
- `logging.py`: ログ収集とCSV出力
- `ui.py`: 神の介入 + Tkinterレンダラー
