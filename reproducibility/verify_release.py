"""Standard-library release audit: hashes, syntax, configs and dispatch.

This is not a numerical forward/backward test and never starts GPU work.
"""
from __future__ import annotations
import ast
import json
from pathlib import Path
from .model_registry import ROOT, VARIANTS, describe, sha256


def verify():
    checks = []
    for method in VARIANTS:
        info = describe(method)
        config = ast.parse((ROOT / info["config_source"]).read_text())
        settings = [n for n in config.body if isinstance(n, ast.ClassDef) and n.name == "setting_config"]
        assignment = next(n for n in settings[0].body if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == "model_config" for t in n.targets))
        values = ast.literal_eval(assignment.value)
        if values["scan_fusion"] != info["scan_fusion"]:
            raise AssertionError("Wrong config mode: " + method)
        model = ast.parse((ROOT / info["model_source"]).read_text())
        literals = {n.value for n in ast.walk(model) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        if info["scan_fusion"] not in literals:
            raise AssertionError("Source does not expose scan mode: " + method)
        for name in [info["model_source"], info["wrapper_source"], info["config_source"]]:
            compile((ROOT / name).read_text(), name, "exec")
        checks.append({"method": method, "scan_fusion": values["scan_fusion"], "syntax_and_config": "PASS"})
    for path in (ROOT / "reproducibility").glob("*.py"):
        compile(path.read_text(), str(path), "exec")
    manifest = json.loads((ROOT / "reproducibility/SOURCE_MANIFEST.json").read_text())
    for path, expected in manifest["files"].items():
        if sha256(ROOT / path) != expected:
            raise AssertionError("Hash mismatch: " + path)
    return {"status": "PASS_STATIC_RELEASE_AUDIT", "methods": checks,
            "verified_files": len(manifest["files"]), "cuda_forward_backward_tested": False,
            "historical_training_commits_recovered": False}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
