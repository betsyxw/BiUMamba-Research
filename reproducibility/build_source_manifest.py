"""Regenerate the source-only manifest after reviewed source changes."""
from __future__ import annotations
import json
from pathlib import Path
from .model_registry import ROOT, VARIANTS, describe, sha256


def main():
    files = set()
    for method, (directory, _, _) in VARIANTS.items():
        for path in (ROOT / "experiments" / directory).rglob("*"):
            if path.is_file() and path.suffix in {".py", ".md", ".json", ".txt"} and "results" not in path.parts:
                files.add(path)
    for path in (ROOT / "reproducibility").rglob("*"):
        if path.is_file() and path.suffix in {".py", ".md", ".txt"}:
            files.add(path)
    files.update(ROOT / name for name in ["engine_synapse.py", "utils.py", "datasets/dataset.py", "LICENSE"])
    for name in ["experiments/E1_synapse_v2", "experiments/E2_modify_2_synapse_v2",
                 "research/protocols/synapse_v2"]:
        for path in (ROOT / name).rglob("*"):
            if path.is_file() and path.suffix in {".py", ".json", ".txt", ".csv", ".md"}:
                files.add(path)
    files.add(ROOT / "research/protocols/synapse_v1/evaluate_synapse_nifti.py")
    manifest = {"updated": "20261015", "scope": "source_completeness_release_not_numerical_reproduction",
                "models": {method: describe(method) for method in VARIANTS},
                "recovered_archive": {"name": "E2_modify_2_freezed", "recorded_parent_head": "ff97fe28",
                                      "copy_date": "20261015", "contains_original_git_objects": False},
                "files": {p.relative_to(ROOT).as_posix(): sha256(p) for p in sorted(files)}}
    output = ROOT / "reproducibility/SOURCE_MANIFEST.json"
    output.write_text(json.dumps(manifest, indent=2) + "\n")
    print("Recorded {} source files for {} methods".format(len(files), len(VARIANTS)))


if __name__ == "__main__":
    main()
