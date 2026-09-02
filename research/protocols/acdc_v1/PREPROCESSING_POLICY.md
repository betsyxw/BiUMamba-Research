# ACDC v1 Frozen Preprocessing Policy

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

- Source: `mathpluscode/ACDC`, revision `4a312b610f395eda5dc0aa36f087dd6ca9991e41`.
- The downloaded derivative is already resampled to `1 x 1 x 10 mm` and center-cropped to `192 x 192`.
- No further spatial resizing or label-dependent preprocessing is performed.
- Images are converted from uint8 to float32 and divided by 255.
- The single grayscale channel is repeated to three channels for the pretrained VM-UNet.
- Masks remain integer labels: 0 background, 1 right ventricle, 2 myocardium, 3 left ventricle.
- Every ED and ES slice is included; empty 2D slices are not removed.
- Only training images receive the frozen joint rotation/flip augmentation.
- Validation and test data receive no augmentation.
- Validation metrics are computed after reconstructing each 3D patient-phase volume.
- HD95 is measured in millimetres with the NIfTI voxel spacing.
- The 20-patient test set cannot be constructed by the training program.

## Important source limitation

The Hugging Face derivative states that volumes were center-cropped using the
left-ventricle mask centre. This is acceptable for engineering adaptation and
smoke testing, but it is a potential label-assisted preprocessing limitation.
The final paper must either disclose it clearly or reproduce the protocol from
the official raw ACDC release without ground-truth-dependent cropping.
