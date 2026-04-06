import ast
import importlib
import sys
import unittest
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
MODULES = {
    "change_cli": PYTHON_ROOT / "grafana_utils" / "change_cli.py",
    "profile_cli": PYTHON_ROOT / "grafana_utils" / "profile_cli.py",
    "resource_cli": PYTHON_ROOT / "grafana_utils" / "resource_cli.py",
    "overview_cli": PYTHON_ROOT / "grafana_utils" / "overview_cli.py",
    "status_cli": PYTHON_ROOT / "grafana_utils" / "status_cli.py",
    "snapshot_cli": PYTHON_ROOT / "grafana_utils" / "snapshot_cli.py",
}

if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))


class NewCliSurfacesTests(unittest.TestCase):
    def test_new_cli_modules_parse_as_python39_syntax(self):
        for module_name, path in MODULES.items():
            source = path.read_text(encoding="utf-8")
            ast.parse(source, filename=str(path), feature_version=(3, 9))

    def test_profile_parser_exposes_expected_commands(self):
        profile_cli = importlib.import_module("grafana_utils.profile_cli")
        help_text = profile_cli.build_parser().format_help()
        self.assertIn("list", help_text)
        self.assertIn("show", help_text)
        self.assertIn("current", help_text)
        self.assertIn("validate", help_text)
        self.assertIn("add", help_text)
        self.assertIn("example", help_text)

    def test_change_parser_exposes_primary_lane(self):
        change_cli = importlib.import_module("grafana_utils.change_cli")
        help_text = change_cli.build_parser().format_help()
        self.assertIn("inspect", help_text)
        self.assertIn("check", help_text)
        self.assertIn("preview", help_text)
        self.assertIn("apply", help_text)

    def test_resource_parser_exposes_read_only_kinds(self):
        resource_cli = importlib.import_module("grafana_utils.resource_cli")
        help_text = resource_cli.build_parser().format_help()
        self.assertIn("kinds", help_text)
        self.assertIn("describe", help_text)
        self.assertIn("list", help_text)
        self.assertIn("get", help_text)

    def test_overview_and_status_parsers_expose_live_and_staged(self):
        overview_cli = importlib.import_module("grafana_utils.overview_cli")
        status_cli = importlib.import_module("grafana_utils.status_cli")
        overview_help = overview_cli.build_parser().format_help()
        status_help = status_cli.build_parser().format_help()
        self.assertIn("live", overview_help)
        self.assertIn("staged", overview_help)
        self.assertIn("live", status_help)
        self.assertIn("staged", status_help)

    def test_snapshot_parser_exposes_export_and_review(self):
        snapshot_cli = importlib.import_module("grafana_utils.snapshot_cli")
        help_text = snapshot_cli.build_parser().format_help()
        self.assertIn("export", help_text)
        self.assertIn("review", help_text)


if __name__ == "__main__":
    unittest.main()
