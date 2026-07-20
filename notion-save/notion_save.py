#!/usr/bin/env python3
"""Save a markdown file to Notion as a new page.

Usage:
  python3 notion_save.py --parent "<page URL | page id | search query>" \
                         --title "Page title" --file content.md [--dry-run]

Token resolution order: $NOTION_TOKEN, then ~/.claude/notion-token file.
Only Python stdlib is used (no pip dependencies).
"""

import argparse
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
MAX_TEXT = 2000  # Notion rich-text content limit per item
MAX_CHILDREN = 100  # Notion limit per create/append request


def get_token() -> str:
    token = os.environ.get("NOTION_TOKEN", "").strip()
    if not token:
        token_file = pathlib.Path.home() / ".claude" / "notion-token"
        if token_file.exists():
            token = token_file.read_text().strip()
    if not token:
        sys.exit(
            "error: no token. Set NOTION_TOKEN env var or write the token to "
            "~/.claude/notion-token"
        )
    return token


def api(token: str, method: str, path: str, body: dict | None = None) -> dict:
    request = urllib.request.Request(
        API + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"error: Notion API {e.code} on {method} {path}: {e.read().decode()}")


# --- markdown -> Notion blocks -------------------------------------------

INLINE = re.compile(
    r"(\*\*.+?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|\*[^*\s][^*]*\*)"
)
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

CODE_LANGUAGES = {
    "ts": "typescript",
    "tsx": "typescript",
    "js": "javascript",
    "jsx": "javascript",
    "py": "python",
    "sh": "shell",
    "zsh": "shell",
    "yml": "yaml",
    "md": "markdown",
    "": "plain text",
}


def chunk_text(text: str) -> list[str]:
    return [text[i : i + MAX_TEXT] for i in range(0, len(text), MAX_TEXT)] or [""]


def rich(text: str) -> list[dict]:
    """Parse inline markdown (bold, italic, code, links) into rich text."""
    items: list[dict] = []
    for token in INLINE.split(text):
        if not token:
            continue
        annotations: dict = {}
        content = token
        link = None
        if token.startswith("**") and token.endswith("**") and len(token) > 4:
            content = token[2:-2]
            annotations["bold"] = True
        elif token.startswith("`") and token.endswith("`") and len(token) > 2:
            content = token[1:-1]
            annotations["code"] = True
        elif token.startswith("[") and LINK.fullmatch(token):
            m = LINK.fullmatch(token)
            content, link = m.group(1), m.group(2)
        elif token.startswith("*") and token.endswith("*") and len(token) > 2:
            content = token[1:-1]
            annotations["italic"] = True
        for piece in chunk_text(content):
            item: dict = {"type": "text", "text": {"content": piece}}
            if link:
                item["text"]["link"] = {"url": link}
            if annotations:
                item["annotations"] = dict(annotations)
            items.append(item)
    return items or [{"type": "text", "text": {"content": ""}}]


def code_block(lines: list[str], lang: str) -> dict:
    text = "\n".join(lines)
    return {
        "type": "code",
        "code": {
            "language": CODE_LANGUAGES.get(lang.lower(), lang.lower() or "plain text"),
            "rich_text": [
                {"type": "text", "text": {"content": piece}}
                for piece in chunk_text(text)
            ],
        },
    }


def table_block(rows: list[str]) -> dict | None:
    parsed: list[list[str]] = []
    for row in rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        # skip separator rows like |---|---|
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        parsed.append(cells)
    if not parsed:
        return None
    width = max(len(r) for r in parsed)
    children = []
    for cells in parsed:
        cells = cells + [""] * (width - len(cells))
        children.append(
            {
                "type": "table_row",
                "table_row": {"cells": [rich(c) for c in cells]},
            }
        )
    return {
        "type": "table",
        "table": {
            "table_width": width,
            "has_column_header": True,
            "has_row_header": False,
            "children": children,
        },
    }


def markdown_to_blocks(markdown: str) -> list[dict]:
    blocks: list[dict] = []
    lines = markdown.splitlines()
    i = 0
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(
                {"type": "paragraph", "paragraph": {"rich_text": rich(" ".join(paragraph))}}
            )
            paragraph.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            lang = stripped[3:].strip()
            i += 1
            body: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            blocks.append(code_block(body, lang))
            i += 1
            continue

        if stripped.startswith("|"):
            flush_paragraph()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            table = table_block(rows)
            if table:
                blocks.append(table)
            continue

        if not stripped:
            flush_paragraph()
        elif re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            flush_paragraph()
            blocks.append({"type": "divider", "divider": {}})
        elif stripped.startswith("#"):
            flush_paragraph()
            level = min(len(stripped) - len(stripped.lstrip("#")), 3)
            text = stripped.lstrip("#").strip()
            key = f"heading_{level}"
            blocks.append({"type": key, key: {"rich_text": rich(text)}})
        elif re.match(r"^\s*[-*+]\s+", line):
            flush_paragraph()
            text = re.sub(r"^\s*[-*+]\s+", "", line)
            blocks.append(
                {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rich(text)}}
            )
        elif re.match(r"^\s*\d+[.)]\s+", line):
            flush_paragraph()
            text = re.sub(r"^\s*\d+[.)]\s+", "", line)
            blocks.append(
                {"type": "numbered_list_item", "numbered_list_item": {"rich_text": rich(text)}}
            )
        elif stripped.startswith(">"):
            flush_paragraph()
            text = stripped.lstrip(">").strip()
            blocks.append({"type": "quote", "quote": {"rich_text": rich(text)}})
        else:
            paragraph.append(stripped)
        i += 1

    flush_paragraph()
    return blocks


# --- parent resolution ----------------------------------------------------

def resolve_parent(token: str, parent: str) -> str:
    compact = parent.replace("-", "")
    m = re.search(r"[0-9a-f]{32}", compact, re.IGNORECASE)
    if m:
        raw = m.group(0).lower()
        return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"
    result = api(
        token,
        "POST",
        "/search",
        {"query": parent, "filter": {"value": "page", "property": "object"}},
    )
    pages = result.get("results", [])
    if not pages:
        sys.exit(
            f"error: no page found for query {parent!r}. Make sure the page is "
            "shared with the integration (page menu ... > Connections)."
        )
    return pages[0]["id"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parent", required=True, help="parent page URL, id, or search query")
    ap.add_argument("--title", required=True, help="title of the new page")
    ap.add_argument("--file", required=True, help="markdown file to upload")
    ap.add_argument("--dry-run", action="store_true", help="print blocks JSON, no API calls")
    args = ap.parse_args()

    markdown = pathlib.Path(args.file).read_text()
    blocks = markdown_to_blocks(markdown)

    if args.dry_run:
        json.dump(blocks, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return

    token = get_token()
    parent_id = resolve_parent(token, args.parent)

    page = api(
        token,
        "POST",
        "/pages",
        {
            "parent": {"page_id": parent_id},
            "properties": {
                "title": {"title": [{"type": "text", "text": {"content": args.title}}]}
            },
            "children": blocks[:MAX_CHILDREN],
        },
    )
    page_id = page["id"]
    for start in range(MAX_CHILDREN, len(blocks), MAX_CHILDREN):
        api(
            token,
            "PATCH",
            f"/blocks/{page_id}/children",
            {"children": blocks[start : start + MAX_CHILDREN]},
        )

    print(page.get("url", page_id))


if __name__ == "__main__":
    main()
