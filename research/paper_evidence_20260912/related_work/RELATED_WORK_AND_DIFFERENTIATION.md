# Related work and method differentiation

VMamba adapts selective state-space modeling to two-dimensional vision through SS2D, which unfolds a feature map along multiple spatial directions. VM-UNet applies this mechanism in a U-shaped medical image segmentation network. In its original form, horizontal forward, horizontal backward, vertical forward, and vertical backward scans each process the complete channel representation.

Recent work has explored more efficient scan organization. EfficientVMamba reduces spatial scan density using atrous selective scanning and combines the resulting global pathway with convolutional processing. LocalMamba uses windowed selective scans and searches scan choices at the layer level. GroupMamba divides channels into four groups, assigns one unidirectional scan to each group, and adds Channel Affinity Modulation to support cross-group communication.

BiUMamba is related to these efficient Vision Mamba designs but uses a different allocation unit. It creates two axis-specific groups. The horizontal group performs forward and backward row-wise scans on half of the channels, and the vertical group performs forward and backward column-wise scans on the remaining half. Thus, every BiUMamba block retains bidirectional modeling on both spatial axes. The grouped outputs are concatenated and mixed through the existing linear projection in the VM-UNet block.

The claim is deliberately limited. BiUMamba is not presented as the first channel-grouped Mamba architecture. Its specific contribution is two-axis bidirectional channel allocation for U-shaped medical image segmentation, together with direction-removal and near-memory-matched width-reduction controls.

## References

- Liu et al., “VMamba: Visual State Space Model,” arXiv:2401.10166. https://arxiv.org/abs/2401.10166
- Ruan and Xiang, “VM-UNet: Vision Mamba UNet for Medical Image Segmentation,” arXiv:2402.02491. https://arxiv.org/abs/2402.02491
- Shaker et al., “GroupMamba: Efficient Group-Based Visual State Space Model,” CVPR 2025, pp. 14912–14922. https://openaccess.thecvf.com/content/CVPR2025/html/Shaker_GroupMamba_Efficient_Group-Based_Visual_State_Space_Model_CVPR_2025_paper.html
- Huang et al., “LocalMamba: Visual State Space Model with Windowed Selective Scan,” ECCV 2024 Workshops, LNCS 15633, pp. 12–22. https://doi.org/10.1007/978-3-031-91979-4_2
- Pei et al., “EfficientVMamba: Atrous Selective Scan for Light Weight Visual Mamba,” AAAI 2025, 39(6), pp. 6443–6451. https://doi.org/10.1609/aaai.v39i6.32690

