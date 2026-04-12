from docsite_html_content_pages import (
    command_breadcrumb_label,
    command_handbook_context,
    command_intro_labels,
    command_language_switch_href,
    handbook_page_eyebrow,
    handbook_page_nav_title,
    render_command_intro,
    render_command_page,
    render_developer_page,
    render_footer_nav,
    render_handbook_page,
    render_language_links,
    rewrite_markdown_link,
)
from docsite_html_landing import (
    build_landing_locale_data as _build_landing_locale_data,
    render_landing_page as _render_landing_page,
)
from docsite_html_manpages import render_manpage_index_page, render_manpage_page, render_roff_manpage_html
from docsite_html_page_shell import page_shell


def build_landing_locale_data(config):
    return _build_landing_locale_data(config, rewrite_markdown_link)


def render_landing_page(config):
    return _render_landing_page(config, rewrite_markdown_link)

__all__ = [
    "build_landing_locale_data",
    "command_breadcrumb_label",
    "command_handbook_context",
    "command_intro_labels",
    "command_language_switch_href",
    "handbook_page_eyebrow",
    "handbook_page_nav_title",
    "page_shell",
    "render_command_intro",
    "render_command_page",
    "render_developer_page",
    "render_footer_nav",
    "render_handbook_page",
    "render_landing_page",
    "render_language_links",
    "render_manpage_index_page",
    "render_manpage_page",
    "render_roff_manpage_html",
    "rewrite_markdown_link",
]
