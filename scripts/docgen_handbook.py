"""Shared handbook metadata for generated HTML manual pages.

This module loads handbook order and navigation structure from a machine-
readable contract so renderer code stays focused on layout behavior.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from docgen_common import REPO_ROOT, relative_href


def get_handbook_root(repo_root: Path = REPO_ROOT) -> Path:
    return repo_root / "docs" / "user-guide"


HANDBOOK_ROOT = get_handbook_root()
HANDBOOK_LOCALES = ("en", "zh-TW")
HANDBOOK_NAV_PATH = REPO_ROOT / "scripts" / "contracts" / "handbook-nav.json"
LOCALE_LABELS = {
    "en": "English",
    "zh-TW": "繁體中文",
}


@dataclass(frozen=True)
class HandbookNavGroup:
    key: str
    files: tuple[str, ...]
    labels: dict[str, str]

    def label_for(self, locale: str) -> str:
        return self.labels[locale]


def _expect_str(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{field} must be a non-empty string")
    return value


def _expect_list(value: object, field: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{field} must be a list")
    return value


def _expect_dict(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{field} must be an object")
    return value


def _load_handbook_nav_contract() -> tuple[tuple[str, ...], tuple[HandbookNavGroup, ...], dict[str, dict[str, str]]]:
    raw = json.loads(HANDBOOK_NAV_PATH.read_text(encoding="utf-8"))
    if raw.get("schema") != 1:
        raise ValueError(f"Unsupported handbook nav schema in {HANDBOOK_NAV_PATH}")

    order = tuple(
        _expect_str(item, f"order[{index}]")
        for index, item in enumerate(_expect_list(raw.get("order"), "order"))
    )

    groups: list[HandbookNavGroup] = []
    for index, group in enumerate(_expect_list(raw.get("nav_groups"), "nav_groups")):
        group_dict = _expect_dict(group, f"nav_groups[{index}]")
        groups.append(
            HandbookNavGroup(
                key=_expect_str(group_dict.get("key"), f"nav_groups[{index}].key"),
                labels={
                    "en": _expect_str(group_dict.get("label_en"), f"nav_groups[{index}].label_en"),
                    "zh-TW": _expect_str(group_dict.get("label_zh_tw"), f"nav_groups[{index}].label_zh_tw"),
                },
                files=tuple(
                    _expect_str(item, f"nav_groups[{index}].files[{file_index}]")
                    for file_index, item in enumerate(_expect_list(group_dict.get("files"), f"nav_groups[{index}].files"))
                ),
            )
        )

    nav_titles: dict[str, dict[str, str]] = {}
    for locale, titles in _expect_dict(raw.get("nav_titles"), "nav_titles").items():
        title_map = _expect_dict(titles, f"nav_titles.{locale}")
        nav_titles[locale] = {
            stem: _expect_str(value, f"nav_titles.{locale}.{stem}")
            for stem, value in title_map.items()
        }

    return order, tuple(groups), nav_titles


HANDBOOK_ORDER, HANDBOOK_NAV_GROUPS, HANDBOOK_NAV_TITLES = _load_handbook_nav_contract()
HANDBOOK_NAV_GROUP_LABELS = {
    locale: {group.key: group.label_for(locale) for group in HANDBOOK_NAV_GROUPS}
    for locale in HANDBOOK_LOCALES
}


@dataclass(frozen=True)
class HandbookPage:
    locale: str
    source_path: Path
    output_rel: str
    stem: str
    title: str
    previous_output_rel: str | None
    previous_title: str | None
    next_output_rel: str | None
    next_title: str | None
    language_switch_rel: str | None
    chapter_number: int
    total_chapters: int
    part_key: str
    part_number: int


def _validate_handbook_nav_groups() -> None:
    nav_files = [filename for group in HANDBOOK_NAV_GROUPS for filename in group.files]
    if len(nav_files) != len(set(nav_files)):
        raise ValueError("HANDBOOK_NAV_GROUPS must not contain duplicate handbook files")
    if set(nav_files) != set(HANDBOOK_ORDER):
        raise ValueError("HANDBOOK_NAV_GROUPS must cover HANDBOOK_ORDER exactly")


def parse_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ").title()


def existing_handbook_files(locale: str, handbook_root: Path = HANDBOOK_ROOT) -> list[str]:
    if locale not in HANDBOOK_LOCALES:
        raise ValueError(f"Unsupported handbook locale: {locale}")
    locale_dir = handbook_root / locale
    return [filename for filename in HANDBOOK_ORDER if (locale_dir / filename).exists()]


def build_handbook_pages(locale: str, handbook_root: Path = HANDBOOK_ROOT) -> list[HandbookPage]:
    """Build the ordered handbook page list for one locale."""
    if locale not in HANDBOOK_LOCALES:
        raise ValueError(f"Unsupported handbook locale: {locale}")
    locale_dir = handbook_root / locale
    filenames = existing_handbook_files(locale, handbook_root)
    output_rels = [f"handbook/{locale}/{Path(name).with_suffix('.html').as_posix()}" for name in filenames]
    titles = [parse_title(locale_dir / filename) for filename in filenames]
    part_numbers = {group.key: index + 1 for index, group in enumerate(HANDBOOK_NAV_GROUPS)}
    pages: list[HandbookPage] = []
    for index, filename in enumerate(filenames):
        source_path = locale_dir / filename
        output_rel = output_rels[index]
        part_key = next(group.key for group in HANDBOOK_NAV_GROUPS if filename in group.files)
        other_locale = next((candidate for candidate in HANDBOOK_LOCALES if candidate != locale), None)
        other_output_rel = None
        if other_locale is not None:
            other_source_path = handbook_root / other_locale / filename
            if other_source_path.exists():
                other_output_rel = f"handbook/{other_locale}/{Path(filename).with_suffix('.html').as_posix()}"
        pages.append(
            HandbookPage(
                locale=locale,
                source_path=source_path,
                output_rel=output_rel,
                stem=Path(filename).stem,
                title=titles[index],
                previous_output_rel=output_rels[index - 1] if index > 0 else None,
                previous_title=titles[index - 1] if index > 0 else None,
                next_output_rel=output_rels[index + 1] if index + 1 < len(output_rels) else None,
                next_title=titles[index + 1] if index + 1 < len(output_rels) else None,
                language_switch_rel=other_output_rel,
                chapter_number=index + 1,
                total_chapters=len(filenames),
                part_key=part_key,
                part_number=part_numbers[part_key],
            )
        )
    return pages


def handbook_language_href(page: HandbookPage) -> str | None:
    if page.language_switch_rel is None:
        return None
    return relative_href(page.output_rel, page.language_switch_rel)


_validate_handbook_nav_groups()
