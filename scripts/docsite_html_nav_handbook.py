from __future__ import annotations

import re
from pathlib import Path

from docgen_common import relative_href
from docgen_handbook import (
    HANDBOOK_NAV_GROUP_LABELS,
    HANDBOOK_NAV_GROUPS,
    HANDBOOK_NAV_TITLES,
    build_handbook_pages,
)
from docsite_html_common import prefixed_output_rel, split_display_title


def handbook_surface_label(locale: str) -> str:
    return "Handbook" if locale == "en" else "手冊"


def format_handbook_nav_label(title: str, locale: str, stem: str) -> str:
    override = HANDBOOK_NAV_TITLES.get(locale, {}).get(stem)
    if override:
        return override
    clean = re.sub(r"^[^\w\u4e00-\u9fffA-Za-z]+", "", title).strip()
    main, secondary = split_display_title(clean)
    if locale == "zh-TW" and secondary:
        return main
    return clean or title


def handbook_nav_titles(locale: str, config) -> dict[str, str]:
    pages = build_handbook_pages(locale, handbook_root=config.handbook_root)
    titles: dict[str, str] = {}
    for page in pages:
        stem = Path(page.output_rel).stem
        titles[stem] = format_handbook_nav_label(page.title, locale, stem)
    return titles


def handbook_nav_groups(locale: str, config) -> list[tuple[str, str, list[tuple[str, str, str]]]]:
    titles = handbook_nav_titles(locale, config)
    grouped: list[tuple[str, str, list[tuple[str, str, str]]]] = []
    labels = HANDBOOK_NAV_GROUP_LABELS[locale]
    for group in HANDBOOK_NAV_GROUPS:
        items: list[tuple[str, str, str]] = []
        for filename in group.files:
            stem = Path(filename).stem
            if stem not in titles:
                continue
            target = prefixed_output_rel(config, f"handbook/{locale}/{stem}.html")
            items.append((stem, titles[stem], target))
        if items:
            grouped.append((group.key, labels[group.key], items))
    return grouped


def handbook_group_for_stem(stem: str) -> str | None:
    for group in HANDBOOK_NAV_GROUPS:
        if f"{stem}.md" in group.files:
            return group.key
    return None
