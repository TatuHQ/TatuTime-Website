#!/usr/bin/env python3
"""Dependency-free checks for the static site.

Fails on broken local links, missing assets, duplicate ids, malformed markup,
inline scripts/styles (the container CSP forbids them), external resources and
missing required files. Run with:

    python3 tools/check-site.py
"""
from __future__ import annotations

import os
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}
PAGES = ["index.html", "privacy.html", "404.html"]
REQUIRED = [
    "index.html", "privacy.html", "404.html", "CNAME", "robots.txt",
    "sitemap.xml", "site.webmanifest", "favicon.ico", "css/site.css",
    "js/site.js", "assets/img/og.png",
]
EXTERNAL_SCHEMES = ("http://", "https://", "mailto:", "tel:")


class Page(HTMLParser):
    def __init__(self, path: str):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.stack: list[tuple[str, tuple[int, int]]] = []
        self.errors: list[str] = []
        self.ids: list[str] = []
        self.refs: list[tuple[str, str]] = []  # (attribute, value)
        self.resource_refs: list[str] = []
        self.inline_scripts = 0
        self.inline_styles = 0
        self.title = ""
        self.description = ""
        self.lang = ""
        self.h1 = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "html":
            self.lang = values.get("lang", "")
        if tag == "title":
            self._in_title = True
        if tag == "h1":
            self.h1 += 1
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "meta" and values.get("name") == "description":
            self.description = values.get("content", "")
        if tag == "script" and "src" not in values:
            self.inline_scripts += 1
        if tag == "style" or "style" in values:
            self.inline_styles += 1
        if tag in ("link", "script", "img", "source"):
            for key in ("href", "src", "srcset"):
                if key in values:
                    self.refs.append((key, values[key]))
        if tag == "a" and "href" in values:
            self.refs.append(("href", values["href"]))
        if tag in ("img", "script", "source") and values.get("src"):
            self.resource_refs.append(values["src"])
        if tag == "source" and values.get("srcset"):
            self.resource_refs.append(values["srcset"])
        if tag == "link" and values.get("rel", "").lower() in ("stylesheet", "preload", "modulepreload", "icon", "manifest", "apple-touch-icon"):
            self.resource_refs.append(values.get("href", ""))
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"unexpected </{tag}> at {self.getpos()}")
            return
        top, pos = self.stack.pop()
        if top != tag:
            self.errors.append(f"<{top}> at {pos} closed by </{tag}> at {self.getpos()}")

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def local_target(page_path: str, ref: str):
    """Resolve a reference to a file under site/, or None for external/fragment."""
    if ref.startswith(EXTERNAL_SCHEMES) or ref.startswith("//"):
        return None
    parsed = urlparse(ref)
    if not parsed.path:
        return None
    if parsed.path.startswith("/"):
        return os.path.join(SITE, parsed.path.lstrip("/"))
    return os.path.normpath(os.path.join(os.path.dirname(page_path), parsed.path))


def main() -> int:
    errors: list[str] = []

    for name in REQUIRED:
        if not os.path.exists(os.path.join(SITE, name)):
            errors.append(f"missing required file: site/{name}")

    cname = os.path.join(SITE, "CNAME")
    if os.path.exists(cname):
        value = open(cname, encoding="utf-8").read().strip()
        if value != "tatutime.com":
            errors.append(f"CNAME must be tatutime.com, found {value!r}")

    parsed_pages: dict[str, Page] = {}
    for name in PAGES:
        path = os.path.join(SITE, name)
        if not os.path.exists(path):
            continue
        page = Page(name)
        page.feed(open(path, encoding="utf-8").read())
        parsed_pages[name] = page

        if page.stack:
            errors.append(f"{name}: unclosed tags {[t for t, _ in page.stack]}")
        for error in page.errors:
            errors.append(f"{name}: {error}")
        if page.lang != "en":
            errors.append(f"{name}: <html> must declare lang=\"en\"")
        if not page.title.strip():
            errors.append(f"{name}: empty <title>")
        if not page.description.strip():
            errors.append(f"{name}: empty meta description")
        if page.h1 != 1:
            errors.append(f"{name}: expected exactly one <h1>, found {page.h1}")
        if page.inline_scripts:
            errors.append(f"{name}: inline <script> is blocked by the CSP")
        if page.inline_styles:
            errors.append(f"{name}: inline style is blocked by the CSP")
        duplicates = sorted({i for i in page.ids if page.ids.count(i) > 1})
        if duplicates:
            errors.append(f"{name}: duplicate ids {duplicates}")
        for resource in page.resource_refs:
            if resource.startswith(EXTERNAL_SCHEMES) or resource.startswith("//"):
                errors.append(f"{name}: external resource {resource!r}")

        for attribute, ref in page.refs:
            if attribute == "srcset":
                candidates = [part.strip().split(" ")[0] for part in ref.split(",")]
            else:
                candidates = [ref]
            for candidate in candidates:
                if not candidate or candidate.startswith(EXTERNAL_SCHEMES) or candidate.startswith("#"):
                    continue
                if candidate.startswith("//"):
                    errors.append(f"{name}: protocol-relative resource {candidate!r}")
                    continue
                target = local_target(path, candidate)
                if target and not os.path.exists(target):
                    errors.append(f"{name}: missing local target {candidate!r}")

            # Same-page anchors exist.
            if ref.startswith("#") and len(ref) > 1 and ref[1:] not in page.ids:
                errors.append(f"{name}: missing same-page anchor {ref!r}")

    # Cross-page anchors such as ./#features.
    for name, page in parsed_pages.items():
        for _, ref in page.refs:
            if ref.startswith(EXTERNAL_SCHEMES) or ref.startswith("#"):
                continue
            parsed = urlparse(ref)
            if not parsed.fragment:
                continue
            target = local_target(os.path.join(SITE, name), ref)
            if target and target.endswith(".html") and os.path.exists(target):
                rel = os.path.relpath(target, SITE)
                target_page = parsed_pages.get(rel)
                if target_page and parsed.fragment not in target_page.ids:
                    errors.append(f"{name}: {ref!r} points at missing id {parsed.fragment!r} in {rel}")

    if errors:
        print("Site checks failed:\n")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"Site checks passed: {len(parsed_pages)} pages, {sum(len(p.refs) for p in parsed_pages.values())} references.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
