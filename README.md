# BiUMamba Research

**Last updated: 20261128**

**20261015 — Six-model source-completeness repair.** Explicit E1, E2,
E2_modify_1, E2_modify_2, E3 and E4-v1 source/config selection is now available
in the [reproduction guide](reproducibility/README.md). Missing E3 and E4-v1
implementation snapshots were restored from an archived execution-code copy.
BiUMamba requires `grouped_2d_bidirectional_sum`; `bidirectional_sum` is E2.
This update repairs public source coverage and adds maintained training and
evaluation entry points; it does not claim recovery of every original training
commit or numerical retraining. See the [source audit](reproducibility/SOURCE_RECOVERY_AUDIT.md).

**20261007 — Memory and model-file sizes are now reported in decimal GB
(`1 GB = 1,000,000,000 bytes`).** Published reports, tables, workbooks and
memory plots have been numerically converted. Device logs and original
benchmark records retain their native units for reproducibility. This is a
unit presentation update; accuracy, timings and percentage reductions are
unchanged. See the [conversion audit](research/unit_standardization_20261007/README.md).

**Research Author and Repository Maintainer:** xuwen

**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

**GitHub:** [@betsyxw](https://github.com/betsyxw)

Research-specific designs, experiment implementations, ablation records,
evaluation reports, and reproducibility documentation in this repository are
maintained by **xuwen**. The original VM-UNet/VMamba code remains attributed to
its upstream authors under the retained license. See [`AUTHORS.md`](AUTHORS.md).

## Project overview

Research repository for the master's project:

> **BiUMamba: Memory-Efficient Channel-Grouped Bidirectional Scanning
> for Medical Image Segmentation**

BiUMamba (E2_modify_2) assigns horizontal and vertical bidirectional scans to
separate channel groups and uses fixed-sum fusion. Adaptive fusion variants
are exploratory ablations. FractalDB-60 is a separate study of
natural-image-free initialization.

## Current progress

**20260912 — The paper evidence package has been regenerated and frozen.**

Formal E1/BiUMamba three-seed results are available for Synapse, ACDC and BUSI.
The Synapse empty-mask aggregation audit is complete, and downstream
Tables 1–7 and statistical figures have been regenerated locally. All 289
mapped numerical cells passed the earlier source/value check; the expanded
final audit covers 774 mapped table cells with zero failures. This update supersedes
the previous approximate 90% progress statement; it is not a live job-status
report for Hakusan.

The preselected Synapse E1-Narrow memory-control experiment is also complete
for seeds `42`, `2026` and `3407`. It provides a direct test of channel-grouped
scanning against the simpler alternative of narrowing the original E1 model.

The final GitHub-safe evidence package now includes the related-work comparison,
method differentiation table, `4HWC -> 2HWC` derivation, research-question-based
scan ablation, the E1-Narrow matched-memory control, Pareto figures, the
cross-dataset scope table, patient-level paired statistics, a forest plot,
manuscript-ready Discussion and Limitations, and a cell-level source map.
All 774 mapped cells passed the final cross-check. Medical-image qualitative
panels and the complete freeze archive remain outside GitHub.

See the [updated conclusions and reports](research/hakusan/),
[Step 20 correction](research/hakusan/STEP20_CORRECTION_REPORT_20260909.md)
and [final paper evidence package](research/paper_evidence_20260912/).

### Update history

- **20261015** — Added explicit source/config directories for all six E1--E4
  variants, recovered E3 static fusion and E4-v1 adaptive-gate code, local model
  wrappers, a guarded model registry, common Synapse-v2 training/evaluation
  commands, source hashes and release checks. Original formal-training commits
  remain subject to the documented provenance gaps; scientific results and E5
  status are unchanged. CUDA numerical reproduction was not performed here.

- **20260906** — Updated overall progress to approximately 90%, noted remaining
  work on Hakusan, made this README English-only, and clarified the final
  fixed-sum BiUMamba design and the separate exploratory pre-training study.

- **20260909** — Replaced the outdated progress estimate with verified candidate-release status; added corrected Synapse paired statistics and report links; clarified the training-memory advantage, inference-latency cost, BUSI limitation and lack of equivalence evidence.

- **20260911** — Added the formal three-seed E1-Narrow Synapse control, patient-level paired statistics, the strict RTX 4090 inference benchmark, and updated Tables 2, 4 and 6. The new control supports BiUMamba over simple narrowing for the observed accuracy-memory balance, while preserving the existing claim limits.

- **20260912** — Froze the GitHub-safe final paper evidence: expanded related work, method-difference table, E1/BiUMamba diagram, analytical scan-core derivation, research-question-based Table 2, E1-Narrow matched-memory comparison, Dice/NSD-memory Pareto figures, cross-dataset Table 4, patient-level Table 7 and forest plot, rewritten Discussion and Limitations, claim audit, cell-level source map and regenerated workbook. The central claim is a dataset-dependent training-memory trade-off, not higher accuracy or universal speed.

- **20260912** — Added direct repository access to the final public-safe
  [method diagram](research/result_img/paper_evidence_20260912/Figure_method_E1_vs_BiUMamba.png),
  [Dice–memory Pareto figure](research/result_img/paper_evidence_20260912/Figure_pareto_Dice_vs_memory.png),
  [NSD–memory Pareto figure](research/result_img/paper_evidence_20260912/Figure_pareto_NSD_vs_memory.png),
  and [patient-level forest plot](research/result_img/paper_evidence_20260912/Figure_patient_level_forest_plot.png).
  The corresponding PDF files remain in the same directory.

For every future README update, update the `Last updated` date and append a
new entry here using `YYYYMMDD`. Preserve earlier entries; updates made on the
same day may share the same date.

### Experimental status

- E1: original four-direction VM-UNet baseline — completed.
- E2: forward/reverse row-major scan with fixed sum — completed; below E1.
- E2_modify_1: alternating-axis bidirectional scan — 50-epoch screening completed. The report, metrics, manifest, logs, and matched comparison are mirrored in [`research/runs/E2_modify_1_screen50/`](research/runs/E2_modify_1_screen50/).
- E2_modify_2: channel-grouped 2D bidirectional scan — formal three-seed evaluation is complete on Synapse, ACDC and BUSI. It is now treated as an efficiency-oriented method, not a universal accuracy improvement.
- E1-Narrow: original four-direction E1 with SS2D expansion reduced to `1.50` — the preselected near-memory-matched Synapse control completed 300 epochs and isolated testing for all three fixed seeds. No post-hoc seed was added.
- E3: static learnable fusion on E2_modify_2 — 50-epoch screening and the full 300-epoch run completed; the final result did not outperform E2_modify_2.
- E4: constrained sample/channel adaptive gate on the same coverage-preserving structure — 50-epoch screening and 300-epoch full run completed; the full run was a Red result and exposed a screen/full reproducibility mismatch.
- E4 Version 2-B: separately named stabilized-gate ablation — deterministic A/A checks and a formal 50-epoch screening run completed. Training stability improved, but accuracy did not justify a 300-epoch extension.
- Datasets: formal three-seed tests are complete on Synapse CT, ACDC cardiac MRI and BUSI breast ultrasound. The FractalDB-60 low-label study is complete and did not show a stable advantage in the ACDC setting.

### Formal three-seed cross-dataset results (reviewed 20260909)

All formal comparisons use the fixed seeds `42`, `3407` and `2026`, matched
E1/E2_modify_2 training settings, validation-selected checkpoints and isolated
test sets.

| Dataset | Image type | E1 Dice | E2_modify_2 Dice | Dice change | Main efficiency evidence | Decision |
|---|---|---:|---:|---:|---|---|
| Synapse | Abdominal CT | 76.84 ± 1.15% | 76.66 ± 1.22% | -0.18 pp | Training peak memory -24.41%; unified inference latency +42.12% | Yellow |
| ACDC | Cardiac MRI | 90.77 ± 0.24% | 90.73 ± 0.15% | -0.046 pp | Training peak memory -24.93%; unified inference latency +78.79% | Yellow |
| BUSI | Breast ultrasound | 75.46 ± 0.87% | 72.60 ± 2.50% | -2.86 pp | Training peak memory -24.93%; unified inference latency +39.28% | Negative accuracy result |

The grouped two-axis scan consistently reduced peak training memory by about
24-25%, but its accuracy was dataset-dependent. It kept mean Dice close to E1
on Synapse and ACDC, while it did not preserve E1 accuracy on BUSI. The current
defensible conclusion is therefore an **accuracy-memory trade-off**, not
universal superiority. These findings concern this implementation and protocol,
not all Mamba architectures.

In the completed same-RTX-4090 inference benchmark, E2_modify_2 reduced peak
inference memory but increased mean latency by 42.12% on Synapse, 78.79% on
ACDC, and 39.28% on BUSI. Thus, the approximately 50% lower analytical SS2D
scan-core workload does not translate into a runtime speedup in the current
implementation. Whole-model FLOPs are explicitly reported as estimates.

- [`research/runs/synapse_v2_formal_3seed_comparison/`](research/runs/synapse_v2_formal_3seed_comparison/)
- [`research/runs/acdc_v1_formal_three_seed_runpod/`](research/runs/acdc_v1_formal_three_seed_runpod/)
- [`research/runs/busi_v1_clean_formal_three_seed/`](research/runs/busi_v1_clean_formal_three_seed/)
- [`research/runs/step19_unified_efficiency_20260906/`](research/runs/step19_unified_efficiency_20260906/)

### Corrected paired statistics and main conclusion (20260909)

The previous Step 20 aggregation incorrectly dropped six single-empty
case-organ-seed rows. The correction retains their stored penalties and
excludes only both-empty undefined pairs (none occurred in these six runs).
It does not change checkpoints or rerun raw-mask evaluation. The Synapse
descriptive Dice values in the table above were already correct.

After averaging the three seeds within each patient, the corrected Synapse
analysis uses 12 independent cases and 10,000 bootstrap resamples
(seed 20260909).

| Metric | BiUMamba minus E1 | Unadjusted bootstrap 95% CI | Raw p | Holm p |
|---|---:|---|---:|---:|
| Dice (percentage points) | -0.18072 | [-1.00645, +0.70612] | 0.697696 | 1.000000 |
| HD95 (protocol units) | +0.99505 | [-0.74899, +2.70181] | 0.300065 | 0.900196 |
| NSD (percentage points) | -0.00069 | [-0.75680, +0.83275] | 0.998731 | 1.000000 |

Holm adjustment covers the three overall metrics. Synapse distances use the
stored unit-spacing protocol, not verified physical CT millimetres. ACDC/BUSI
statistics are unchanged in this update.

**Main contribution:** a channel-grouped bidirectional scan that preserves
horizontal and vertical coverage while reducing peak training memory by
approximately 24–25%. Synapse and ACDC show small observed mean accuracy
differences and no statistically significant patient-level differences.
BUSI shows significantly worse Dice and NSD and higher HD95.

**Limitations:** no equivalence or non-inferiority test was performed, so
"equivalent", "no accuracy loss" and universal accuracy improvement are not
supported. The current strict RTX 4090 benchmark shows increased inference
latency on all three datasets, despite lower analytical scan-core workload.
The contribution is an observed accuracy–memory trade-off with runtime
costs and dataset-dependent limitations, not a speedup claim.

### Near-memory-matched E1-Narrow control (20260911)

To test whether BiUMamba's result could be reproduced by simply shrinking the
baseline, four E1 width candidates received short memory-only calibration.
The SS2D expansion `1.50` candidate was selected before full training and was
then evaluated with the fixed seeds `42`, `2026` and `3407`. Every run completed
300 epochs and used the same frozen Synapse split and 12-case isolated test set.

| Method | Dice (%) | HD95 | NSD (%) | Peak training allocated | Parameters | Strict inference latency |
|---|---:|---:|---:|---:|---:|---:|
| E1 / VM-UNet | 76.84 ± 1.15 | 32.13 ± 4.95 | 71.59 ± 2.25 | 12.842 GB | 27.43 M | 4.955 ± 0.544 ms |
| E1-Narrow | 75.04 ± 2.82 | 33.89 ± 3.99 | 69.15 ± 2.34 | 10.168 GB | 21.36 M | 10.740 ± 0.187 ms |
| BiUMamba | 76.66 ± 1.22 | 33.12 ± 5.06 | 71.59 ± 1.73 | 9.707 GB | 27.43 M | 7.043 ± 0.832 ms |

Each patient was first averaged across the three seeds before paired testing.
Relative to E1, E1-Narrow had significantly lower Dice and NSD after Holm
correction. Relative to E1-Narrow, BiUMamba's observed Dice was `1.62`
percentage points higher, but this difference did not remain significant after
Holm correction (`p=0.0683`). Its NSD was `2.44` percentage points higher and
remained significant (`p=0.0111`); HD95 did not differ significantly.

BiUMamba also had lower observed seed-level variability for Dice (`1.22` versus
`2.82` percentage points) and NSD (`1.73` versus `2.34` percentage points).
With only three fixed seeds, this is descriptive stability evidence rather than
a formal variance test.

The control therefore supports retaining BiUMamba for the observed
accuracy-memory balance. Simple narrowing reduced parameters but also reduced
Dice and NSD. BiUMamba used slightly less peak allocated training memory than
E1-Narrow and had lower strict inference latency while retaining the original
model capacity. Original E1 remained the fastest, so these findings do not
support a universal speedup claim.

The GitHub-safe statistics, strict benchmark record, updated tables and paper
conclusion are archived in
[`research/runs/e1_narrow_synapse_3seed_20260911/`](research/runs/e1_narrow_synapse_3seed_20260911/).

### Natural-image-free pre-training (20260909)

Under the frozen ACDC 25% label protocol, FractalDB-60 did not outperform
training from scratch and remained below ImageNet initialization across the
three fixed seeds. The 50% and 100% runs use seed 42 only and are exploratory;
they cannot overturn the formal 25% conclusion or support a general
low-label advantage. This negative finding is specific to our setting.

### Historical training story and screening evidence

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
| E2_modify_1 | Alternating horizontal/vertical bidirectional blocks | 72.54% | **35.58** | 0.1478 | 213.81 s | **10.901 GB** |
| E2_modify_2 | Channel-grouped horizontal/vertical bidirectional scan in every block | **75.07%** | 40.42 | **0.1307** | **170.71 s** | 11.551 GB |

E2_modify_2 was selected for the first full 300-epoch validation because it
improved Dice by `2.53` percentage points, improved Dice in seven of eight
organs, reduced final loss, and trained about `20.16%` faster per epoch than
E2_modify_1. Its HD95 was `4.84` worse, so this is a provisional selection—not
evidence that the method is already superior. This screening result motivated
the later 300-epoch and formal three-seed evaluations reported above. E1/E2
(300 epochs) and E2_modify_1/E2_modify_2 (50 epochs) are not treated as directly
comparable final results.

### Historical single-seed 300-epoch comparison

This historical comparison uses the archived checkpoint selected by each training
run. It is separate from the formal isolated-test comparison above. For E2_modify_2, the training script selected Epoch 297 by minimum training
loss; the resulting checkpoint achieved `80.2540%` Mean Dice and `21.9206`
Mean HD95.

| Experiment | Scan and fusion design | Checkpoint epoch | Mean Dice ↑ | Mean HD95 ↓ | Training time | Mean epoch time | Peak GPU memory |
|---|---|---:|---:|---:|---:|---:|---:|
| E1 | Original VM-UNet four-direction SS2D + fixed sum | 286 | 80.0488% | 24.6136 | 14 h 49 m | 177.86 s | 15.377 GB |
| E2 | Row-major forward/backward + fixed sum | 299 | 78.6080% | 26.1111 | 13 h 42 m | 164.48 s | **11.269 GB** |
| **E2_modify_2** | **Channel-grouped horizontal/vertical bidirectional scan + fixed sum** | **297** | **80.2540%** | **21.9206** | **13 h 05 m** | **157.06 s** | 11.551 GB |
| E3 | Channel-grouped horizontal/vertical bidirectional scan + static learnable fusion | 286 | 80.0049% | 25.5669 | 11 h 35 m | **139.09 s** | 13.587 GB |
| E4 Version 1 | Channel-grouped horizontal/vertical bidirectional scan + constrained adaptive gate | 285 | 70.9089% | 35.3190 | 9 h 49 m | **117.91 s** | 14.191 GB |

Compared with E1, E2_modify_2 improved Dice by `0.2052` percentage points,
reduced HD95 by `2.6931` (`10.94%`), reduced training time by `11.69%`, and
reduced peak GPU memory by `24.88%`. Compared with E2, it recovered `1.6460`
Dice points and reduced HD95 by `4.1906`. This is consistent with directional
coverage being important, but does not establish it as the sole cause of the
performance difference. The grouped-2D design retains both scan axes with a
lower directional scan workload than the original implementation. These values are retained as historical
single-seed evidence; the formal three-seed results above supersede them for
the final cross-dataset conclusion.

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
HD95, `97.81 s` mean epoch time, and `12.058 GB` peak allocated memory.

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
to `13.587 GB`.

This is a short single-seed screening result, not a direct comparison with the
300-epoch E1/E2/E2_modify_2 results. It motivated the completed E3 300-epoch
run described above. Right-kidney Dice and the spleen HD95 outlier remain
explicit risks. The report and structured comparisons are archived in
[`research/runs/E3_fusion_50_epochs/`](research/runs/E3_fusion_50_epochs/).

Datasets, pretrained weights, checkpoints, NIfTI outputs and credentials are
intentionally excluded. See [`research/`](research/) for the experiment design,
environment lock and verified results.

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

## Update log

### 2026-11-28: Synapse v2 validation results table

We added three files under `results/val_table_20261128/`: `RESULTS_TABLE_VAL.md`, `RESULTS_TABLE_VAL.csv`, and `SOURCES.txt`.

The table reports validation results only. It uses the Synapse v2 protocol, with 4 validation cases. The three seeds (42, 3407, and 2026) were fixed in advance. This table does not include test-set results.

The G4-Single row is incomplete (2 of 3 seeds finished). The G4-Paired row is incomplete (0 of 3 seeds finished).

On the validation set, E1 (VM-UNet) has the best Dice (0.7995 ± 0.0078) and the best HD95. BiUMamba has a lower validation Dice (0.7878 ± 0.0145). BiUMamba uses half the scan budget (2HWC vs 4HWC). On the same RTX 4090, it also uses less training memory (9.71 GB vs 12.85 GB). With only 4 validation cases, these differences may be within noise.

The repository `.gitignore` contains `results/**`. The three files were added with `git add -f`. The `.gitignore` file was not changed.

- We also updated the "Last updated" date at the top of this README to 20261128.
