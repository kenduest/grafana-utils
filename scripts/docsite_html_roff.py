from __future__ import annotations

import html
import re
from collections.abc import Callable

ROFF_FONT_TOKEN_RE = re.compile(r"\\f[BRI]|\\fR")
MANPAGE_REF_RE = re.compile(r"(?<![A-Za-z0-9-])(grafana-util(?:-[A-Za-z0-9]+)*)\(1\)")
STRONG_MANPAGE_REF_RE = re.compile(r"<strong>(grafana-util(?:-[A-Za-z0-9]+)*)</strong>\(1\)")


def normalize_roff_text(text: str) -> str:
    return text.replace(r"\-", "-").replace(r"\(bu", "•")


def render_roff_inline(text: str) -> str:
    pieces = []
    stack = []
    cursor = 0
    for match in ROFF_FONT_TOKEN_RE.finditer(text):
        if match.start() > cursor:
            pieces.append(html.escape(normalize_roff_text(text[cursor:match.start()])))
        token = match.group(0)
        if token == r"\fB":
            pieces.append("<strong>")
            stack.append("strong")
        elif token == r"\fI":
            pieces.append("<em>")
            stack.append("em")
        elif token == r"\fR" and stack:
            pieces.append(f"</{stack.pop()}>")
        cursor = match.end()
    if cursor < len(text):
        pieces.append(html.escape(normalize_roff_text(text[cursor:])))
    while stack:
        pieces.append(f"</{stack.pop()}>")
    return "".join(pieces)


def render_roff_macro_text(line: str) -> str:
    if line.startswith(".B "):
        return f"<strong>{render_roff_inline(line[3:])}</strong>"
    if line.startswith(".I "):
        return f"<em>{render_roff_inline(line[3:])}</em>"
    return render_roff_inline(line)


def is_cli_command_line(line: str) -> bool:
    """Return true when a roff paragraph line is really a CLI example."""
    normalized = normalize_roff_text(line).strip()
    return normalized.startswith("grafana-util ")


def man_section_id(heading: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
    return slug or "section"


def render_roff_manpage_html(roff_text_body: str, manpage_href: Callable[[str], str | None] | None = None) -> str:
    body_parts = []
    section_parts = []
    paragraph_lines = []
    bullet_items = []
    definition_items = []
    definition_term = None
    definition_desc = []
    code_lines = []
    current_heading = None
    in_code_block = False
    pending_bullet = False
    expecting_definition_term = False

    def flush_paragraph():
        nonlocal paragraph_lines
        if paragraph_lines:
            if len(paragraph_lines) == 1 and is_cli_command_line(paragraph_lines[0]):
                section_parts.append(
                    f'<pre class="man-example"><code>{html.escape(normalize_roff_text(paragraph_lines[0]).strip())}</code></pre>'
                )
                paragraph_lines = []
                return
            section_parts.append("<p>" + " ".join(render_roff_macro_text(line) if line.startswith((".B ", ".I ")) else render_roff_inline(line) for line in paragraph_lines) + "</p>")
            paragraph_lines = []

    def flush_bullets():
        nonlocal bullet_items
        if bullet_items:
            section_parts.append('<ul class="man-bullets">' + "".join(f"<li>{item}</li>" for item in bullet_items) + "</ul>")
            bullet_items = []

    def flush_definition():
        nonlocal definition_term, definition_desc
        if definition_term is not None:
            definition_items.append((definition_term, " ".join(render_roff_inline(line) for line in definition_desc).strip()))
            definition_term = None
            definition_desc = []

    def flush_definitions():
        nonlocal definition_items
        flush_definition()
        if definition_items:
            section_parts.append('<dl class="man-definitions">' + "".join(f"<dt>{term}</dt><dd>{desc}</dd>" for term, desc in definition_items) + "</dl>")
            definition_items = []

    def flush_code():
        nonlocal code_lines
        if code_lines:
            section_parts.append(f'<pre class="man-example"><code>{html.escape(chr(10).join(code_lines))}</code></pre>')
            code_lines = []

    def flush_section_content():
        flush_paragraph()
        flush_bullets()
        flush_definitions()
        flush_code()

    def render_section() -> str:
        content = "".join(section_parts)
        if current_heading == "SUBCOMMAND MANPAGES":
            content = re.sub(
                r'<h3 class="man-subsection">([^<]+)</h3>(<dl class="man-definitions">.*?</dl>)',
                r'<details class="man-subcommand-group"><summary>\1</summary>\2</details>',
                content,
            )
            return f'<section class="man-section man-section-subcommand-index"><h2 id="{html.escape(man_section_id(current_heading), quote=True)}">{html.escape(current_heading)}</h2>{content}</section>'
        return f'<section class="man-section"><h2 id="{html.escape(man_section_id(current_heading), quote=True)}">{html.escape(current_heading)}</h2>{content}</section>'

    def link_manpage_refs(rendered: str) -> str:
        if manpage_href is None:
            return rendered

        def replace_strong(match: re.Match[str]) -> str:
            stem = match.group(1)
            href = manpage_href(stem)
            if not href:
                return match.group(0)
            return f'<strong><a class="manpage-ref" href="{html.escape(href, quote=True)}">{stem}(1)</a></strong>'

        def replace(match: re.Match[str]) -> str:
            stem = match.group(1)
            href = manpage_href(stem)
            if not href:
                return match.group(0)
            return f'<a class="manpage-ref" href="{html.escape(href, quote=True)}">{match.group(0)}</a>'

        return STRONG_MANPAGE_REF_RE.sub(replace_strong, MANPAGE_REF_RE.sub(replace, rendered))

    def emit_section():
        nonlocal section_parts
        flush_section_content()
        if current_heading is not None:
            body_parts.append(render_section())
            section_parts = []

    for raw_line in roff_text_body.splitlines():
        line = raw_line.rstrip()
        if in_code_block:
            if line == ".EE":
                in_code_block = False
                flush_code()
            else:
                code_lines.append(line)
            continue
        if pending_bullet:
            bullet_items.append(render_roff_inline(line))
            pending_bullet = False
            continue
        if expecting_definition_term:
            definition_term = render_roff_macro_text(line)
            definition_desc = []
            expecting_definition_term = False
            continue
        if line.startswith('.\\"') or line.startswith(".TH"):
            continue
        if line.startswith(".SH "):
            emit_section()
            current_heading = normalize_roff_text(line[4:])
            continue
        if line.startswith(".SS "):
            flush_paragraph()
            flush_bullets()
            flush_definitions()
            flush_code()
            section_parts.append(f'<h3 class="man-subsection">{html.escape(normalize_roff_text(line[4:]))}</h3>')
            continue
        if line == ".PP":
            flush_paragraph()
            flush_bullets()
            flush_definitions()
            continue
        if line.startswith(".IP "):
            flush_paragraph()
            flush_definitions()
            pending_bullet = True
            continue
        if line == ".TP":
            flush_paragraph()
            flush_bullets()
            flush_definition()
            expecting_definition_term = True
            continue
        if line == ".EX":
            flush_paragraph()
            flush_bullets()
            flush_definitions()
            in_code_block = True
            code_lines = []
            continue
        if definition_term is not None:
            definition_desc.append(line)
        else:
            paragraph_lines.append(line)

    emit_section()
    if not body_parts and section_parts:
        body_parts.extend(section_parts)
    return '<div class="manpage-rendered">' + link_manpage_refs("".join(body_parts)) + "</div>"
