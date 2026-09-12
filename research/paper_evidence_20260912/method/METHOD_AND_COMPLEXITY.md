# BiUMamba method and scan-core complexity

Let the input feature map be $X \in \mathbb{R}^{H\times W\times C}$. Original SS2D constructs horizontal forward, horizontal backward, vertical forward, and vertical backward sequences. Each path processes all $C$ channels. Ignoring shared constants inside the selective-scan implementation, its directional scan-core workload is proportional to

\[
W_{\mathrm{E1}} \propto 4HWC.
\]

BiUMamba divides the channels into a horizontal group and a vertical group, each containing $C/2$ channels. Two opposite directions operate within each group:

\[
W_{\mathrm{BiUMamba}}
\propto 2HW\frac{C}{2}+2HW\frac{C}{2}
=2HWC.
\]

The analytical reduction in directional scan-core workload is therefore

\[
1-\frac{2HWC}{4HWC}=50\%.
\]

This 50% figure refers only to the analytical directional selective-scan core. It is not an exact claim about whole-model FLOPs, peak GPU memory, training time, or wall-clock inference latency. Projections, normalization, convolution, reshaping, concatenation, kernel-launch overhead, and other network operations remain. Whole-model operations are therefore reported separately as estimated profiled operations plus the analytical SS2D contribution.

Unlike horizontal-only E2, BiUMamba does not remove a spatial axis. Unlike E2_modify_1, which alternates the active axis between blocks, BiUMamba retains horizontal and vertical bidirectional processing inside every block. Unlike E1-Narrow, BiUMamba keeps the original model width and changes where directional processing capacity is allocated.
