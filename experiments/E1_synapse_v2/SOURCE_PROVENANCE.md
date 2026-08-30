# E1 Synapse v2 Source Provenance

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

- Baseline: original VM-UNet four-direction SS2D
- Protocol: frozen `research/protocols/synapse_v2`
- Comparison target: E2_modify_2 channel-grouped 2D bidirectional fixed sum

The trainer, validation logic, checkpoint selector, and dataset loader were
mechanically copied from the formal E2_modify_2 `synapse_v2` implementation.
The model construction explicitly overrides only `scan_fusion` to `original`.
