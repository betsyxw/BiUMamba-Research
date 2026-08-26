# BiUMamba Research

[English](#english) | [日本語](#日本語)

## English

Private research repository for the master's project:

> **BiUMamba: Bidirectional Selective Scan with Adaptive Fusion and
> Natural-Image-Free Pre-training for Medical Image Segmentation**

Current experimental status:

- E1: original four-direction VM-UNet baseline — completed.
- E2: forward/backward bidirectional scan with fixed sum — training.
- E3: planned global static learnable fusion, after a sum/average equivalence test.
- E4: planned input-dependent adaptive fusion gate.
- Datasets: Synapse first, ACDC second; FractalDB pre-training pilot follows the directional ablation.

Datasets, pretrained weights, checkpoints, NIfTI outputs and credentials are
intentionally excluded. See [`research/`](research/) for the experiment design,
environment lock and verified results.

## 日本語

本リポジトリは、修士研究として取り組む以下の研究課題のための非公開リポジトリです。

> **BiUMamba：医用画像セグメンテーションのための、適応的融合を備えた双方向選択的スキャンと自然画像を使用しない事前学習**

本研究では、Vision Mambaを基盤とする医用画像セグメンテーションモデルに対して、次の二つの研究課題を検証します。

1. 従来の走査方法を双方向スキャンへ拡張し、入力に応じて情報を統合するAdaptive Fusion Gateを導入することで、臓器の形状や長距離依存関係をより効果的に表現できるか。
2. ImageNetなどの自然画像を用いず、FractalDBによる事前学習が医用画像セグメンテーションに有効な初期表現を提供できるか。

### 実験の進捗

- **E1：Original** — VM-UNetのオリジナル4方向スキャンによるベースライン。完了。
- **E2：Bidirectional + Fixed Sum** — Forward/Backwardの双方向スキャンを固定加算で融合。現在学習中。
- **E3：Bidirectional + Static Learnable Fusion** — SumとAverageの数学的等価性を確認した後、静的な学習可能融合として検証予定。
- **E4：Bidirectional + Adaptive Gate** — 入力依存の適応的融合ゲートとして検証予定。

### 実験計画

- 最初にSynapseデータセットを用いてE1〜E4を単一seedで比較し、提案手法の有効性を予備評価します。
- 改善傾向が確認できた場合、3 seedsおよびACDCデータセットへ実験を拡張します。
- その後、Scratch、ImageNet、FractalDBの事前学習条件を比較し、FractalDBの有効性を検証します。
- 主な評価指標はDice、HD95、NSDです。

### 現在確認済みの結果

- E1 VM-UNet Synapse baseline：Mean Dice 約80.05%、Mean HD95 約24.61。
- 最良checkpoint：Epoch 286付近。
- 300 epochsの総学習時間：RTX 4090で約15〜16時間。

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


