#!/usr/bin/env python3
"""Rebuild the index section of README.md from the entries in topic folders.

An entry is any <topic>/<slug>.md file with a frontmatter block holding at
least `title` and `date`. Entries with `draft: true` are skipped.
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
START = "<!-- index starts -->"
END = "<!-- index ends -->"
RECENT = 5

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(text):
    match = FRONTMATTER.match(text)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip().strip("\"'")
    return fields


def load_entries():
    entries = []
    for path in sorted(ROOT.glob("*/*.md")):
        if path.parts[-2].startswith("."):
            continue
        fields = parse_frontmatter(path.read_text(encoding="utf-8"))
        if "title" not in fields or "date" not in fields:
            print(f"skipping {path.relative_to(ROOT)}: missing title or date", file=sys.stderr)
            continue
        if fields.get("draft", "false").lower() == "true":
            continue
        entries.append(
            {
                "topic": path.parent.name,
                "title": fields["title"],
                "date": fields["date"],
                "path": path.relative_to(ROOT).as_posix(),
            }
        )
    # ISO dates sort correctly as strings.
    entries.sort(key=lambda e: (e["date"], e["title"]), reverse=True)
    return entries


def render(entries):
    if not entries:
        return "Nothing here yet."

    count = len(entries)
    lines = [f"**{count} TIL{'' if count == 1 else 's'}**", "", "### Recent", ""]
    for e in entries[:RECENT]:
        lines.append(f"- [{e['title']}]({e['path']}) ({e['topic']}, {e['date']})")

    by_topic = defaultdict(list)
    for e in entries:
        by_topic[e["topic"]].append(e)

    for topic in sorted(by_topic):
        lines += ["", f"### {topic}", ""]
        for e in by_topic[topic]:
            lines.append(f"- [{e['title']}]({e['path']}) - {e['date']}")
    return "\n".join(lines)


def main():
    readme = README.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        sys.exit(f"README.md needs both {START} and {END} markers")
    head, rest = readme.split(START, 1)
    _, tail = rest.split(END, 1)
    README.write_text(f"{head}{START}\n{render(load_entries())}\n{END}{tail}", encoding="utf-8")


if __name__ == "__main__":
    main()
