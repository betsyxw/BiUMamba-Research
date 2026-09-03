# BUSI `busi_v1_clean` Frozen Preprocessing Policy

- Source: public `Dataset_BUSI_with_GT` release (780 images).
- Data-quality reference: Pawłowska, Karwat and Żołek (2023), DOI `10.1016/j.dib.2023.109247`.
- Frozen correction table: `dataset_comment_list.csv`, SHA-256 `e3c2abc0ce027401dc717bf8a7ec76442e30c3cda2df32a0bc8aa197ff1c74a4`.
- The correction table defines duplicate-image groups. One deterministic representative is retained from each acceptable group.
- Groups marked `axilla`, `multiclass`, or `needle` are excluded.
- Multiple masks belonging to one retained image are merged by pixel-wise logical OR.
- Normal images retain an empty binary mask and participate in training.
- Images are converted to RGB, resized without changing the aspect ratio, and symmetrically zero-padded to `224 x 224`.
- Masks use nearest-neighbour resizing and remain binary.
- Only the training split receives the frozen joint augmentation.
- The public release does not include patient identifiers. The split is therefore a fixed, duplicate-cleaned, stratified **image-group split**, not a claimed patient-level split.
- Training code may construct only train and validation datasets. The test list is read only by the final offline evaluator after both formal models finish.
- HD95 is reported in standardized 224-grid pixels because BUSI provides no reliable physical pixel spacing. NSD uses a frozen tolerance of 2 pixels.
