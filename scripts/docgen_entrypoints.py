"""Load and validate shared docs entrypoint metadata from a definition file."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from docgen_common import REPO_ROOT


ENTRYPOINTS_PATH = REPO_ROOT / "scripts" / "contracts" / "docs-entrypoints.json"


@dataclass(frozen=True)
class QuickCommand:
    label: str
    command: str
    target: str


@dataclass(frozen=True)
class JumpCommandEntry:
    label: str
    target: str


@dataclass(frozen=True)
class CommandMapLink:
    command: str
    target: str


@dataclass(frozen=True)
class CommandMapGroup:
    title_en: str
    title_zh_tw: str
    links: tuple[CommandMapLink, ...]

    def title_for(self, locale: str) -> str:
        return self.title_zh_tw if locale == "zh-TW" else self.title_en


def _load_raw() -> dict[str, object]:
    raw = json.loads(ENTRYPOINTS_PATH.read_text(encoding="utf-8"))
    if raw.get("schema") != 1:
        raise ValueError(f"Unsupported docs entrypoint schema in {ENTRYPOINTS_PATH}")
    return raw


RAW = _load_raw()


def _expect_locale_map(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{field} must be a locale-keyed object")
    return value


def _expect_list(value: object, field: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{field} must be a list")
    return value


def _expect_str(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{field} must be a non-empty string")
    return value


def _load_quick_commands() -> dict[str, tuple[QuickCommand, ...]]:
    loaded: dict[str, tuple[QuickCommand, ...]] = {}
    for locale, items in _expect_locale_map(RAW.get("quick_commands"), "quick_commands").items():
        entries: list[QuickCommand] = []
        for index, item in enumerate(_expect_list(items, f"quick_commands.{locale}")):
            if not isinstance(item, dict):
                raise TypeError(f"quick_commands.{locale}[{index}] must be an object")
            entries.append(
                QuickCommand(
                    label=_expect_str(item.get("label"), f"quick_commands.{locale}[{index}].label"),
                    command=_expect_str(item.get("command"), f"quick_commands.{locale}[{index}].command"),
                    target=_expect_str(item.get("target"), f"quick_commands.{locale}[{index}].target"),
                )
            )
        loaded[locale] = tuple(entries)
    return loaded


def _load_jump_entries() -> dict[str, tuple[JumpCommandEntry, ...]]:
    loaded: dict[str, tuple[JumpCommandEntry, ...]] = {}
    for locale, items in _expect_locale_map(RAW.get("jump_command_entries"), "jump_command_entries").items():
        entries: list[JumpCommandEntry] = []
        for index, item in enumerate(_expect_list(items, f"jump_command_entries.{locale}")):
            if not isinstance(item, dict):
                raise TypeError(f"jump_command_entries.{locale}[{index}] must be an object")
            entries.append(
                JumpCommandEntry(
                    label=_expect_str(item.get("label"), f"jump_command_entries.{locale}[{index}].label"),
                    target=_expect_str(item.get("target"), f"jump_command_entries.{locale}[{index}].target"),
                )
            )
        loaded[locale] = tuple(entries)
    return loaded


def _load_handbook_command_maps() -> dict[str, tuple[CommandMapGroup, ...]]:
    loaded: dict[str, tuple[CommandMapGroup, ...]] = {}
    raw_maps = _expect_locale_map(RAW.get("handbook_command_maps"), "handbook_command_maps")
    for handbook_stem, groups in raw_maps.items():
        parsed_groups: list[CommandMapGroup] = []
        for index, group in enumerate(_expect_list(groups, f"handbook_command_maps.{handbook_stem}")):
            if not isinstance(group, dict):
                raise TypeError(f"handbook_command_maps.{handbook_stem}[{index}] must be an object")
            parsed_links: list[CommandMapLink] = []
            for link_index, link in enumerate(_expect_list(group.get("links"), f"handbook_command_maps.{handbook_stem}[{index}].links")):
                if not isinstance(link, dict):
                    raise TypeError(
                        f"handbook_command_maps.{handbook_stem}[{index}].links[{link_index}] must be an object"
                    )
                parsed_links.append(
                    CommandMapLink(
                        command=_expect_str(
                            link.get("command"),
                            f"handbook_command_maps.{handbook_stem}[{index}].links[{link_index}].command",
                        ),
                        target=_expect_str(
                            link.get("target"),
                            f"handbook_command_maps.{handbook_stem}[{index}].links[{link_index}].target",
                        ),
                    )
                )
            parsed_groups.append(
                CommandMapGroup(
                    title_en=_expect_str(group.get("title_en"), f"handbook_command_maps.{handbook_stem}[{index}].title_en"),
                    title_zh_tw=_expect_str(
                        group.get("title_zh_tw"),
                        f"handbook_command_maps.{handbook_stem}[{index}].title_zh_tw",
                    ),
                    links=tuple(parsed_links),
                )
            )
        loaded[handbook_stem] = tuple(parsed_groups)
    aliases = RAW.get("handbook_command_map_aliases", {})
    if aliases:
        alias_map = _expect_locale_map(aliases, "handbook_command_map_aliases")
        for handbook_stem, source_stem in alias_map.items():
            source_key = _expect_str(
                source_stem,
                f"handbook_command_map_aliases.{handbook_stem}",
            )
            if source_key not in loaded:
                raise KeyError(
                    f"handbook_command_map_aliases.{handbook_stem} references unknown map {source_key}"
                )
            loaded[handbook_stem] = loaded[source_key]
    return loaded


QUICK_COMMANDS = _load_quick_commands()
JUMP_COMMAND_ENTRIES = _load_jump_entries()
HANDBOOK_COMMAND_MAPS = _load_handbook_command_maps()
