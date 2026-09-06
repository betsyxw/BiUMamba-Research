# BiUMamba Research

**Last updated: 20260906**

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

**20260906 — Approximately 90% of the experiment and model-result work is
complete. Some remaining work is still running on JAIST Hakusan.**

This is the maintainer's overall progress estimate, not a measured percentage
of completed jobs. Completed evaluations below remain available as evidence;
the full project should not yet be treated as a 100% complete release.
Results from the remaining Hakusan work will be added after completion and
verification.

### Update history

- **20260906** — Updated overall progress to approximately 90%, noted remaining
  work on Hakusan, made this README English-only, and clarified the final
  fixed-sum BiUMamba design and the separate exploratory pre-training study.

For every future README update, update the `Last updated` date and append a
new entry here using `YYYYMMDD`. Preserve earlier entries; updates made on the
same day may share the same date.

### Experimental status

- E1: original four-direction VM-UNet baseline — completed.
- E2: forward/reverse row-major scan with fixed sum — completed; below E1.
- E2_modify_1: alternating-axis bidirectional scan — 50-epoch screening completed. The report, metrics, manifest, logs, and matched comparison are mirrored in [`research/runs/E2_modify_1_screen50/`](research/runs/E2_modify_1_screen50/).
- E2_modify_2: channel-grouped 2D bidirectional scan — formal three-seed evaluation is complete on Synapse, ACDC and BUSI. It is now treated as an efficiency-oriented method, not a universal accuracy improvement.
- E3: static learnable fusion on E2_modify_2 — 50-epoch screening and the full 300-epoch run completed; the final result did not outperform E2_modify_2.
- E4: constrained sample/channel adaptive gate on the same coverage-preserving structure — 50-epoch screening and 300-epoch full run completed; the full run was a Red result and exposed a screen/full reproducibility mismatch.
- E4 Version 2-B: separately named stabilized-gate ablation — deterministic A/A checks and a formal 50-epoch screening run completed. Training stability improved, but accuracy did not justify a 300-epoch extension.
- Datasets: formal three-seed tests are complete on Synapse CT, ACDC cardiac MRI and BUSI breast ultrasound. The FractalDB-60 low-label study is complete and did not show a stable advantage in the ACDC setting.

### Formal three-seed cross-dataset results (updated 20260906)

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
universal superiority. Full Dice/HD95/NSD results, per-seed tables and audit
records are archived in:

In the completed same-RTX-4090 inference benchmark, E2_modify_2 reduced peak
inference memory but increased mean latency by 42.12% on Synapse, 78.79% on
ACDC, and 39.28% on BUSI. Thus, the approximately 50% lower analytical SS2D
scan-core workload does not translate into a runtime speedup in the current
implementation. Whole-model FLOPs are explicitly reported as estimates.

- [`research/runs/synapse_v2_formal_3seed_comparison/`](research/runs/synapse_v2_formal_3seed_comparison/)
- [`research/runs/acdc_v1_formal_three_seed_runpod/`](research/runs/acdc_v1_formal_three_seed_runpod/)
- [`research/runs/busi_v1_clean_formal_three_seed/`](research/runs/busi_v1_clean_formal_three_seed/)
- [`research/runs/step19_unified_efficiency_20260906/`](research/runs/step19_unified_efficiency_20260906/)

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
four-direction implementation. These values are retained as historical
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
