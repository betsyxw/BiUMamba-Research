import numpy as np
# E4_version_2_stabilized_gate research modifications: xuwen, JAIST.
from tqdm import tqdm

from torch.cuda.amp import autocast as autocast
import torch

from sklearn.metrics import confusion_matrix

from scipy.ndimage.morphology import binary_fill_holes, binary_opening
from scipy.ndimage import zoom
from medpy import metric

from utils import test_single_volume

import time


# E4_version_2_stabilized_gate research modifications maintained by xuwen,
# Japan Advanced Institute of Science and Technology (JAIST).
def _unwrapped_model(model):
    return model.module if hasattr(model, 'module') else model


def _stabilized_gate_modules(model):
    for module in _unwrapped_model(model).modules():
        if hasattr(module, 'grouped_adaptive_gate'):
            yield module


def configure_stabilized_gate(model, epoch, config):
    """Apply the declared freeze and residual-alpha schedule for one epoch."""
    freeze_epochs = int(getattr(config, 'gate_freeze_epochs', 0))
    ramp_epochs = max(int(getattr(config, 'gate_alpha_ramp_epochs', 1)), 1)
    alpha_max = float(getattr(config, 'gate_alpha_max', 0.25))
    frozen = epoch <= freeze_epochs
    if frozen:
        alpha = 0.0
    else:
        ramp_step = min(epoch - freeze_epochs, ramp_epochs)
        alpha = alpha_max * float(ramp_step) / float(ramp_epochs)

    gate_parameter_count = 0
    for module in _stabilized_gate_modules(model):
        stored_alpha = module.grouped_gate_alpha
        if torch.is_tensor(stored_alpha):
            stored_alpha.fill_(alpha)
        else:
            # Backward-compatible fallback for older research snapshots.
            module.grouped_gate_alpha = alpha
        for parameter in module.grouped_adaptive_gate.parameters():
            parameter.requires_grad = not frozen
            gate_parameter_count += parameter.numel()
    return {
        'frozen': frozen,
        'alpha': alpha,
        'gate_parameter_count': gate_parameter_count,
    }


def equal_fusion_regularization(model):
    """Penalize gate residuals away from zero (equal forward/backward fusion)."""
    penalties = []
    for module in _stabilized_gate_modules(model):
        gate_delta = getattr(
            module, '_grouped_gate_delta_for_regularization', None
        )
        if gate_delta is not None:
            penalties.append(gate_delta.float().pow(2).mean())
    if not penalties:
        return None
    return torch.stack(penalties).mean()


def train_one_epoch(train_loader,
                    model,
                    criterion,
                    optimizer,
                    scheduler,
                    epoch,
                    logger,
                    config,
                    scaler=None):
    '''
    train model for one epoch
    '''
    stime = time.time()
    model.train()
    gate_state = configure_stabilized_gate(model, epoch, config)
    reg_weight = float(getattr(config, 'equal_fusion_reg_weight', 0.0))
    clip_norm = float(getattr(config, 'gradient_clip_norm', 0.0))
    gate_message = (
        f"E4v2 gate state: epoch {epoch}, frozen: {gate_state['frozen']}, "
        f"alpha: {gate_state['alpha']:.6f}, regularizer_weight: {reg_weight}, "
        f"gradient_clip_norm: {clip_norm}"
    )
    print(gate_message)
    logger.info(gate_message)

    loss_list = []

    for iter, data in enumerate(train_loader):
        optimizer.zero_grad()

        images, targets = data['image'], data['label']
        images, targets = images.cuda(non_blocking=True).float(), targets.cuda(non_blocking=True).float()

        if config.amp:
            with autocast():
                out = model(images)
                segmentation_loss = criterion(out, targets)
                gate_regularizer = equal_fusion_regularization(model)
                regularization_loss = (
                    gate_regularizer * reg_weight
                    if gate_regularizer is not None
                    else segmentation_loss.new_zeros(())
                )
                loss = segmentation_loss + regularization_loss
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            if clip_norm > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), clip_norm)
            scaler.step(optimizer)
            scaler.update()
        else:
            out = model(images)
            segmentation_loss = criterion(out, targets)
            gate_regularizer = equal_fusion_regularization(model)
            regularization_loss = (
                gate_regularizer * reg_weight
                if gate_regularizer is not None
                else segmentation_loss.new_zeros(())
            )
            loss = segmentation_loss + regularization_loss
            loss.backward()
            if clip_norm > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), clip_norm)
            optimizer.step()

        loss_list.append(loss.item())
        lr_by_group = {
            group.get('group_name', f'group_{index}'): group['lr']
            for index, group in enumerate(optimizer.param_groups)
        }
        mean_loss = np.mean(loss_list)
        if iter % config.print_interval == 0:
            log_info = (
                f'train: epoch {epoch}, iter:{iter}, loss: {loss.item():.4f}, '
                f'seg_loss: {segmentation_loss.item():.4f}, '
                f'equal_reg: {regularization_loss.item():.8f}, '
                f'lr_groups: {lr_by_group}'
            )
            print(log_info)
            logger.info(log_info)
    scheduler.step()
    etime = time.time()
    log_info = f'Finish one epoch train: epoch {epoch}, loss: {mean_loss:.4f}, time(s): {etime-stime:.2f}'
    print(log_info)
    logger.info(log_info)
    return mean_loss


def val_heldout_training_cases(val_loader, model, epoch, logger, config):
    """Validate on fixed held-out training cases, never on the test volumes."""
    stime = time.time()
    model.eval()
    case_slices = {}
    with torch.no_grad():
        for data in tqdm(val_loader):
            images = data['image'].cuda(non_blocking=True).float()
            outputs = model(images)
            predictions = torch.argmax(
                torch.softmax(outputs, dim=1), dim=1
            ).cpu().numpy()
            labels = data['label'].cpu().numpy()
            case_names = list(data['case_name'])
            for index, slice_name in enumerate(case_names):
                case_name, slice_index_text = slice_name.rsplit('_slice', 1)
                slice_index = int(slice_index_text)
                prediction = predictions[index]
                label = labels[index]
                if prediction.shape != label.shape:
                    prediction = zoom(
                        prediction,
                        (
                            label.shape[0] / prediction.shape[0],
                            label.shape[1] / prediction.shape[1],
                        ),
                        order=0,
                    )
                case_slices.setdefault(case_name, []).append(
                    (slice_index, prediction.astype(np.int16), label.astype(np.int16))
                )

    per_class = {class_index: [] for class_index in range(1, config.num_classes)}
    empty_penalty = float(
        getattr(config, 'validation_empty_hd95_penalty', 373.13)
    )
    for case_name, slices in sorted(case_slices.items()):
        slices.sort(key=lambda item: item[0])
        prediction = np.stack([item[1] for item in slices], axis=0)
        label = np.stack([item[2] for item in slices], axis=0)
        for class_index in range(1, config.num_classes):
            pred_binary = prediction == class_index
            label_binary = label == class_index
            if not pred_binary.any() and not label_binary.any():
                continue
            if not pred_binary.any() or not label_binary.any():
                dice, hd95 = 0.0, empty_penalty
            else:
                dice = metric.binary.dc(pred_binary, label_binary)
                hd95 = metric.binary.hd95(pred_binary, label_binary)
            per_class[class_index].append((float(dice), float(hd95)))

    class_metrics = []
    for class_index, values in per_class.items():
        if not values:
            continue
        class_dice = float(np.mean([value[0] for value in values]))
        class_hd95 = float(np.mean([value[1] for value in values]))
        class_metrics.append((class_dice, class_hd95))
        logger.info(
            'Held-out class %d mean_dice %f mean_hd95 %f'
            % (class_index, class_dice, class_hd95)
        )
    if not class_metrics:
        raise RuntimeError('Held-out validation produced no organ metrics.')
    mean_dice = float(np.mean([value[0] for value in class_metrics]))
    mean_hd95 = float(np.mean([value[1] for value in class_metrics]))
    message = (
        f'heldout val epoch: {epoch}, mean_dice: {mean_dice}, '
        f'mean_hd95: {mean_hd95}, cases: {sorted(case_slices)}, '
        f'time(s): {time.time() - stime:.2f}'
    )
    print(message)
    logger.info(message)
    return mean_dice, mean_hd95





def val_one_epoch(test_datasets,
                    test_loader,
                    model,
                    epoch,
                    logger,
                    config,
                    test_save_path,
                    val_or_test=False):
    # switch to evaluate mode
    stime = time.time()
    model.eval()
    with torch.no_grad():
        metric_list = 0.0
        i_batch = 0
        for data in tqdm(test_loader):
            img, msk, case_name = data['image'], data['label'], data['case_name'][0]
            metric_i = test_single_volume(img, msk, model, classes=config.num_classes, patch_size=[config.input_size_h, config.input_size_w],
                                    test_save_path=test_save_path, case=case_name, z_spacing=config.z_spacing, val_or_test=val_or_test)
            metric_list += np.array(metric_i)

            logger.info('idx %d case %s mean_dice %f mean_hd95 %f' % (i_batch, case_name,
                        np.mean(metric_i, axis=0)[0], np.mean(metric_i, axis=0)[1]))
            i_batch += 1
        metric_list = metric_list / len(test_datasets)
        performance = np.mean(metric_list, axis=0)[0]
        mean_hd95 = np.mean(metric_list, axis=0)[1]
        for i in range(1, config.num_classes):
            logger.info('Mean class %d mean_dice %f mean_hd95 %f' % (i, metric_list[i-1][0], metric_list[i-1][1]))
        performance = np.mean(metric_list, axis=0)[0]
        mean_hd95 = np.mean(metric_list, axis=0)[1]
        etime = time.time()
        log_info = f'val epoch: {epoch}, mean_dice: {performance}, mean_hd95: {mean_hd95}, time(s): {etime-stime:.2f}'
        print(log_info)
        logger.info(log_info)

    return performance, mean_hd95
