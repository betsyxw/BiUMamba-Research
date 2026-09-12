# Limitations

1. BiUMamba did not improve mean segmentation accuracy over E1 under the formal three-seed protocols. The Synapse and ACDC paired analyses found no statistically significant difference, but absence of significance does not prove equivalence or non-inferiority.
2. Performance decreased significantly on BUSI ultrasound. The current evidence does not support generalization across all medical image types.
3. The 50% computation reduction is an analytical estimate for the directional scan core. Whole-model FLOPs are estimated, and measured wall-clock latency did not consistently improve.
4. Peak training memory was reduced on all three datasets, whereas inference memory and latency must be interpreted separately. E1 remained faster in the strict inference benchmark.
5. E2, E2_modify_1, and the fusion variants are exploratory single-seed experiments. Screen50 and Full300 results are not directly comparable.
6. E1-Narrow was evaluated only on Synapse. Its observed inferiority cannot be generalized to ACDC or BUSI without additional experiments.
7. GroupMamba and other recent efficient Vision Mamba models were compared at the architectural and literature level but were not reproduced under the present medical segmentation protocol.
8. The datasets are public research benchmarks and do not establish multi-center clinical validity. External clinical validation remains necessary.
9. Qualitative cases were selected using fixed quantitative rules, but visual interpretation remains descriptive and does not establish causal mechanisms.

