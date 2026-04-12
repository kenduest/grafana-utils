from __future__ import annotations

from pathlib import Path

from docgen_common import relative_href
from docsite_html_common import prefixed_output_rel

HANDBOOK_CONTEXT_BY_COMMAND = {
    "index": "index",
    "config": "getting-started",
    "dashboard": "dashboard",
    "datasource": "datasource",
    "alert": "alert",
    "access": "access",
    "status": "status-workspace",
    "workspace": "status-workspace",
    "overview": "status-workspace",
    "snapshot": "status-workspace",
    "profile": "getting-started",
}


def command_handbook_context(locale, output_rel, source_name, config):
    stem = Path(source_name).stem
    root = stem.split("-", 1)[0]
    handbook_stem = HANDBOOK_CONTEXT_BY_COMMAND.get(stem) or HANDBOOK_CONTEXT_BY_COMMAND.get(root)
    if not handbook_stem:
        return None
    return ("Matching handbook chapter", relative_href(output_rel, prefixed_output_rel(config, f"handbook/{locale}/{handbook_stem}.html")))


def rewrite_markdown_link(source_path, output_rel, target, config):
    if target.startswith(("http", "mailto:", "#")):
        return target
    bare, frag = (target.split("#", 1) + [""])[:2]
    resolved = (source_path.parent / bare).resolve()
    if resolved == (config.source_root / "docs" / "DEVELOPER.md").resolve():
        rel = "developer.html"
    else:
        try:
            rel = resolved.relative_to(config.source_root / "docs").as_posix()
        except Exception:
            return target
    if rel.startswith("commands/") and rel.endswith(".md"):
        rel = rel[:-3] + ".html"
    elif rel.startswith("user-guide/") and rel.endswith(".md"):
        rel = rel.replace("user-guide/", "handbook/", 1)[:-3] + ".html"
    href = relative_href(output_rel, prefixed_output_rel(config, rel))
    return f"{href}#{frag}" if frag else href
