# Step 19 Unified Efficiency Results

This GitHub-safe export contains tables, raw iteration timings, summary JSON files, and the exact benchmark scripts. Checkpoints, deployable state_dict files, medical images, and dataset files are intentionally excluded. State-dict sizes and SHA-256 values remain recorded in the summary JSON files for audit purposes.

## Protocol

- GPU: NVIDIA GeForce RTX 4090 (same pod and software environment)
- Models: E1 (original VM-UNet) and E2_modify_2 (BiUMamba)
- Checkpoint: seed 42 best-validation checkpoint for each dataset and method
- Batch size: 1
- AMP: disabled for all runs
- Inference mode: `model.eval()` with gradients disabled
- Warm-up: 20 forward passes
- Timed iterations: 200 forward passes
- Timing: GPU synchronization immediately before and after every forward pass
- Excluded: data loading, host-to-device transfer, post-processing, metric calculation, and image saving
- Inputs: Synapse 1 x 3 x 224 x 224; ACDC 1 x 3 x 192 x 192; BUSI 1 x 3 x 224 x 224

## Unified inference results

| Dataset | Method | Mean ± SD (ms) | Median (ms) | P95 (ms) | Throughput (images/s) | Peak allocated (GB) | Peak reserved (GB) |
|---|---|---:|---:|---:|---:|---:|---:|
| Synapse | E1 | 4.955 ± 0.544 | 4.835 | 5.956 | 201.80 | 0.171 | 0.191 |
| Synapse | E2_modify_2 | 7.043 ± 0.832 | 6.794 | 8.681 | 141.99 | 0.158 | 0.172 |
| ACDC | E1 | 4.072 ± 0.044 | 4.062 | 4.140 | 245.60 | 0.155 | 0.172 |
| ACDC | E2_modify_2 | 7.280 ± 0.677 | 7.114 | 8.572 | 137.37 | 0.145 | 0.159 |
| BUSI | E1 | 4.901 ± 0.476 | 4.795 | 5.876 | 204.05 | 0.171 | 0.191 |
| BUSI | E2_modify_2 | 6.826 ± 0.560 | 6.710 | 7.906 | 146.50 | 0.158 | 0.172 |

E2_modify_2 reduced inference peak allocated memory by 6.1% to 7.8% and peak reserved memory by 7.3% to 9.9%. However, it increased mean latency by 39.3% to 78.8% in this implementation. Therefore, the results do not support a claim that E2_modify_2 is faster.

## Theoretical efficiency and deployable size

- Parameter counts are essentially unchanged at about 27.43 million.
- Estimated whole-model FLOPs decrease by about 18.3%.
- The analytical SS2D scan-core workload decreases by about 50.0%.
- The deployable FP32 state_dict is about 0.110 GB for both methods.
- Whole-model FLOPs are estimates, not exact values. They combine THOP-profiled layers with analytical SS2D projection and selective-scan calculations, use `1 MAC = 2 FLOPs`, exclude post-processing, and do not fully count elementwise and normalization operations.

## Training-efficiency scope

- ACDC and BUSI training efficiency is summarized over seeds 42, 3407, and 2026 on RTX 4090.
- Synapse same-GPU training comparison uses seed 42 only; the other E1 seeds were trained on Hakusan and were not rerun.
- The stable training phase is defined as epochs 21 to 300, inclusive.
- Epoch totals are separated into training, validation, and other overhead such as checkpoint decisions/saving and logging.

## Safe conclusion

> E2_modify_2 reduces theoretical scan workload and both training and inference memory while keeping segmentation accuracy close to VM-UNet on Synapse and ACDC. The lower theoretical workload does not translate into lower inference latency in the current implementation, and the practical runtime benefit is dataset- and implementation-dependent.

Do not state that E2_modify_2 is faster on all datasets.
