# BiUMamba Research

[English](#english) | [日本語](#日本語)

**Research Author and Repository Maintainer:** xuwen

**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

**GitHub:** [@betsyxw](https://github.com/betsyxw)

Research-specific designs, experiment implementations, ablation records,
evaluation reports, and reproducibility documentation in this repository are
maintained by **xuwen**. The original VM-UNet/VMamba code remains attributed to
its upstream authors under the retained license. See [`AUTHORS.md`](AUTHORS.md).

## English

Private research repository for the master's project:

> **BiUMamba: Bidirectional Selective Scan with Adaptive Fusion and
> Natural-Image-Free Pre-training for Medical Image Segmentation**

Current experimental status:

- E1: original four-direction VM-UNet baseline — completed.
- E2: forward/reverse row-major scan with fixed sum — completed; below E1.
- E2_modify_1: alternating-axis bidirectional scan — 50-epoch screening completed.
- E2_modify_2: channel-grouped 2D bidirectional scan — 300-epoch validation completed; it recovered E2's lost accuracy and passed the Strong Green decision gate.
- E3: static learnable fusion on E2_modify_2 — 50-epoch screening and the full 300-epoch run completed; the final result did not outperform E2_modify_2.
- E4: constrained sample/channel adaptive gate on the same coverage-preserving structure — 50-epoch screening and 300-epoch full run completed; the full run was a Red result and exposed a screen/full reproducibility mismatch.
- E4 Version 2-B: separately named stabilized-gate ablation — deterministic A/A checks and a formal 50-epoch screening run completed. Training stability improved, but accuracy did not justify a 300-epoch extension.
- Datasets: Synapse first, ACDC second; FractalDB pre-training pilot follows the directional ablation.

### Training story and current evidence

E2 reduced the original four SS2D directions to row-major forward/reverse scans.
It reduced mean epoch time and peak memory, but Dice decreased from `80.05%` to
`78.61%` and HD95 worsened from `24.61` to `26.11`. This negative control
suggested that bidirectionality alone was insufficient because the transposed
vertical scan pair had been removed.

Two coverage-recovery variants were therefore implemented and tested under a
matched 50-epoch Synapse screening protocol (seed 42, batch size 32, 224x224
input, and the same initialization and optimization settings):

| Variant | Design | Mean Dice | Mean HD95 | Final loss | Mean epoch time | Peak memory |
|---|---|---:|---:|---:|---:|---:|
| E2_modify_1 | Alternating horizontal/vertical bidirectional blocks | 72.54% | **35.58** | 0.1478 | 213.81 s | **10,396 MiB** |
| E2_modify_2 | Channel-grouped horizontal/vertical bidirectional scan in every block | **75.07%** | 40.42 | **0.1307** | **170.71 s** | 11,016 MiB |

E2_modify_2 was selected for the first full 300-epoch validation because it
improved Dice by `2.53` percentage points, improved Dice in seven of eight
organs, reduced final loss, and trained about `20.16%` faster per epoch than
E2_modify_1. Its HD95 was `4.84` worse, so this is a provisional selection—not
evidence that the method is already superior. The 300-epoch run will determine
whether the boundary outliers persist after convergence. E1/E2 (300 epochs)
and E2_modify_1/E2_modify_2 (50 epochs) are not treated as directly comparable
final results.

### Converged 300-epoch comparison

The official comparison uses the archived checkpoint selected by each training
run. For E2_modify_2, the training script selected Epoch 297 by minimum training
loss; the resulting checkpoint achieved `80.2540%` Mean Dice and `21.9206`
Mean HD95.

| Experiment | Scan and fusion design | Checkpoint epoch | Mean Dice ↑ | Mean HD95 ↓ | Training time | Mean epoch time | Peak GPU memory |
|---|---|---:|---:|---:|---:|---:|---:|
| E1 | Original VM-UNet four-direction SS2D + fixed sum | 286 | 80.0488% | 24.6136 | 14 h 49 m | 177.86 s | 14,665 MiB |
| E2 | Row-major forward/backward + fixed sum | 299 | 78.6080% | 26.1111 | 13 h 42 m | 164.48 s | **10,747 MiB** |
| **E2_modify_2** | **Channel-grouped horizontal/vertical bidirectional scan + fixed sum** | **297** | **80.2540%** | **21.9206** | **13 h 05 m** | **157.06 s** | 11,016 MiB |
| E3 | Channel-grouped horizontal/vertical bidirectional scan + static learnable fusion | 286 | 80.0049% | 25.5669 | 11 h 35 m | **139.09 s** | 12,958 MiB |
| E4 Version 1 | Channel-grouped horizontal/vertical bidirectional scan + constrained adaptive gate | 285 | 70.9089% | 35.3190 | 9 h 49 m | **117.91 s** | 13,534 MiB |

Compared with E1, E2_modify_2 improved Dice by `0.2052` percentage points,
reduced HD95 by `2.6931` (`10.94%`), reduced training time by `11.69%`, and
reduced peak GPU memory by `24.88%`. Compared with E2, it recovered `1.6460`
Dice points and reduced HD95 by `4.1906`. This supports the interpretation that
E2 failed mainly because it removed vertical coverage, while the grouped-2D
design preserves two-dimensional context at lower cost than the original
four-direction implementation. These are single-seed results and are not yet a
statistical superiority claim.

The complete archive report, overall and per-organ CSV comparisons, and
structured manifest are available in
[`research/runs/e2_modify_2_synapse_seed42/`](research/runs/e2_modify_2_synapse_seed42/).

E3 reached `80.0049%` Mean Dice and `25.5669` Mean HD95 after 300 epochs.
Compared with E2_modify_2, Dice decreased by `0.2491` percentage points and
HD95 worsened by `3.6464`. Dice improved only for pancreas and stomach, while
six of eight organs decreased; right-kidney HD95 deteriorated from `31.5460`
to `56.1532`. The learned static weights remained close to equal fusion. E3 is
therefore retained as a negative/neutral ablation: preserving two-dimensional
coverage is the main structural gain, whereas input-independent static fusion
is insufficient. E2_modify_2 remains the current reference model.

The E3 full-run archive, five-experiment overall comparison, per-organ CSV,
manifest, and Chinese/English/Japanese presentation summary are available in
[`research/runs/E3_fusion_300_epochs/`](research/runs/E3_fusion_300_epochs/).

E4 Version 1 reached `70.9089%` Mean Dice and `35.3190` Mean HD95. Compared
with E2_modify_2, Dice decreased by `9.3451` percentage points and HD95
worsened by `13.3985`; all eight organs lost Dice. Although the mean epoch
time was `24.93%` shorter, peak memory increased by `22.86%`. Moreover, the
full run's Epoch-50 loss (`0.7409`) diverged sharply from the favorable
screening run (`0.1146`) despite matching logged settings. E4 is therefore a
negative ablation, and its initialization/determinism mismatch must be audited
before another full run. E2_modify_2 remains the current reference model.

The E4 archive, six-experiment overall comparison, eight-organ comparison and
manifest are available in
[`research/runs/E4_version_1_full300/`](research/runs/E4_version_1_full300/).

The subsequent deterministic A/A audit froze the E4 source and ran two matched
12-epoch trajectories. Both runs began from the same model hash and used the
same batch order at every epoch, yet their model and checkpoint hashes differed
from Epoch 1; the maximum loss difference was `0.042850100568` at Epoch 11.
The gate also reached the `tanh` limits of `-1` and `+1` during Epoch 1. This is
a Red result for bitwise reproducibility, not proof that adaptive fusion is
theoretically invalid. Formal E4 comparisons therefore require multiple seeds,
while gate stabilization must be tested as a separately named ablation. The
scripts, aggregate evidence, and decision record are archived in
[`research/runs/E4_determinism_AA/`](research/runs/E4_determinism_AA/).

E4 Version 2-B was then created as a separate stabilization ablation rather
than replacing Version 1. It uses a `0.1x` gate learning rate, five frozen gate
epochs, an alpha ramp from `0` to `0.25`, gradient clipping, equal-fusion
regularization, context normalization, and temperature scaling. Alpha was also
made persistent in checkpoints and verified by save/reload testing. The formal
50-epoch run completed normally with `74.9931%` Mean Dice, `37.9087` Mean
HD95, `97.81 s` mean epoch time, and `11,499.30 MiB` peak allocated memory.

This is a positive engineering-stability result but a negative/inconclusive
accuracy ablation. E4 Version 2-B reserved 433 of the 2,211 training slices for
held-out checkpoint selection, unlike the earlier experiments that trained on
all 2,211 slices. It therefore must not be ranked as a controlled architecture
comparison. A direct 300-epoch extension is not justified, and E2_modify_2
remains the current main model. The source snapshot, seven-experiment table,
eight-organ table, workbook, manifest, and negative-ablation analysis are in
[`research/runs/E4_v2_stabilized_b_epoch50/`](research/runs/E4_v2_stabilized_b_epoch50/).

### E3 50-epoch screening result

E3 replaces fixed-sum fusion on the E2_modify_2 grouped-2D structure with
static learnable fusion. Under the matched 50-epoch protocol, E3 achieved
`75.6773%` Mean Dice and `36.0624` Mean HD95, compared with `75.0737%` and
`40.4159` for E2_modify_2. Dice therefore improved by `0.6035` percentage
points and HD95 decreased by `4.3535`. Mean epoch time decreased from
`170.71 s` to `152.66 s`, while sampled peak memory increased from `11,016`
to `12,958 MiB`.

This is a short single-seed screening result, not a direct comparison with the
300-epoch E1/E2/E2_modify_2 results. The result supports running E3 for the
matched 300-epoch budget. Right-kidney Dice and the spleen HD95 outlier remain
explicit risks. The report and structured comparisons are archived in
[`research/runs/E3_fusion_50_epochs/`](research/runs/E3_fusion_50_epochs/).

Datasets, pretrained weights, checkpoints, NIfTI outputs and credentials are
intentionally excluded. See [`research/`](research/) for the experiment design,
environment lock and verified results.

## 日本語

**研究者・リポジトリ管理者：** xuwen

**GitHub：** [@betsyxw](https://github.com/betsyxw)

本リポジトリに含まれる研究固有の設計、実験実装、アブレーション記録、
評価レポートおよび再現性資料は、**xuwen**が管理しています。基盤となる
VM-UNet/VMambaのオリジナルコードの著作権およびクレジットは、保持されて
いるライセンスに従い原著者に帰属します。詳細は[`AUTHORS.md`](AUTHORS.md)
を参照してください。

本リポジトリは、修士研究として取り組む以下の研究課題のための非公開リポジトリです。

> **BiUMamba：医用画像セグメンテーションのための、適応的融合を備えた双方向選択的スキャンと自然画像を使用しない事前学習**

本研究では、Vision Mambaを基盤とする医用画像セグメンテーションモデルに対して、次の二つの研究課題を検証します。

1. 従来の走査方法を双方向スキャンへ拡張し、入力に応じて情報を統合するAdaptive Fusion Gateを導入することで、臓器の形状や長距離依存関係をより効果的に表現できるか。
2. ImageNetなどの自然画像を用いず、FractalDBによる事前学習が医用画像セグメンテーションに有効な初期表現を提供できるか。

### 実験の進捗

- **E1：Original** — VM-UNetのオリジナル4方向スキャンによるベースライン。完了。
- **E2：Bidirectional + Fixed Sum** — Row-majorのForward/Reverseを固定加算で融合。完了したがE1を下回った。
- **E2_modify_1** — 水平・垂直軸をブロックごとに交互に用いる双方向走査。50 epochのスクリーニング完了。
- **E2_modify_2** — 各ブロック内でチャネルを水平・垂直グループに分ける二次元双方向走査。300 epoch検証が完了し、E2で失われた精度を回復してStrong Green判定を満たした。
- **E3** — E2_modify_2を基盤とする静的学習可能融合。50 epochスクリーニングおよび300 epochのFull runが完了したが、最終結果はE2_modify_2を上回らなかった。
- **E4** — 同じ二次元被覆を維持したサンプル・チャネル依存Adaptive Gate。50 epochスクリーニングと300 epoch Full runが完了したが、Full runはRed判定となり、screen/full間の再現性不一致が確認された。
- **E4 Version 2-B** — E4 Version 1を上書きせず、独立した安定化Gateアブレーションとして作成。決定性A/A確認と50 epoch正式スクリーニングを完了した。学習安定性は改善したが、300 epochへ延長する精度上の根拠は得られなかった。

### 学習過程で得られた知見

E2では、4方向SS2DをRow-majorのForward/Reverseの2方向へ削減しました。
その結果、計算時間とGPUメモリは減少しましたが、Diceは80.05%から
78.61%へ低下し、HD95は24.61から26.11へ悪化しました。この負の結果は、
双方向性だけでは十分ではなく、転置された垂直方向の被覆を削除した影響を
示唆しています。

そこで、二次元被覆を回復する二つの方式を、同一条件の50 epoch
スクリーニングで比較しました。

| Variant | 走査設計 | Mean Dice | Mean HD95 | Final loss | 平均epoch時間 | Peak memory |
|---|---|---:|---:|---:|---:|---:|
| E2_modify_1 | ブロックごとに水平・垂直の双方向走査を交互に使用 | 72.54% | **35.58** | 0.1478 | 213.81 s | **10,396 MiB** |
| E2_modify_2 | 各ブロック内で水平・垂直のチャネルグループを使用 | **75.07%** | 40.42 | **0.1307** | **170.71 s** | 11,016 MiB |

E2_modify_2は、E2_modify_1よりDiceが2.53ポイント高く、8臓器中7臓器で
Diceが改善し、最終lossが低く、平均epoch時間も約20.16%短縮しました。
一方、HD95は4.84悪化しているため、この選択は暫定的なものです。
境界の外れ値が収束後にも残るかを確認するため、E2_modify_2を300 epochで
検証しています。300 epochのE1/E2と50 epochのスクリーニング結果は、
最終性能として直接比較しません。

### 300 epoch収束結果の比較

正式比較には、各学習で保存されたcheckpointのテスト結果を使用します。
E2_modify_2では、学習lossが最小となったEpoch 297が選択され、Mean Dice
`80.2540%`、Mean HD95 `21.9206`を達成しました。

| 実験 | 走査・融合設計 | Checkpoint epoch | Mean Dice ↑ | Mean HD95 ↓ | 学習時間 | 平均epoch時間 | Peak GPU memory |
|---|---|---:|---:|---:|---:|---:|---:|
| E1 | オリジナルVM-UNet 4方向SS2D＋固定加算 | 286 | 80.0488% | 24.6136 | 14時間49分 | 177.86秒 | 14,665 MiB |
| E2 | Row-major Forward/Backward＋固定加算 | 299 | 78.6080% | 26.1111 | 13時間42分 | 164.48秒 | **10,747 MiB** |
| **E2_modify_2** | **チャネル分割型水平・垂直双方向走査＋固定加算** | **297** | **80.2540%** | **21.9206** | **13時間05分** | **157.06秒** | 11,016 MiB |
| E3 | チャネル分割型水平・垂直双方向走査＋静的学習可能融合 | 286 | 80.0049% | 25.5669 | 11時間35分 | **139.09秒** | 12,958 MiB |
| E4 Version 1 | チャネル分割型水平・垂直双方向走査＋制約付きAdaptive Gate | 285 | 70.9089% | 35.3190 | 9時間49分 | **117.91秒** | 13,534 MiB |

E1と比較すると、E2_modify_2はDiceを`0.2052`ポイント改善し、HD95を
`2.6931`（`10.94%`）低減しました。また、学習時間を`11.69%`、Peak GPU
memoryを`24.88%`削減しました。E2と比較すると、Diceを`1.6460`ポイント
回復し、HD95を`4.1906`改善しました。この結果は、E2の性能低下が主に
垂直方向の被覆を削除したことに起因し、E2_modify_2が低コストで二次元
コンテキストを維持できる可能性を支持します。ただし、現段階では単一seed
の結果であり、統計的な優越性を主張するものではありません。

完全なアーカイブレポート、全体・臓器別比較CSVおよびManifestは
[`research/runs/e2_modify_2_synapse_seed42/`](research/runs/e2_modify_2_synapse_seed42/)
に保存しています。

E3の300 epoch Full runでは、Mean Dice `80.0049%`、Mean HD95 `25.5669`
となりました。E2_modify_2と比較すると、Diceは`0.2491`ポイント低下し、
HD95は`3.6464`悪化しました。Diceが向上したのは膵臓と胃のみで、8臓器中
6臓器では低下しました。また、右腎のHD95は`31.5460`から`56.1532`へ
悪化しました。学習された静的融合重みは等重み付近に留まったため、E3は
負または中立的なアブレーション結果として位置付けます。すなわち、主要な
改善要因は二次元空間カバレッジの維持であり、入力非依存の静的融合だけでは
不十分です。現時点の参照モデルはE2_modify_2です。

E3 Full runの完全レポート、5実験の全体比較、臓器別CSV、Manifest、および
中日英3言語の発表用要約は
[`research/runs/E3_fusion_300_epochs/`](research/runs/E3_fusion_300_epochs/)
に保存しています。

E4 Version 1の300 epoch Full runでは、Mean Dice `70.9089%`、Mean HD95
`35.3190`となりました。E2_modify_2と比較するとDiceは`9.3451`ポイント
低下し、HD95は`13.3985`悪化し、8臓器すべてでDiceが低下しました。
平均epoch時間は`24.93%`短縮しましたが、Peak memoryは`22.86%`増加しました。
また、同じ設定として記録された50 epoch screeningとFull runでEpoch 50の
lossが`0.1146`対`0.7409`と大きく異なりました。したがってE4は負の
アブレーションとして保持し、再実行前に初期化と決定性を監査します。
現時点の参照モデルはE2_modify_2です。

E4の完全レポート、6実験の全体比較、8臓器別CSVおよびManifestは
[`research/runs/E4_version_1_full300/`](research/runs/E4_version_1_full300/)
に保存しています。

その後、E4のソースを固定し、同一条件で12 epochのA/A再現性監査を2回
実施しました。初期モデルのハッシュと各epochのバッチ順序は一致しましたが、
モデルおよびcheckpointのハッシュはEpoch 1から一致せず、最大loss差は
Epoch 11の`0.042850100568`でした。また、gate出力はEpoch 1で既に`tanh`の
下限`-1`と上限`+1`へ到達しました。これはbitwise再現性に対するRed判定で
あり、Adaptive Fusionそのものの理論的無効性を証明する結果ではありません。
したがって、正式なE4比較では複数seedとmean ± stdを用い、gate安定化は
別名のアブレーションとして検証します。診断コード、集約結果および判断記録は
[`research/runs/E4_determinism_AA/`](research/runs/E4_determinism_AA/)
に保存しています。

次に、E4 Version 1を置き換えず、別名の安定化アブレーションとしてE4
Version 2-Bを作成しました。Gateの学習率をbackboneの`0.1倍`とし、最初の
5 epochでGateを凍結し、alphaを`0`から`0.25`へ段階的に増加させました。
さらにgradient clipping、equal-fusion正則化、context normalization、
temperature scalingを導入し、alphaをcheckpointへ保存・復元できるように
修正しました。50 epoch正式実験は正常終了し、Mean Dice `74.9931%`、
Mean HD95 `37.9087`、平均epoch時間`97.81秒`、Peak allocated memory
`11,499.30 MiB`となりました。

これは工学的な安定化には成功した一方、精度面では負または未確定の
アブレーションです。E4 Version 2-Bは2,211枚の学習スライスから433枚を
checkpoint選択用のhold-out validationへ分離しており、全2,211枚を学習に
使用した従来実験とはプロトコルが一致しません。そのため、構造性能の直接順位
には使用せず、300 epochへの延長も行いません。現時点の主モデルは引き続き
E2_modify_2です。コード、7実験比較、8臓器比較、Excel、Manifestおよび
負のアブレーション分析は
[`research/runs/E4_v2_stabilized_b_epoch50/`](research/runs/E4_v2_stabilized_b_epoch50/)
に保存しています。

### E3 50 epochスクリーニング結果

E3では、E2_modify_2のチャネル分割型二次元双方向走査を維持し、固定加算を
静的学習可能融合へ置き換えました。同一条件の50 epoch比較では、E3はMean
Dice `75.6773%`、Mean HD95 `36.0624`を達成しました。E2_modify_2の50 epoch
結果（Dice `75.0737%`、HD95 `40.4159`）に対して、Diceは`0.6035`ポイント
改善し、HD95は`4.3535`低減しました。平均epoch時間も`170.71秒`から
`152.66秒`へ短縮しましたが、Peak memoryは`11,016 MiB`から`12,958 MiB`
へ増加しました。

これは単一seed・50 epochのスクリーニング結果であり、300 epochのE1/E2/
E2_modify_2と直接順位付けするものではありません。E3を300 epochで検証する
根拠は得られましたが、右腎Diceと脾臓HD95の外れ値は引き続き確認が必要です。
レポートと比較CSVは
[`research/runs/E3_fusion_50_epochs/`](research/runs/E3_fusion_50_epochs/)
に保存しています。

### 実験計画

- 最初にSynapseデータセットを用いてE1〜E4を単一seedで比較し、提案手法の有効性を予備評価します。
- 改善傾向が確認できた場合、3 seedsおよびACDCデータセットへ実験を拡張します。
- その後、Scratch、ImageNet、FractalDBの事前学習条件を比較し、FractalDBの有効性を検証します。
- 主な評価指標はDice、HD95、NSDです。

### 現在確認済みの結果

- E1 VM-UNet Synapse baseline：Mean Dice 約80.05%、Mean HD95 約24.61。
- 最良checkpoint：Epoch 286付近。
- 300 epochsの総学習時間：RTX 4090で約15〜16時間。
- E2 two-path fixed sum：Mean Dice 約78.61%、Mean HD95 約26.11。E1より低いため、転置・垂直方向の被覆を失った影響を次に検証する。
- E2_modify_2 grouped-2D fixed sum：Mean Dice 80.2540%、Mean HD95 21.9206。E1よりDiceが0.2052ポイント高く、HD95、学習時間およびPeak GPU memoryも改善した。
- E3 static learnable fusion（50 epoch screening）：Mean Dice 75.6773%、Mean HD95 36.0624。同一50 epoch条件のE2_modify_2よりDiceが0.6035ポイント高く、HD95が4.3535低い。300 epoch検証へ進む予備的根拠が得られた。
- E3 static learnable fusion（300 epoch）：Mean Dice 80.0049%、Mean HD95 25.5669。E2_modify_2を上回らず、静的融合のみでは追加改善が得られないことを示すアブレーション結果となった。
- E4 adaptive gate（300 epoch）：Mean Dice 70.9089%、Mean HD95 35.3190。E2_modify_2を下回り、screen/full学習軌跡の不一致を確認したためRed判定とした。
- E4 Version 2-B stabilized gate（50 epoch）：Mean Dice 74.9931%、Mean HD95 37.9087。安定化は確認できたが精度改善は得られず、validation splitも従来実験と異なるため、負または未確定のアブレーションとして保存し300 epochへは進めない。

実験設計、実行環境、設定値および確認済みの結果は[`research/`](research/)にまとめています。

再配布条件と容量の問題を考慮し、データセット、事前学習済み重み、checkpoint、NIfTI形式の出力、および認証情報は本リポジトリに含めていません。

### オリジナル実装について

本研究はVM-UNetの公式実装を基盤としています。再現性とライセンス表記を維持するため、以下にオリジナルの英語READMEおよびApache-2.0ライセンスを保持しています。

## Upstream attribution

This work is derived from the official VM-UNet implementation. The upstream
README and Apache-2.0 license are retained below.

---

# VM-UNet
This is the official code repository for "VM-UNet: Vision Mamba UNet for Medical
Image Segmentation". {[Arxiv Paper](https://arxiv.org/abs/2402.02491)}

## Abstract
In the realm of medical image segmentation, both CNN-based and Transformer-based models have been extensively explored. However, CNNs exhibit limitations in long-range modeling capabilities, whereas Transformers are hampered by their quadratic computational complexity. Recently, State Space Models (SSMs), exemplified by Mamba, have emerged as a promising approach. They not only excel in modeling long-range interactions but also maintain a linear computational complexity. In this paper, leveraging state space models, we propose a U-shape architecture model for medical image segmentation, named Vision Mamba UNet (VM-UNet). Specifically, the Visual State Space (VSS) block is introduced as the foundation block to capture extensive contextual information, and an asymmetrical encoder-decoder structure is constructed. We conduct comprehensive experiments on the ISIC17, ISIC18, and Synapse datasets, and the results indicate that VM-UNet performs competitively in medical image segmentation tasks. To our best knowledge, this is the first medical image segmentation model constructed based on the pure SSM-based model. We aim to establish a baseline and provide valuable insights for the future development of more efficient and effective SSM-based segmentation systems.

## 0. Main Environments
```bash
conda create -n vmunet python=3.8
conda activate vmunet
pip install torch==1.13.0 torchvision==0.14.0 torchaudio==0.13.0 --extra-index-url https://download.pytorch.org/whl/cu117
pip install packaging
pip install timm==0.4.12
pip install pytest chardet yacs termcolor
pip install submitit tensorboardX
pip install triton==2.0.0
pip install causal_conv1d==1.0.0  # causal_conv1d-1.0.0+cu118torch1.13cxx11abiFALSE-cp38-cp38-linux_x86_64.whl
pip install mamba_ssm==1.0.1  # mmamba_ssm-1.0.1+cu118torch1.13cxx11abiFALSE-cp38-cp38-linux_x86_64.whl
pip install scikit-learn matplotlib thop h5py SimpleITK scikit-image medpy yacs
```
The .whl files of causal_conv1d and mamba_ssm could be found here. {[Baidu](https://pan.baidu.com/s/1Tibn8Xh4FMwj0ths8Ufazw?pwd=uu5k) or [GoogleDrive](https://drive.google.com/drive/folders/1ZJjc7sdyd-6KfI7c8R6rDN8bcTz3QkCx?usp=sharing)}

## 1. Prepare the dataset

### ISIC datasets
- The ISIC17 and ISIC18 datasets, divided into a 7:3 ratio, can be found here {[Baidu](https://pan.baidu.com/s/1Y0YupaH21yDN5uldl7IcZA?pwd=dybm)}.

- After downloading the datasets, you are supposed to put them into './data/isic17/' and './data/isic18/', and the file format reference is as follows. (take the ISIC17 dataset as an example.)

- './data/isic17/'
  - train
    - images
      - .png
    - masks
      - .png
  - val
    - images
      - .png
    - masks
      - .png

### Synapse datasets

- For the Synapse dataset, you could follow [Swin-UNet](https://github.com/HuCaoFighting/Swin-Unet) to download the dataset, or you could download them from {[Baidu](https://pan.baidu.com/s/1JCXBfRL9y1cjfJUKtbEhiQ?pwd=9jti)}.

- After downloading the datasets, you are supposed to put them into './data/Synapse/', and the file format reference is as follows.

- './data/Synapse/'
  - lists
    - list_Synapse
      - all.lst
      - test_vol.txt
      - train.txt
  - test_vol_h5
    - casexxxx.npy.h5
  - train_npz
    - casexxxx_slicexxx.npz

## 2. Prepare the pre_trained weights

- The weights of the pre-trained VMamba could be downloaded from [Baidu](https://pan.baidu.com/s/1ci_YvPPEiUT2bIIK5x8Igw?pwd=wnyy) or [GoogleDrive](https://drive.google.com/drive/folders/1ZJjc7sdyd-6KfI7c8R6rDN8bcTz3QkCx?usp=sharing). After that, the pre-trained weights should be stored in './pretrained_weights/'.



## 3. Train the VM-UNet
```bash
cd VM-UNet
python train.py  # Train and test VM-UNet on the ISIC17 or ISIC18 dataset.
python train_synapse.py  # Train and test VM-UNet on the Synapse dataset.
```

**NOTE**: If you want to use the trained checkpoint for inference testing only and save the corresponding test images, you can follow these steps:

- **In `config_setting`**:
   - Set the parameter `only_test_and_save_figs` to `True`.
   - Fill in the path of the trained checkpoint in `best_ckpt_path`.
   - Specify the save path for test images in `img_save_path`.

- **Execute the script**:
   After setting the above parameters, you can run `train.py`.

## 4. Obtain the outputs
- After trianing, you could obtain the results in './results/'

## 5. Trained VM-UNet Checkpoint

- You can also obtain our trained VM-UNet on ISIC17, ISIC18 and Synapse from [Baidu Netdisk](https://pan.baidu.com/s/1lygUOFo6fMF_wS_dskwpBQ?pwd=5z00) or [GoogleDrive](https://drive.google.com/drive/folders/1ZJjc7sdyd-6KfI7c8R6rDN8bcTz3QkCx?usp=sharing).

## 6. Acknowledgments

- We thank the authors of [VMamba](https://github.com/MzeroMiko/VMamba) and [Swin-UNet](https://github.com/HuCaoFighting/Swin-Unet) for their open-source codes.


