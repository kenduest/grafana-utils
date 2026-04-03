import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_command_html.py"
SCRIPTS_DIR = REPO_ROOT / "scripts"


def load_module():
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location("generate_command_html", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules.setdefault("generate_command_html", module)
    spec.loader.exec_module(module)
    return module


class GenerateCommandHtmlTests(unittest.TestCase):
    def test_generated_html_matches_checked_in_outputs(self):
        module = load_module()

        generated = module.generate_outputs()
        html_root = REPO_ROOT / "docs" / "html"
        checked_in = {
            path.relative_to(html_root).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted(html_root.rglob("*.html"))
        }
        nojekyll_path = html_root / ".nojekyll"
        if nojekyll_path.exists():
            checked_in[".nojekyll"] = nojekyll_path.read_text(encoding="utf-8")

        self.assertEqual(set(generated), set(checked_in))
        self.assertEqual(generated, checked_in)

    def test_generate_outputs_supports_versioned_lane(self):
        module = load_module()

        config = module.HtmlBuildConfig(
            source_root=REPO_ROOT,
            command_docs_root=REPO_ROOT / "docs" / "commands",
            handbook_root=REPO_ROOT / "docs" / "user-guide",
            output_prefix="v9.9",
            version="9.9.0",
            version_label="v9.9",
            version_links=(
                module.VersionLink("Version portal", "index.html"),
                module.VersionLink("Latest release", "latest/index.html"),
            ),
            raw_manpage_target_rel="v9.9/man/grafana-util.1",
            include_raw_manpages=True,
        )

        generated = module.generate_outputs(config)

        self.assertIn("v9.9/index.html", generated)
        self.assertIn("v9.9/man/index.html", generated)
        self.assertIn("v9.9/man/grafana-util.1", generated)
        self.assertIn("Current: v9.9", generated["v9.9/commands/en/dashboard.html"])
        self.assertIn("../index.html", generated["v9.9/commands/en/dashboard.html"])

    def test_render_manpage_page_renders_structured_html(self):
        module = load_module()

        config = module.HtmlBuildConfig(version="9.9.0")
        roff = "\n".join(
            (
                '.TH TEST 1 "2026-04-04" "grafana-util 9.9.0" "User Commands"',
                ".SH NAME",
                r"grafana\-util\-test \- sample command",
                ".SH DESCRIPTION",
                r"Run \fBgrafana-util test\fR with readable HTML output.",
                r".IP \(bu 2",
                "First bullet",
                ".TP",
                ".B --flag",
                "Flag description",
                ".SH EXAMPLES",
                ".EX",
                "grafana-util test --flag",
                ".EE",
            )
        )

        rendered = module.render_manpage_page("man/test.html", "grafana-util-test.1", roff, config)

        self.assertIn('<div class="manpage-rendered">', rendered)
        self.assertIn("<h2>DESCRIPTION</h2>", rendered)
        self.assertIn("<strong>grafana-util test</strong>", rendered)
        self.assertIn('<ul class="man-bullets">', rendered)
        self.assertIn('<dl class="man-definitions">', rendered)
        self.assertIn('<pre class="man-example"><code>grafana-util test --flag</code></pre>', rendered)
        self.assertNotIn('<pre class="manpage">', rendered)


if __name__ == "__main__":
    unittest.main()
