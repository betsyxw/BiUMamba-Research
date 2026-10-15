# E3: Grouped-2D Bidirectional Static Learnable Fusion

## Experimental role

E3 changes only the fusion rule of E2_modify_2. The channel grouping,
horizontal/vertical scan coverage, directional parameter slices, optimizer,
dataset split, seed, input resolution, and training protocol remain unchanged.

## Fusion rule

For each SS2D block and each spatial axis, E3 learns two input-independent
logits for the forward and backward outputs:

`w_axis = 2 * softmax(logits_axis)`

`y_axis = w_forward * y_forward + w_backward * y_backward`

There are four new scalar logits per SS2D block: two for the horizontal group
and two for the vertical group. The factor 2 keeps each pair's sum equal to 2.
With zero initialization, the weights are exactly `[1, 1]`, making the initial
E3 function mathematically equivalent to E2_modify_2 fixed sum.

## Controlled comparison

- E2_modify_2: fixed `[1, 1]` direction weights.
- E3: static, learnable, input-independent direction weights.
- E4 (separate future source version): input-dependent adaptive gate built on
  the same grouped-2D coverage.

E4 must not be enabled in the E3 run. This keeps the E2_modify_2-to-E3
comparison attributable only to static learnability.

## Required pre-training checks

1. E3 output equals E2_modify_2 output at initialization.
2. Full-model forward and backward complete without error.
3. Every static fusion parameter receives a finite, non-zero gradient.
4. Horizontal and vertical directional parameter slices retain gradients.
5. Loss and peak GPU memory are recorded.
