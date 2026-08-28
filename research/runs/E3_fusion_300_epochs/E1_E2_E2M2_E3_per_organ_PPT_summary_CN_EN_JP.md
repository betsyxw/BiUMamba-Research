# Per-organ Ablation Summary for Midterm Presentation

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

> Reading rule: Dice ↑ is better; HD95 ↓ is better. `pp` means percentage points.

## 中文版

### E1 → E2：只保留行方向的前向/反向扫描

- Dice仅肝脏上升（`+0.37 pp`），其余7个器官下降。
- 下降最大：胃（`-5.86 pp`）、胰腺（`-2.70 pp`）、右肾（`-1.34 pp`）、左肾（`-1.23 pp`）。
- 右肾HD95恶化`+33.57`，说明边界稳定性明显下降。
- 结论：问题不是简单地“方向数量减少”，而是丢失垂直方向后，二维空间覆盖不足。

### E2 → E2_modify_2：通过通道分组恢复水平与垂直覆盖

- 6/8器官Dice上升：主动脉、左肾、右肾、胰腺、脾脏、胃。
- 恢复最明显：胃（`+4.95 pp`）、右肾（`+3.14 pp`）、脾脏（`+2.16 pp`）。
- 右肾HD95改善`-39.96`，边界错误被大幅修复。
- 胆囊和肝脏Dice仅轻微下降，分别为`-0.14 pp`和`-0.12 pp`。
- 结论：保持二维覆盖比单纯保留两个方向更加重要。

### E2_modify_2 → E3：固定融合改为静态可学习融合

- 胰腺（`+3.40 pp`）和胃（`+0.96 pp`）Dice上升。
- 其余6个器官Dice下降，左肾、右肾和主动脉下降最明显。
- 右肾HD95恶化`+24.61`；胰腺和胃虽然Dice提高，但HD95同时变差。
- 结论：静态权重能够偏向某些器官，但不能适应不同病例和不同器官，不足以取代固定融合。

### 一句话故事

E2的失败揭示了垂直覆盖的重要性；E2_modify_2恢复二维覆盖后取得当前最好结果；E3证明仅增加静态权重并不足够，因此下一步需要检验输入依赖的E4 Adaptive Gate。

## English version

### E1 → E2: Row-only forward/backward scanning

- Dice improved for only the liver (`+0.37 pp`) and decreased for the other seven organs.
- The largest drops occurred in the stomach (`-5.86 pp`), pancreas (`-2.70 pp`), right kidney (`-1.34 pp`) and left kidney (`-1.23 pp`).
- Right-kidney HD95 deteriorated by `+33.57`, indicating unstable boundary localization.
- Interpretation: the degradation was caused not simply by using fewer directions, but by losing vertical spatial coverage.

### E2 → E2_modify_2: Restoring horizontal and vertical coverage

- Dice improved for six of eight organs: aorta, left kidney, right kidney, pancreas, spleen and stomach.
- The largest recoveries were observed in the stomach (`+4.95 pp`), right kidney (`+3.14 pp`) and spleen (`+2.16 pp`).
- Right-kidney HD95 improved by `-39.96`.
- Gallbladder and liver Dice decreased only slightly (`-0.14 pp` and `-0.12 pp`).
- Interpretation: preserving two-dimensional coverage is more important than simply reducing the number of scan directions.

### E2_modify_2 → E3: Static learnable fusion

- Pancreas (`+3.40 pp`) and stomach (`+0.96 pp`) Dice improved.
- Dice decreased for the other six organs, particularly the left kidney, right kidney and aorta.
- Right-kidney HD95 deteriorated by `+24.61`. Pancreas and stomach gained Dice but lost boundary accuracy.
- Interpretation: static weights can favor selected organs, but cannot adapt reliably across organs and cases.

### Take-home message

The failure of E2 revealed the importance of vertical coverage. E2_modify_2 restored two-dimensional coverage and achieved the best current result. E3 showed that static weighting alone is insufficient, motivating E4 with an input-dependent adaptive gate.

## 日本語版

### E1 → E2：行方向のみの順方向・逆方向走査

- Diceが向上したのは肝臓（`+0.37 pp`）のみで、残り7臓器では低下した。
- 特に胃（`-5.86 pp`）、膵臓（`-2.70 pp`）、右腎（`-1.34 pp`）、左腎（`-1.23 pp`）で低下が大きかった。
- 右腎のHD95は`+33.57`悪化し、境界推定の不安定性が確認された。
- 解釈：性能低下の主因は単なる走査方向数の削減ではなく、垂直方向の空間カバレッジの欠如である。

### E2 → E2_modify_2：水平・垂直方向のカバレッジを回復

- 8臓器中6臓器（大動脈、左腎、右腎、膵臓、脾臓、胃）でDiceが向上した。
- 改善が大きかったのは胃（`+4.95 pp`）、右腎（`+3.14 pp`）、脾臓（`+2.16 pp`）である。
- 右腎のHD95は`-39.96`改善した。
- 胆嚢と肝臓のDice低下は、それぞれ`-0.14 pp`、`-0.12 pp`と小さかった。
- 解釈：走査方向数を減らすことよりも、二次元空間カバレッジを維持することが重要である。

### E2_modify_2 → E3：静的学習可能融合

- 膵臓（`+3.40 pp`）と胃（`+0.96 pp`）ではDiceが向上した。
- 一方、残り6臓器ではDiceが低下し、特に左腎、右腎、大動脈で低下が目立った。
- 右腎のHD95は`+24.61`悪化した。膵臓と胃ではDiceが向上したものの、境界精度は低下した。
- 解釈：静的重みは一部の臓器には有効であるが、症例や臓器ごとの違いに十分適応できない。

### まとめ

E2の失敗から垂直方向カバレッジの重要性が明らかになった。E2_modify_2は二次元カバレッジを回復し、現時点で最良の結果を達成した。E3により静的重み付けだけでは不十分であることが示され、入力依存型Adaptive Gateを用いるE4の必要性が導かれた。

## Recommended PPT layout

Use one slide with three columns:

1. **E1 → E2: Coverage loss** — red downward arrows for seven organs.
2. **E2 → E2_modify_2: Coverage recovery** — green upward arrows for six organs.
3. **E2_modify_2 → E3: Static fusion limitation** — highlight pancreas/stomach gains and right-kidney boundary deterioration.

Footer message:

> Coverage preservation is the key structural factor; static fusion alone is insufficient, motivating input-dependent adaptive fusion.
