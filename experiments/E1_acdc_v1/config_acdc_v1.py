"""Frozen ACDC v1 E1 training configuration.

Research Author and Repository Maintainer: xuwen
Affiliation: Japan Advanced Institute of Science and Technology (JAIST)
"""

from utils import CeDiceLoss


class ACDCV1Config:
    network = "vmunet"
    num_classes = 4
    input_channels = 3
    input_size_h = 192
    input_size_w = 192
    batch_size = 32
    num_workers = 0
    amp = False
    print_interval = 10
    criterion = CeDiceLoss(num_classes, [1, 1])

    opt = "AdamW"
    lr = 0.001
    betas = (0.9, 0.999)
    eps = 1e-8
    weight_decay = 1e-2
    amsgrad = False

    sch = "CosineAnnealingLR"
    T_max = 100
    eta_min = 0.00001
    last_epoch = -1

    model_config = {
        "num_classes": 4,
        "input_channels": 3,
        "depths": [2, 2, 2, 2],
        "depths_decoder": [2, 2, 2, 1],
        "drop_path_rate": 0.2,
        "load_ckpt_path": "./pre_trained_weights/vmamba_small_e238_ema.pth",
        "scan_fusion": "original",
    }
