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

The full 90-epoch FractalDB-60 VMamba encoder pre-training is now running. If
it succeeds, the queue will automatically run three downstream smoke tests
and then the three 300-epoch ACDC experiments. The isolated test set is not
read during training.

Earlier setup attempts stopped before any full training and are not treated as
experimental runs. Only `r4` is the valid queue.
