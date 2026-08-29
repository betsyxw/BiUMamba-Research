import torch
# E4_version_2_stabilized_gate research modifications: xuwen, JAIST.
from torch import nn
from torch.cuda.amp import autocast, GradScaler
from torch.utils.data import DataLoader, Subset
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data.distributed import DistributedSampler
from torchvision import transforms

from datasets.dataset import RandomGenerator
from datasets.validation import ValidationGenerator
from engine_synapse import *

from models.vmunet.vmunet import VMUNet

import os
import sys
os.environ["CUDA_VISIBLE_DEVICES"] = "0" # "0, 1, 2, 3"

from utils import *
from configs.config_setting_synapse import setting_config

import warnings
warnings.filterwarnings("ignore")





def main(config):

    print('#----------Creating logger----------#')
    sys.path.append(config.work_dir + '/')
    log_dir = os.path.join(config.work_dir, 'log')
    checkpoint_dir = os.path.join(config.work_dir, 'checkpoints')
    resume_model = os.path.join(checkpoint_dir, 'latest.pth')
    outputs = os.path.join(config.work_dir, 'outputs')
    if not os.path.exists(checkpoint_dir):
        os.makedirs(checkpoint_dir)
    if not os.path.exists(outputs):
        os.makedirs(outputs)

    global logger
    logger = get_logger('train', log_dir)

    log_config_info(config, logger)





    print('#----------GPU init----------#')
    set_seed(config.seed)
    gpu_ids = [0]# [0, 1, 2, 3]
    torch.cuda.empty_cache()
    gpus_type, gpus_num = torch.cuda.get_device_name(), torch.cuda.device_count()
    if config.distributed:
        print('#----------Start DDP----------#')
        dist.init_process_group(backend='nccl', init_method='env://')
        torch.cuda.manual_seed_all(config.seed)
        config.local_rank = torch.distributed.get_rank()





    print('#----------Preparing dataset----------#')
    # Research modification maintained by xuwen, JAIST: checkpoint selection
    # uses a fixed case-level holdout from the original training cases. The
    # official Synapse test volumes remain untouched until final evaluation.
    augmented_train_dataset = config.datasets(
        base_dir=config.data_path,
        list_dir=config.list_dir,
        split="train",
        transform=transforms.Compose([
            RandomGenerator(
                output_size=[config.input_size_h, config.input_size_w]
            )
        ]),
    )
    deterministic_val_dataset = config.datasets(
        base_dir=config.data_path,
        list_dir=config.list_dir,
        split="train",
        transform=transforms.Compose([
            ValidationGenerator(
                output_size=[config.input_size_h, config.input_size_w]
            )
        ]),
    )
    validation_cases = set(config.validation_cases)
    all_training_cases = {
        name.strip().split('_slice')[0]
        for name in augmented_train_dataset.sample_list
    }
    missing_validation_cases = validation_cases - all_training_cases
    if missing_validation_cases:
        raise RuntimeError(
            f'Validation cases are not in the training list: '
            f'{sorted(missing_validation_cases)}'
        )
    train_indices = []
    validation_indices = []
    for index, sample_name in enumerate(augmented_train_dataset.sample_list):
        case_name = sample_name.strip().split('_slice')[0]
        if case_name in validation_cases:
            validation_indices.append(index)
        else:
            train_indices.append(index)
    if not train_indices or not validation_indices:
        raise RuntimeError('The fixed training/validation split is empty.')
    train_dataset = Subset(augmented_train_dataset, train_indices)
    selection_val_dataset = Subset(
        deterministic_val_dataset, validation_indices
    )
    train_sampler = DistributedSampler(train_dataset, shuffle=True) if config.distributed else None
    train_loader = DataLoader(train_dataset,
                                batch_size=config.batch_size//gpus_num if config.distributed else config.batch_size,
                                shuffle=(train_sampler is None),
                                pin_memory=True,
                                num_workers=config.num_workers,
                                sampler=train_sampler)

    selection_val_loader = DataLoader(
        selection_val_dataset,
        batch_size=config.validation_batch_size,
        shuffle=False,
        pin_memory=True,
        num_workers=config.num_workers,
    )

    split_message = (
        f'Case-level split: train_cases={sorted(all_training_cases - validation_cases)}, '
        f'validation_cases={sorted(validation_cases)}, '
        f'train_slices={len(train_dataset)}, '
        f'validation_slices={len(selection_val_dataset)}'
    )
    print(split_message)
    logger.info(split_message)

    test_dataset = config.datasets(base_dir=config.volume_path, split="test_vol", list_dir=config.list_dir)
    test_sampler = DistributedSampler(test_dataset, shuffle=False) if config.distributed else None
    test_loader = DataLoader(test_dataset,
                                batch_size=1, # if config.distributed else config.batch_size,
                                shuffle=False,
                                pin_memory=True,
                                num_workers=config.num_workers,
                                sampler=test_sampler,
                                drop_last=True)





    print('#----------Prepareing Models----------#')
    model_cfg = config.model_config
    if config.network == 'vmunet':
        model = VMUNet(
            num_classes=model_cfg['num_classes'],
            input_channels=model_cfg['input_channels'],
            depths=model_cfg['depths'],
            depths_decoder=model_cfg['depths_decoder'],
            drop_path_rate=model_cfg['drop_path_rate'],
            load_ckpt_path=model_cfg['load_ckpt_path'],
            scan_fusion=model_cfg.get('scan_fusion', 'original'),
        )
        model.load_from()
    else: raise('Please prepare a right net!')

    if config.distributed:
        model = torch.nn.SyncBatchNorm.convert_sync_batchnorm(model).cuda()
        model = DDP(model, device_ids=[config.local_rank], output_device=config.local_rank)
    else:
        model = torch.nn.DataParallel(model.cuda(), device_ids=gpu_ids, output_device=gpu_ids[0])





    print('#----------Prepareing loss, opt, sch and amp----------#')
    criterion = config.criterion
    optimizer = get_optimizer(config, model)
    scheduler = get_scheduler(config, optimizer)
    scaler = GradScaler()





    print('#----------Set other params----------#')
    start_epoch = 1
    best_val_dice = float('-inf')
    best_val_hd95 = float('inf')
    best_epoch = 0


    if config.only_test_and_save_figs:
        checkpoint = torch.load(config.best_ckpt_path, map_location=torch.device('cpu'))
        model.load_state_dict(checkpoint)
        config.work_dir = config.img_save_path
        if not os.path.exists(config.work_dir + 'outputs/'):
            os.makedirs(config.work_dir + 'outputs/')
        mean_dice, mean_hd95 = val_one_epoch(
                test_dataset,
                test_loader,
                model,
                0,
                logger,
                config,
                test_save_path=outputs,
                val_or_test=True
            )
        print(mean_dice, mean_hd95)
        return



    if os.path.exists(resume_model):
        print('#----------Resume Model and Other params----------#')
        checkpoint = torch.load(resume_model, map_location=torch.device('cpu'))
        model.module.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        saved_epoch = checkpoint['epoch']
        start_epoch += saved_epoch
        best_val_dice = checkpoint.get('best_val_dice', float('-inf'))
        best_val_hd95 = checkpoint.get('best_val_hd95', float('inf'))
        best_epoch = checkpoint.get('best_epoch', 0)
        loss = checkpoint['loss']

        log_info = (
            f'resuming model from {resume_model}. resume_epoch: {saved_epoch}, '
            f'best_val_dice: {best_val_dice:.6f}, '
            f'best_val_hd95: {best_val_hd95:.6f}, '
            f'best_epoch: {best_epoch}, loss: {loss:.4f}'
        )
        logger.info(log_info)





    print('#----------Training----------#')
    for epoch in range(start_epoch, config.epochs + 1):

        torch.cuda.empty_cache()
        train_sampler.set_epoch(epoch) if config.distributed else None

        loss = train_one_epoch(
            train_loader,
            model,
            criterion,
            optimizer,
            scheduler,
            epoch,
            logger,
            config,
            scaler=scaler
        )

        if epoch % config.selection_val_interval == 0:
            mean_dice, mean_hd95 = val_heldout_training_cases(
                selection_val_loader, model, epoch, logger, config
            )
            epsilon = config.checkpoint_metric_epsilon
            is_better = (
                mean_dice > best_val_dice + epsilon
                or (
                    abs(mean_dice - best_val_dice) <= epsilon
                    and mean_hd95 < best_val_hd95
                )
            )
            if is_better:
                torch.save(
                    model.module.state_dict(),
                    os.path.join(checkpoint_dir, 'best.pth'),
                )
                best_val_dice = mean_dice
                best_val_hd95 = mean_hd95
                best_epoch = epoch
                logger.info(
                    f'New validation-selected checkpoint: epoch {epoch}, '
                    f'mean_dice {mean_dice:.6f}, mean_hd95 {mean_hd95:.6f}'
                )

        torch.save(
            {
                'epoch': epoch,
                'best_val_dice': best_val_dice,
                'best_val_hd95': best_val_hd95,
                'best_epoch': best_epoch,
                'validation_cases': sorted(validation_cases),
                'loss': loss,
                'model_state_dict': model.module.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict(),
            }, os.path.join(checkpoint_dir, 'latest.pth'))

    if best_epoch == 0:
        mean_dice, mean_hd95 = val_heldout_training_cases(
            selection_val_loader, model, epoch, logger, config
        )
        torch.save(
            model.module.state_dict(),
            os.path.join(checkpoint_dir, 'best.pth'),
        )
        best_val_dice = mean_dice
        best_val_hd95 = mean_hd95
        best_epoch = epoch
        logger.info(
            f'Fallback final-epoch validation checkpoint: epoch {epoch}, '
            f'mean_dice {mean_dice:.6f}, mean_hd95 {mean_hd95:.6f}'
        )

    if os.path.exists(os.path.join(checkpoint_dir, 'best.pth')):
        print('#----------Testing----------#')
        best_weight = torch.load(config.work_dir + 'checkpoints/best.pth', map_location=torch.device('cpu'))
        model.module.load_state_dict(best_weight)
        mean_dice, mean_hd95 = val_one_epoch(
                test_dataset,
                test_loader,
                model,
                epoch,
                logger,
                config,
                test_save_path=outputs,
                val_or_test=True
            )
        os.rename(
            os.path.join(checkpoint_dir, 'best.pth'),
            os.path.join(checkpoint_dir,
                f'best-valepoch{best_epoch}-vald{best_val_dice:.4f}-'
                f'valhd95{best_val_hd95:.4f}-testd{mean_dice:.4f}-'
                f'testhd95{mean_hd95:.4f}.pth')
        )


if __name__ == '__main__':
    config = setting_config
    main(config)
