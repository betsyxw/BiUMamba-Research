#!/usr/bin/env python3
"""Hash the frozen result tree and build public/private Step 20 packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def all_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name not in {"SHA256SUMS.txt", "FILE_MANIFEST_STEP20.tsv", "final_hash_and_pack.log"}:
            yield path


def is_public_step20(rel: Path) -> bool:
    text = rel.as_posix()
    if "medical_images_DO_NOT_UPLOAD_GITHUB" in text:
        return False
    allowed = (
        "README.md",
        "statistics/",
        "qualitative_figures/error_analysis/",
        "qualitative_figures/fixed_selection_v2/",
        "manifests/STEP20_STEP20_5_COMPLETION.json",
        "manifests/step20_step205_completion.log",
        "manifests/step20_step205_report_generation.log",
        "manifests/fixed_qualitative_render.log",
        "manifests/SHA256SUMS.txt",
        "manifests/FILE_MANIFEST_STEP20.tsv",
        "repro_scripts/",
    )
    return text == "README.md" or any(text.startswith(prefix) for prefix in allowed if prefix.endswith("/")) or text in allowed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("/workspace/paper_final_results_v2"))
    parser.add_argument("--output-dir", type=Path, default=Path("/workspace/download_packages"))
    parser.add_argument("--skip-full-hash", action="store_true")
    args = parser.parse_args()
    root, output = args.root, args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    records = []
    if not args.skip_full_hash:
        for path in all_files(root):
            rel = path.relative_to(root)
            records.append((rel.as_posix(), path.stat().st_size, digest(path)))
        manifest_dir = root / "manifests"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        (manifest_dir / "SHA256SUMS.txt").write_text("".join(f"{sha}  {name}\n" for name, _, sha in records), encoding="utf-8")
        (manifest_dir / "FILE_MANIFEST_STEP20.tsv").write_text(
            "relative_path\tsize_bytes\tsha256\n" + "".join(f"{name}\t{size}\t{sha}\n" for name, size, sha in records),
            encoding="utf-8",
        )

    public_zip = output / "BiUMamba_Step20_Step20_5_GitHub_Safe_20260906.zip"
    with zipfile.ZipFile(public_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in all_files(root):
            rel = path.relative_to(root)
            if is_public_step20(rel):
                archive.write(path, Path("paper_final_results_v2") / rel)
        for rel in (Path("manifests/SHA256SUMS.txt"), Path("manifests/FILE_MANIFEST_STEP20.tsv")):
            archive.write(root / rel, Path("paper_final_results_v2") / rel)

    professor_zip = output / "BiUMamba_Step20_Step20_5_Professor_With_Images_20260906.zip"
    private_prefixes = (
        "statistics/",
        "qualitative_figures/error_analysis/",
        "qualitative_figures/fixed_selection_v2/",
        "manifests/STEP20_STEP20_5_COMPLETION.json",
        "manifests/SHA256SUMS.txt",
        "manifests/FILE_MANIFEST_STEP20.tsv",
        "repro_scripts/",
    )
    with zipfile.ZipFile(professor_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in all_files(root):
            rel = path.relative_to(root)
            text = rel.as_posix()
            if any(text.startswith(prefix) for prefix in private_prefixes):
                archive.write(path, Path("paper_final_results_v2") / rel)
        for rel in (Path("manifests/SHA256SUMS.txt"), Path("manifests/FILE_MANIFEST_STEP20.tsv")):
            archive.write(root / rel, Path("paper_final_results_v2") / rel)

    package_manifest = {
        "root_file_count_hashed": len(records),
        "public_zip": {"path": str(public_zip), "size_bytes": public_zip.stat().st_size, "sha256": digest(public_zip)},
        "professor_zip": {"path": str(professor_zip), "size_bytes": professor_zip.stat().st_size, "sha256": digest(professor_zip)},
    }
    (output / "BiUMamba_Step20_Step20_5_PACKAGES_20260906.json").write_text(json.dumps(package_manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(package_manifest, indent=2))


if __name__ == "__main__":
    main()
