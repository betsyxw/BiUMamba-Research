# ACDC FractalDB-60 pilot launch status

- Status: running.
- Valid queue: `r4`.
- Started: 2026-09-03 02:36:23 UTC.
- Platform: RunPod NVIDIA GeForce RTX 4090.
- Protocol: `acdc_fractaldb60_pilot_v1`.
- Downstream model: E2_modify_2.
- Downstream split: fixed 18/70 training patients, unchanged 10 validation
  patients and unchanged 20 isolated-test patients.
- Seed: 42.
- Conditions: scratch, ImageNet and FractalDB-60.
- Server run directory:
  `/workspace/runs/acdc_fractaldb60_pilot_v1_seed42_runpod_r4`.

The FractalDB-60 archive was checked as 60 classes and 60,000 PNG images. The
VMamba encoder pre-training smoke test completed one epoch on a deterministic
64-image subset. It used 1,877,671,936 peak allocated GPU bytes and produced a
checkpoint with SHA-256
`e232b0776b2be1bcfe8c3be9d5689d772b3d1dd7e030aae966d0baf1ce79ab2f`.

The full 90-epoch FractalDB-60 VMamba encoder pre-training completed normally
on 2026-09-03 UTC. It used all 60,000 images, reached final training accuracy
`0.9998333`, and produced
`fractaldb60_vmamba_encoder_epoch90.pth` with SHA-256
`ba5d60a0b4f260b28f3acc5726c31706b2ce4c67f7adcfc48a209fc807a07c37`.

The original queue then stopped before downstream training because the
partial RunPod source deployment omitted two ACDC protocol modules:
`checkpointing.py` and `validation_acdc_v1.py`. No downstream epoch was run
under the failed attempt, and the completed pre-training checkpoint was not
affected. The missing files were restored with hashes verified against the
local repository. A dedicated downstream-resume queue was added with an
import preflight so the 90-epoch pre-training is not repeated.

All three downstream smoke tests (scratch, ImageNet and FractalDB-60) passed.
The FractalDB initialization audit matched all 117 encoder tensors and mirrored
91 decoder tensors. The resumed queue is now running the three downstream
300-epoch ACDC experiments in the frozen order: scratch, ImageNet and
FractalDB-60. The isolated test set is not read during training.

Earlier setup attempts stopped before any full training and are not treated as
experimental runs. Only `r4` is the valid queue.
