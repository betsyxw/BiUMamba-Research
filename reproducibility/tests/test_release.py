"""Focused stdlib tests for model selection and source-package isolation."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from reproducibility import model_registry as registry
from reproducibility.verify_release import verify


class ReleaseTests(unittest.TestCase):
    def test_all_six_modes_and_hashes(self):
        report = verify()
        self.assertEqual(len(report["methods"]), 6)
        self.assertEqual(registry.describe("E2")["scan_fusion"], "bidirectional_sum")
        self.assertEqual(registry.describe("E2_modify_2")["scan_fusion"], "grouped_2d_bidirectional_sum")
        self.assertEqual(registry.describe("E4")["scan_fusion"], "grouped_2d_adaptive_gate_v1")

    def test_unknown_method_rejected(self):
        with self.assertRaises(ValueError):
            registry.describe("E5")

    def test_wrong_fusion_rejected_before_import(self):
        with self.assertRaises(ValueError):
            registry.build_model("E2_modify_2", scan_fusion="bidirectional_sum")

    def test_all_descriptions_need_no_torch(self):
        result = subprocess.run([sys.executable, "-m", "reproducibility.model_registry"],
                                cwd=registry.ROOT, capture_output=True, text=True, check=True)
        self.assertEqual(len(json.loads(result.stdout)), 6)

    def test_train_dry_description_selects_correct_source(self):
        for method in registry.VARIANTS:
            result = subprocess.run([sys.executable, "-m", "reproducibility.train_synapse",
                                     "--method", method, "--seed", "42", "--epochs", "300",
                                     "--work-dir", "/nonexistent/output", "--train-npz", "/nonexistent/data",
                                     "--pretrained", "/nonexistent/weights", "--describe-only"],
                                    cwd=registry.ROOT, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout)["scan_fusion"], registry.VARIANTS[method][1])

    def test_relative_imports_do_not_share_model_modules(self):
        # Tiny stand-ins test the actual package loader without pretending to
        # validate numerical PyTorch forwards on a Mac without the CUDA stack.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for method in ["E1", "E2"]:
                base = root / method
                base.mkdir()
                (base / "vmamba.py").write_text("IDENTITY = {!r}\n".format(method))
                (base / "vmunet.py").write_text("from .vmamba import IDENTITY\nclass VMUNet:\n    identity = IDENTITY\n")
            def description(method):
                return {"model_source": method + "/vmamba.py", "wrapper_source": method + "/vmunet.py"}
            names = ["_biumamba_release_" + m + suffix for m in ["E1", "E2"]
                     for suffix in ["", ".vmamba", ".vmunet"]]
            saved = {n: sys.modules.pop(n) for n in names if n in sys.modules}
            try:
                with patch.object(registry, "ROOT", root), patch.object(registry, "describe", description):
                    self.assertEqual(registry.model_class("E1").identity, "E1")
                    self.assertEqual(registry.model_class("E2").identity, "E2")
            finally:
                for n in names:
                    sys.modules.pop(n, None)
                sys.modules.update(saved)


if __name__ == "__main__":
    unittest.main()
