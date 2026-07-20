---
name: notion-save
description: Save content or a markdown document to Notion as a new page via the Notion API. Use when the user asks to save, upload, or export something to Notion (e.g. "노션에 저장해줘", "save this to Notion").
---

# notion-save

Save markdown content to Notion as a new page under a parent page, using the
bundled `notion_save.py` script (Python stdlib only, no dependencies).

## Prerequisites (check before running)

1. **Token**: `$NOTION_TOKEN` env var, or the file `~/.claude/notion-token`
   containing the token. If neither exists, ask the user for their Notion
   integration token (from https://www.notion.so/my-integrations) and offer to
   store it in `~/.claude/notion-token` (chmod 600) so future sessions work
   without setup.
2. **Parent page**: the Notion API can only write to pages explicitly shared
   with the integration (page menu `…` → Connections → add the integration).
   If the user hasn't specified where to save, ask for a page URL or name.

## Workflow

1. Compose the content as a markdown file. Write it to the session scratchpad
   directory (do NOT create files in the user's project unless asked).
2. Run:

   ```bash
   python3 ~/.claude/skills/notion-save/notion_save.py \
     --parent "<page URL, 32-hex id, or search query>" \
     --title "<new page title>" \
     --file <path to markdown file>
   ```

   - `--parent` accepts a full Notion URL, a page id, or a plain-text search
     query (resolved via the Notion search API, first match wins).
   - On success the script prints the new page's URL — give it to the user.
   - `--dry-run` prints the converted Notion blocks JSON without calling the
     API (useful to debug conversion issues).

3. If the API returns 404 "Could not find page", the parent page is not shared
   with the integration — tell the user to add the connection on that page and
   retry.

## Supported markdown

Headings (H1–H3), paragraphs, bulleted/numbered lists, code fences (with
language), blockquotes, dividers, tables (first row = header), and inline
bold / italic / `code` / links. Nested list indentation is flattened. Anything
else falls back to plain paragraphs — prefer these constructs when composing.
