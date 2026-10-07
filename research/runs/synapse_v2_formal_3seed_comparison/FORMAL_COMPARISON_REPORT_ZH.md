# Synapse_v2 正式三种子对比报告：E1 vs E2_modify_2

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)  
**报告日期：** 2026-09-02

## 1. 实验目的

本报告在完全一致的 `Synapse_v2` 正式协议下，对以下两种模型进行公平比较：

- **E1：Original VM-UNet with four-direction SS2D**，即原始四方向 VM-UNet baseline；
- **E2_modify_2：Channel-grouped 2D Bidirectional Scan**，通过通道分组分别保留水平与垂直双向覆盖。

核心问题是：E2_modify_2 能否在减少扫描计算与显存需求的同时，保持或提高医学图像分割精度。

## 2. 正式实验协议

- 数据集：Synapse CT；
- 固定划分：14 个训练病例、4 个验证病例、12 个隔离测试病例；
- 随机种子：42、2026、3407；
- 训练轮数：300 epochs；
- 最佳 checkpoint：仅根据 validation Dice 选择；Dice 相同时，以较低 validation HD95 为准；
- 测试集：训练与 checkpoint 选择期间完全隔离，只在训练完成后统一离线评估一次；
- 正式指标：Mean Dice、physical HD95（mm）、NSD@1 mm；
- 汇总方式：报告三个预注册种子的 mean ± sample standard deviation；
- 效率比较：只使用相同 RTX 4090 环境下的 seed 42，避免跨平台时间比较。

## 3. 三种子总体测试结果

| 模型 | Mean Dice (%) ↑ | Mean HD95 (mm) ↓ | Mean NSD@1 mm (%) ↑ |
|---|---:|---:|---:|
| E1 | **76.84 ± 1.15** | **32.13 ± 4.95** | **71.59 ± 2.25** |
| E2_modify_2 | 76.66 ± 1.22 | 33.12 ± 5.06 | 71.59 ± 1.73 |
| E2_modify_2 − E1 | **−0.18 pp** | **+1.00 mm** | **约 0.00 pp** |

解释：

- E2_modify_2 的平均 Dice 比 E1 低 0.18 个百分点，差距很小，但没有形成精度提升；
- E2_modify_2 的 HD95 高 1.00 mm，说明最差边界距离略有恶化；
- 两者的 NSD@1 mm 基本相同；
- 三个指标共同表明：E2_modify_2 基本保持了 E1 的分割性能，但不能声称整体精度优于 E1。

## 4. 各随机种子结果

| Seed | E1 Dice (%) | E2_modify_2 Dice (%) | Dice差值 (pp) | E1 HD95 | E2_modify_2 HD95 | E1 NSD (%) | E2_modify_2 NSD (%) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 76.24 | 76.82 | +0.58 | 31.63 | 34.69 | 70.86 | 71.85 |
| 2026 | 78.17 | 77.79 | −0.38 | 27.45 | 27.47 | 74.12 | 73.18 |
| 3407 | 76.12 | 75.38 | −0.74 | 37.31 | 37.21 | 69.80 | 69.74 |

E2_modify_2 只在 seed 42 上取得 Dice 提升；在 seed 2026 和 3407 上略低于 E1。因此，先前单 seed 42 的改善不能直接解释为稳定的普遍提升，多种子验证是必要的。

## 5. 逐器官平均变化

下表为 `E2_modify_2 − E1`。Dice 与 NSD 为正代表改善；HD95 为负代表改善。

| 器官 | Dice变化 (pp) | HD95变化 (mm) | NSD变化 (pp) | 综合观察 |
|---|---:|---:|---:|---|
| Aorta | −0.44 | −0.85 | −0.46 | 边界距离改善，但重叠率略降 |
| Gallbladder | +1.58 | +3.28 | +0.44 | Dice改善，但极端边界误差增加 |
| Left Kidney | +1.25 | +5.67 | +1.84 | 重叠与表面接近度改善，但HD95恶化 |
| Right Kidney | +2.20 | −1.19 | +1.78 | 三项指标均改善 |
| Liver | +0.25 | −3.68 | +0.97 | 三项指标均改善 |
| Pancreas | −2.81 | −0.48 | −1.66 | HD95略改善，但Dice与NSD下降 |
| Spleen | −1.79 | +2.12 | −2.27 | 三项指标均下降 |
| Stomach | −1.68 | +3.09 | −0.63 | 三项指标均下降 |

器官级结果说明，E2_modify_2 对右肾和肝脏最有利，但对胰腺、脾脏和胃的结果较弱。整体平均值接近，是不同器官改善与下降相互抵消的结果。

## 6. 同硬件效率与显存比较

为了保证公平性，以下只比较同一 RTX 4090 上的 seed 42。

| 模型 | 总训练时间 (h) ↓ | 平均每epoch (s) ↓ | 峰值训练显存 (GB) ↓ | 参数量 | 推理时间 (ms/slice) ↓ |
|---|---:|---:|---:|---:|---:|
| E1 | **8.61** | **102.69** | 12.842 | 27,427,761 | **4.79** |
| E2_modify_2 | 9.01 | 107.42 | **9.707** | 27,427,761 | 6.95 |
| 相对变化 | +4.57% | +4.60% | **−24.44%** | 0% | +45.22% |

效率结论：

- **明确优势：** E2_modify_2 将训练峰值显存从 12.842 GB 降至 9.707 GB，降低约 **24.44%**；
- **没有速度优势：** 总训练时间增加约 4.57%，平均 epoch 时间增加约 4.60%；
- **推理更慢：** 单 slice 推理时间由 4.79 ms 增至 6.95 ms；
- **参数量不变：** 两个模型均为 27,427,761 个参数；
- THOP 对自定义 selective-scan 操作可能存在漏计，因此正式效率论证应优先采用实际测量的时间和显存，而不是只依赖名义 FLOPs。

## 7. Green / Yellow / Red 决策门

### Green

三种子平均 Dice 不低于或优于 E1，HD95 与小器官结果稳定，同时实际时间或显存有明确改善。此时可以强调“精度与效率同时改善”。

### Yellow

总体精度与 E1 接近，但不同种子或器官存在分化；或者只获得部分资源优势，同时牺牲了其他效率指标。此时应诚实报告 accuracy–resource trade-off。

### Red

三种子平均 Dice 明显下降、HD95系统性恶化，并且没有可验证的计算或显存优势。此时不能将该模型作为最终主模型，应重新设计或转为负面消融。

## 8. 最终判定：Yellow

**E2_modify_2 的正式结论是 Yellow。**

它成功修复了原始 E2 因丢失垂直覆盖造成的明显精度下降，并在三种子实验中基本保持 E1 的 Dice 和 NSD。同时，它将 RTX 4090 上的训练峰值显存降低约 24.4%，证明覆盖保持型通道分组扫描具有实际资源优势。

但是，E2_modify_2 的平均 Dice 仍比 E1 低 0.18 个百分点，HD95 高 1.00 mm，而且训练与推理速度更慢。因此目前不能声称它在精度和速度上全面优于 VM-UNet。

## 9. 论文中的推荐表述

> Under the frozen Synapse_v2 protocol with three random seeds, the proposed channel-grouped bidirectional scan maintained segmentation accuracy close to the original four-direction VM-UNet while reducing peak training memory by 24.4%. However, it did not improve average Dice or runtime efficiency, indicating an accuracy–memory trade-off rather than universal superiority.

中文解释：

> 在冻结的 Synapse_v2 三种子协议下，通道分组双向扫描在将训练峰值显存降低 24.4% 的同时，基本保持了原始四方向 VM-UNet 的分割精度。但它没有提高平均 Dice 或运行速度，因此本研究证明的是精度与显存之间的权衡，而不是模型全面优越。

## 10. 后续研究建议

1. 将 E1 与 E2_modify_2 扩展到 ACDC，检验该显存优势和精度保持能力是否可以跨 CT/MRI 数据集复现；
2. 使用同一 Synapse_v2 checkpoint 制作 Input、Ground Truth、E1、E2_modify_2 的同 slice 定性对比；
3. 重点检查右肾、肝脏、胰腺、脾脏和胃，解释哪些结构从二维覆盖中获益，哪些小器官或复杂边界仍然受损；
4. 在论文中将 E2 与 E3/E4 作为诊断性或负面消融，保留完整研究过程；
5. FractalDB 低标注预训练作为第二条独立贡献，不能用来掩盖当前扫描结构的混合结果。

## 11. 审计说明

- 三种子为预注册的 42、2026、3407；
- 标准差为三个种子的 sample standard deviation；
- 由于只有三个种子，本报告不宣称基于正态假设检验的统计显著性；
- E2_modify_2 正式推理模式为 `grouped_2d_bidirectional_sum`；错误模式的早期 dry run 已排除并单独记录；
- HAKUSAN A100 与 RunPod RTX 4090 的精度结果可统一汇总，但跨平台时间不能直接作为效率结论；
- 所有正式效率结论均来自同一 RTX 4090、同一 seed 42 的直接比较。
