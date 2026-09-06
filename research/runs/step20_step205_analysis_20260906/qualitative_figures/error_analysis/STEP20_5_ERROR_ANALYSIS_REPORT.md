# Step 20.5 Error Analysis and Applicability Boundary

Status: complete for the planned analyses using existing masks; no retraining was performed.

## Objective grouping rules

- Lesion/organ size uses ground-truth area or physical volume tertiles fixed within the dataset. Synapse and ACDC are grouped separately within each organ or structure.
- BUSI shape uses the ground-truth bounding-box width/height ratio: Horizontal >= 1.25, Vertical <= 0.80, and Balanced otherwise.
- BUSI local contrast is an objective lesion-versus-dilated-ring contrast-to-noise ratio, divided into ground-truth-group tertiles.
- Precision, recall, false-positive ratio, and false-negative ratio are computed from the saved prediction masks for every model and seed.

## Main BUSI observations

- Low-contrast lesions showed the clearest Dice decrease: mean E2_modify_2 - E1 = -0.0819, bootstrap 95% CI [-0.1461, -0.0195], Holm p = 0.02051.
- Large lesions also showed a Dice decrease: mean difference = -0.0509, bootstrap 95% CI [-0.0930, -0.0152], Holm p = 0.04099.
- No shape subgroup remained significant after correction; the smallest shape-group Holm p for Dice was 0.1204. The vertical group contains only four units and is exploratory.
- These are associations, not proof that contrast, size, or scan direction alone caused the errors.

## Fixed qualitative selection

Each dataset includes seven unique cases selected before viewing the seed-42 panels: largest decline, largest improvement, both poor, dataset-median typical case, and Small/Medium/Large representatives. The combined figures and individual 300-dpi PNG/PDF panels are under `fixed_selection_v2/<dataset>/medical_images_DO_NOT_UPLOAD_GITHUB/`. Case IDs and numerical values are public in each selection manifest, but medical images and masks must not be uploaded to GitHub.

## Safe conclusion

BiUMamba provides an effective accuracy-memory trade-off on Synapse CT and ACDC MRI. Its segmentation quality decreased on BUSI ultrasound, especially among objectively defined low-contrast lesions in this analysis. The subgroup findings describe an applicability boundary and require confirmation on additional ultrasound datasets.

## Supporting files

- `busi_mask_level_metrics_all_seeds.csv`
- `busi_*_group_summary.csv` and `busi_*_group_paired_statistics.csv`
- `synapse_acdc_per_organ_size_group_*.csv`
- `busi_size_shape_contrast_analysis.png` and `.pdf`
- `fixed_selection_v2/*/selection_manifest_rendered.csv`
