from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "rust_maintainability_report.py"


def load_module():
    spec = importlib.util.spec_from_file_location("rust_maintainability_report", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("rust_maintainability_report", module)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RustMaintainabilityReportTests(unittest.TestCase):
    def test_discover_rust_maintainability_findings_reports_oversized_files(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "src"
            source.mkdir()
            path = source / "large.rs"
            path.write_text("\n".join(["fn x() {}"] * 9), encoding="utf-8")

            findings = module.discover_rust_maintainability_findings(
                source,
                source_line_limit=5,
                test_line_limit=5,
                reexport_line_limit=99,
            )

            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].category, "oversized-file")
            self.assertEqual(findings[0].path.resolve(), path.resolve())

    def test_discover_rust_maintainability_findings_reports_reexport_counts(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "src"
            source.mkdir()
            path = source / "mod.rs"
            path.write_text(
                "\n".join(
                    [
                        "pub use crate::alpha::A;",
                        "pub use crate::beta::B;",
                        "pub use crate::gamma::C;",
                    ]
                ),
                encoding="utf-8",
            )

            findings = module.discover_rust_maintainability_findings(
                source,
                source_line_limit=99,
                test_line_limit=99,
                reexport_line_limit=2,
            )

            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].category, "reexport-heavy")
            self.assertEqual(findings[0].detail, "3 pub use lines")
            self.assertEqual(findings[0].path.resolve(), path.resolve())


if __name__ == "__main__":
    unittest.main()
