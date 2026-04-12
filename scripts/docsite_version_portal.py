from __future__ import annotations

import html
import json
from functools import lru_cache
from pathlib import Path

from docgen_common import REPO_ROOT
from docsite_html_common import render_template
from docsite_html_nav import render_landing_locale_select
from generate_command_html import page_shell


PORTAL_CONTRACT_PATH = REPO_ROOT / "scripts" / "contracts" / "versioned-docs-portal.json"


@lru_cache(maxsize=1)
def load_versioned_docs_portal() -> dict:
    raw = json.loads(PORTAL_CONTRACT_PATH.read_text(encoding="utf-8"))
    if raw.get("schema") != 1:
        raise ValueError(f"Unsupported portal schema in {PORTAL_CONTRACT_PATH}")
    locales = raw.get("locales")
    if not isinstance(locales, dict):
        raise TypeError(f"{PORTAL_CONTRACT_PATH} must define a locale map")
    return raw


def _portal_locale(locale: str) -> dict:
    locales = load_versioned_docs_portal()["locales"]
    selected = locales.get(locale) or locales.get("en")
    if selected is None:
        raise KeyError(f"No portal locale found for {locale}")
    return selected


def _render_links(items: list[tuple[str, str]]) -> str:
    return "".join(
        f'<li><a href="{html.escape(href)}">{html.escape(label)}</a></li>'
        for label, href in items
    )


def _render_panel(title: str, summary: str, links: list[tuple[str, str]]) -> str:
    return render_template(
        "landing_panel.html.tmpl",
        title=html.escape(title),
        summary=html.escape(summary),
        links_html=_render_links(links),
    )


def _render_section(title: str, summary: str, tasks: list[tuple[str, str, list[tuple[str, str]]]]) -> str:
    tasks_html = "".join(
        render_template(
            "landing_task.html.tmpl",
            title=html.escape(task_title),
            summary=html.escape(task_summary),
            links_html=_render_links(task_links),
        )
        for task_title, task_summary, task_links in tasks
    )
    return render_template(
        "landing_section.html.tmpl",
        title=html.escape(title),
        summary=html.escape(summary),
        inline_html="",
        tasks_html=tasks_html,
    )


def _portal_copy(locale: str, *, latest_lane: str | None, version_lanes: list[str], has_dev: bool) -> tuple[dict, list[tuple[str, str]]]:
    copy = _portal_locale(locale)
    lane_links: list[tuple[str, str]] = []
    lane_labels = copy["lane_labels"]
    if latest_lane:
        lane_links.append((lane_labels["latest_release"].format(latest_lane=latest_lane), "latest/index.html"))
    if has_dev:
        lane_links.append((lane_labels["dev_preview"], "dev/index.html"))
    lane_links.extend((label, f"{label}/index.html") for label in version_lanes if label != latest_lane)
    return copy, lane_links


def _lane_output_href(lane_href: str, output: str, locale: str) -> str:
    base = lane_href.removesuffix("index.html")
    if output == "handbook":
        return f"{base}handbook/{locale}/index.html"
    if output == "commands":
        return f"{base}commands/{locale}/index.html"
    if output == "man":
        return f"{base}man/index.html"
    raise ValueError(f"Unsupported portal output: {output}")


def _lane_output_links(lane_links: list[tuple[str, str]], *, output: str, locale: str) -> list[tuple[str, str]]:
    return [
        (label, _lane_output_href(href, output, locale))
        for label, href in lane_links
    ]


def _older_lane_links(lane_links: list[tuple[str, str]], *, latest_lane: str | None) -> list[tuple[str, str]]:
    hidden_hrefs = {"latest/index.html", "dev/index.html"}
    if latest_lane:
        hidden_hrefs.add(f"{latest_lane}/index.html")
    return [(label, href) for label, href in lane_links if href not in hidden_hrefs]


def _primary_lane_links(lane_links: list[tuple[str, str]], *, latest_lane: str | None, has_dev: bool) -> list[tuple[str, str]]:
    primary_hrefs = {"latest/index.html"}
    if has_dev:
        primary_hrefs.add("dev/index.html")
    if not latest_lane:
        primary_hrefs.discard("latest/index.html")
    return [(label, href) for label, href in lane_links if href in primary_hrefs]


def render_version_portal(*, latest_lane: str | None, version_lanes: list[str], has_dev: bool) -> str:
    portal_data: dict[str, dict[str, str]] = {}
    default_locale = "en"

    for locale in ("en", "zh-TW"):
        copy, lane_links = _portal_copy(locale, latest_lane=latest_lane, version_lanes=version_lanes, has_dev=has_dev)
        release_section = copy["sections"]["release_lanes"]
        outputs_section = copy["sections"]["available_outputs"]
        outputs_tasks = outputs_section["tasks"]
        primary_lane_links = _primary_lane_links(lane_links, latest_lane=latest_lane, has_dev=has_dev)
        release_tasks = [
            (
                release_section["tasks"]["latest_release"]["title"],
                release_section["tasks"]["latest_release"]["summary"],
                lane_links[:1] if latest_lane else [],
            )
        ]
        if has_dev:
            release_tasks.append(
                (
                    release_section["tasks"]["dev_preview"]["title"],
                    release_section["tasks"]["dev_preview"]["summary"],
                    lane_links[1:2] if latest_lane else lane_links[:1],
                )
            )
        release_tasks.append(
            (
                release_section["tasks"]["older_release_lines"]["title"],
                release_section["tasks"]["older_release_lines"]["summary"],
                _older_lane_links(lane_links, latest_lane=latest_lane),
            )
        )
        portal_data[locale] = {
            "lang": locale,
            "hero_title": copy["hero_title"],
            "hero_summary": copy["hero_summary"],
            "hero_links_html": "".join(
                f'<a class="landing-hero-link" href="{html.escape(href)}">{html.escape(label)}</a>'
                for label, href in lane_links[:2]
            ),
            "sections_html": "".join(
                [
                    _render_section(
                        release_section["title"],
                        release_section["summary"],
                        release_tasks,
                    ),
                    _render_section(
                        outputs_section["title"],
                        outputs_section["summary"],
                        [
                            (
                                outputs_tasks["handbook_html"]["title"],
                                outputs_tasks["handbook_html"]["summary"],
                                _lane_output_links(primary_lane_links, output="handbook", locale=locale),
                            ),
                            (
                                outputs_tasks["command_reference_html"]["title"],
                                outputs_tasks["command_reference_html"]["summary"],
                                _lane_output_links(primary_lane_links, output="commands", locale=locale),
                            ),
                            (
                                outputs_tasks["manpage_html"]["title"],
                                outputs_tasks["manpage_html"]["summary"],
                                _lane_output_links(primary_lane_links, output="man", locale=locale),
                            ),
                        ],
                    ),
                ]
            ),
            "meta_html": "".join(
                [
                    _render_panel(
                        copy["meta"]["how_to_use"]["title"],
                        copy["meta"]["how_to_use"]["summary"],
                        lane_links[:2],
                    ),
                    _render_panel(
                        copy["meta"]["formats"]["title"],
                        copy["meta"]["formats"]["summary"],
                        [
                            (copy["meta"]["formats"]["links"][0], _lane_output_href(primary_lane_links[0][1], "handbook", locale)),
                            (copy["meta"]["formats"]["links"][1], _lane_output_href(primary_lane_links[0][1], "commands", locale)),
                            (copy["meta"]["formats"]["links"][2], _lane_output_href(primary_lane_links[0][1], "man", locale)),
                        ] if primary_lane_links else [],
                    ),
                ]
            ),
            "jump_options_html": (
                f'<option value="" selected>{html.escape(copy["jump_prompt"])}</option>'
                + "".join(
                    f'<option value="{html.escape(href)}">{html.escape(label)}</option>'
                    for label, href in lane_links
                )
            ),
        }

    body_html = (
        '<div class="landing-page portal-page">'
        '<section class="landing-hero">'
        '<div class="landing-hero-inner">'
        f'<h1 id="landing-title" class="landing-title">{html.escape(portal_data[default_locale]["hero_title"])}</h1>'
        f'<p id="landing-summary" class="landing-summary">{html.escape(portal_data[default_locale]["hero_summary"])}</p>'
        f'<div id="landing-hero-links">{portal_data[default_locale]["hero_links_html"]}</div>'
        '</div>'
        '</section>'
        f'<div id="landing-sections" class="landing-sections">{portal_data[default_locale]["sections_html"]}</div>'
        f'<div id="landing-meta" class="landing-meta">{portal_data[default_locale]["meta_html"]}</div>'
        f'<script id="landing-i18n" type="application/json">{json.dumps(portal_data, ensure_ascii=False)}</script>'
        '</div>'
    )
    copy = _portal_locale(default_locale)
    jump_html = render_landing_locale_select("auto") + (
        f'<select id="jump-select" aria-label="Jump"><option value="" selected>{html.escape(copy["jump_prompt"])}</option>'
        + "".join(
            f'<option value="{html.escape(href)}">{html.escape(label)}</option>'
            for label, href in _portal_copy(default_locale, latest_lane=latest_lane, version_lanes=version_lanes, has_dev=has_dev)[1]
        )
        + "</select>"
    )
    return page_shell(
        page_title=copy["page_title"],
        html_lang="en",
        home_href="index.html",
        hero_title="",
        hero_summary="",
        breadcrumbs=[("Home", None)],
        body_html=body_html,
        toc_html="",
        related_html="",
        version_html="",
        locale_html="",
        footer_nav_html="",
        footer_html="Generated by <code>scripts/build_pages_site.py</code>.",
        jump_html=jump_html,
        nav_html="",
        is_landing=True,
    )
