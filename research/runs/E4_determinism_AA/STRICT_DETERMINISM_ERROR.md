# Strict-determinism compatibility finding

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)  
**GitHub:** [@betsyxw](https://github.com/betsyxw)

The first strict-determinism attempt stopped before completing Epoch 1 because
PyTorch 1.13 reports that its CUDA `nll_loss2d` implementation is not
deterministic. No model architecture, adaptive-gate implementation, dataset,
optimizer, scheduler, or Dice-loss term caused this compatibility error.

For the A/A diagnostic only, the default cross-entropy primitive was replaced
with the mathematically equivalent `log_softmax + gather + mean` expression.
This allowed strict deterministic mode to remain enabled while the Mamba and
adaptive-gate training path was audited. The resulting losses are diagnostic
signals and are not reported as formal E4 segmentation performance.

The original server traceback is intentionally excluded because it contains
environment-specific filesystem paths. The failed attempt returned exit code
`1`; both completed 12-epoch A/A runs returned exit code `0`.
