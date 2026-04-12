from __future__ import annotations

import html
from pathlib import Path

from docgen_command_docs import command_doc_cli_path, parse_command_page, render_markdown_document
from docgen_common import relative_href
from docgen_handbook import LOCALE_LABELS
from docsite_html_common import (
    html_list,
    prefixed_output_rel,
    render_template,
    render_toc,
    render_version_links,
    strip_heading_decorations,
    strip_leading_h1,
    title_only,
)
from docsite_html_links import command_handbook_context, rewrite_markdown_link
from docsite_html_nav import command_reference_label, render_global_nav, render_jump_select, render_page_locale_select
from docsite_html_page_shell import page_shell

COMMAND_AUDIENCE_HINTS = {
    "dashboard": {
        "en": "Best for SREs, Grafana operators, and responders working with dashboard inventory, inspection, export, policy, or screenshots.",
        "zh-TW": "適合 SRE、Grafana 維運人員，以及要處理 dashboard 盤點、檢查、匯出、政策或截圖的人。",
    },
    "datasource": {
        "en": "Best for operators who manage Grafana data source configuration, dependency checks, and recovery paths.",
        "zh-TW": "適合要管理 Grafana data source 設定、依賴檢查與復原流程的維運人員。",
    },
    "alert": {
        "en": "Best for operators who review alert rules, routes, contact points, and staged alert changes.",
        "zh-TW": "適合要檢查告警規則、通知路由、contact point 與 staged 變更的人。",
    },
    "access": {
        "en": "Best for administrators who work with org, user, team, service account, and token lifecycle operations.",
        "zh-TW": "適合要管理 org、使用者、team、service account 與 token 生命週期的管理者。",
    },
    "config": {
        "en": "Best for anyone setting up repo-local connection defaults, secret handling, and repeatable live-command authentication.",
        "zh-TW": "適合想整理 repo-local 連線預設、secret 處理，以及可重複執行的 live 指令認證方式的人。",
    },
    "profile": {
        "en": "Best for anyone setting up repeatable connection defaults, secret handling, and non-interactive runs.",
        "zh-TW": "適合想整理可重複連線預設、secret 處理與非互動式執行方式的人。",
    },
    "status": {
        "en": "Best for operators who need fast live or staged readiness checks before they change anything.",
        "zh-TW": "適合想在動手前先做 live 或 staged readiness 檢查的人。",
    },
    "workspace": {
        "en": "Best for operators who need one local workspace flow to scan, test, preview, package, and apply staged changes.",
        "zh-TW": "適合想用一條本機 workspace 流程完成掃描、檢查、預覽、打包與套用 staged 變更的人。",
    },
    "overview": {
        "en": "Best for readers who need a fast cross-surface inventory and health overview of the current Grafana estate.",
        "zh-TW": "適合想快速盤點目前 Grafana 環境、先看健康度與資產概況的人。",
    },
    "snapshot": {
        "en": "Best for readers who need a local snapshot bundle for offline review, backup, or handoff work.",
        "zh-TW": "適合需要建立本機 snapshot bundle，做離線檢視、備份或交接的人。",
    },
}


def command_intro_labels(locale: str) -> dict[str, str]:
    if locale == "zh-TW":
        return {"what": "這頁在說什麼", "when": "什麼時候看這頁", "who": "適合誰"}
    return {"what": "What this page covers", "when": "When to open this page", "who": "Who this page is for"}


def command_audience_hint(locale: str, source_path: Path) -> str:
    root = source_path.stem.split("-", 1)[0]
    hints = COMMAND_AUDIENCE_HINTS.get(root)
    if not hints:
        return ""
    return hints.get(locale, "")


def render_command_intro(locale: str, source_path: Path) -> str:
    cli_path = command_doc_cli_path(source_path, "grafana-util " + source_path.stem.replace("-", " "))
    if cli_path is None:
        return ""
    try:
        parsed = parse_command_page(source_path, cli_path)
    except Exception:
        return ""
    labels = command_intro_labels(locale)
    blocks: list[str] = []
    if parsed.purpose:
        blocks.append(render_template("command_intro_block.html.tmpl", label=html.escape(labels["what"]), content_html=f'<p class="command-intro-text">{html.escape(parsed.purpose)}</p>'))
    when_html = ""
    if parsed.when_lines:
        items = "".join(f"<li>{html.escape(line.removeprefix('- ').strip())}</li>" for line in parsed.when_lines)
        when_html = f'<ul class="command-intro-list">{items}</ul>'
    elif parsed.when:
        when_html = f'<p class="command-intro-text">{html.escape(parsed.when)}</p>'
    if when_html:
        blocks.append(render_template("command_intro_block.html.tmpl", label=html.escape(labels["when"]), content_html=when_html))
    audience = command_audience_hint(locale, source_path)
    if audience:
        blocks.append(render_template("command_intro_block.html.tmpl", label=html.escape(labels["who"]), content_html=f'<p class="command-intro-text">{html.escape(audience)}</p>'))
    if not blocks:
        return ""
    return render_template("command_intro.html.tmpl", blocks_html="".join(blocks))


def command_language_switch_href(output_rel, locale, source_name, config):
    other = "zh-TW" if locale == "en" else "en"
    target = config.command_docs_root / other / source_name
    if not target.exists():
        return None, None
    return LOCALE_LABELS[other], relative_href(output_rel, prefixed_output_rel(config, f"commands/{other}/{Path(source_name).with_suffix('.html').as_posix()}"))


def command_breadcrumb_label(locale: str) -> str:
    return command_reference_label(locale)


def render_language_links(current_label, switch_label, switch_href):
    items = [(f"Current: {current_label}", "#")]
    if switch_label and switch_href:
        items.append((f"Switch to {switch_label}", switch_href))
    return html_list(items)


def render_command_page(locale, source_path, output_rel, config):
    doc = render_markdown_document(source_path.read_text(encoding="utf-8"), link_transform=lambda target: rewrite_markdown_link(source_path, output_rel, target, config))
    title = title_only(doc.title or source_path.stem)
    switch_label, switch_href = command_language_switch_href(output_rel, locale, source_path.name, config)
    handbook_link = command_handbook_context(locale, output_rel, source_name=source_path.name, config=config)
    body_html = render_command_intro(locale, source_path) + strip_heading_decorations(strip_leading_h1(doc.body_html))
    breadcrumbs = [("Home", relative_href(output_rel, prefixed_output_rel(config, "index.html"))), (command_breadcrumb_label(locale), None)]
    if source_path.stem != "index":
        breadcrumbs.append((title, None))
    return page_shell(page_title=title, html_lang=locale, home_href=relative_href(output_rel, prefixed_output_rel(config, "index.html")), hero_title=title, hero_summary="", breadcrumbs=breadcrumbs, body_html=body_html, toc_html=render_toc(doc.headings), related_html=html_list([handbook_link]) if handbook_link else "", version_html=render_version_links(output_rel, config), locale_html=render_language_links(LOCALE_LABELS[locale], switch_label, switch_href), footer_nav_html="", footer_html="Source: " + source_path.name, jump_html=render_page_locale_select(LOCALE_LABELS[locale], switch_label, switch_href) + render_jump_select(output_rel, locale, config), nav_html=render_global_nav(output_rel, locale, config))
