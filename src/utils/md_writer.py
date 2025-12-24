from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional


class MD_Writer:
    """
    Obsidian-optimized Markdown writer
    """

    def __init__(self, output_file: str):
        self.output_file = output_file
        self.body: List[str] = []

        # Front matter properties
        self.properties: Dict[str, str] = {}

        # Footer metadata
        self.tags: List[str] = []
        self.aliases: List[str] = []

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.properties["created"] = now
        self.properties["modified"] = now

    # -------------------------
    # Core
    # -------------------------
    def _add(self, line: str = ""):
        self.body.append(line)

    def save(self):
        lines: List[str] = []

        # Front matter
        if self.properties:
            lines.append("---")
            for k, v in self.properties.items():
                lines.append(f"{k}: {v}")
            lines.append("---\n")

        # Main body
        lines.extend(self.body)

        # Footer
        if self.tags or self.aliases:
            lines.append("\n---")

        if self.tags:
            tag_line = " ".join(f"#{t.lstrip('#')}" for t in self.tags)
            lines.append(tag_line)

        if self.aliases:
            lines.append("Aliases: " + ", ".join(self.aliases))

        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    # -------------------------
    # Front matter helpers
    # -------------------------
    def title(self, title: str):
        self.properties["title"] = title

    def set_property(self, key: str, value: str):
        self.properties[key] = value

    # -------------------------
    # Structure
    # -------------------------
    def heading(self, text: str, level: int = 1):
        level = max(1, min(level, 6))
        self._add(f"{'#' * level} {text}\n")

    def text(self, text: str):
        self._add(text + "\n")

    def hr(self):
        self._add("---\n")

    # -------------------------
    # Lists
    # -------------------------
    def bullets(self, items: List[str]):
        for i in items:
            self._add(f"- {i}")
        self._add()

    def checklist(self, items: Dict[str, bool]):
        for item, done in items.items():
            mark = "x" if done else " "
            self._add(f"- [{mark}] {item}")
        self._add()

    # -------------------------
    # Links & embeds
    # -------------------------
    def link(self, page: str, alias: Optional[str] = None):
        if alias:
            self._add(f"[[{page}|{alias}]]")
        else:
            self._add(f"[[{page}]]")

    def links(self, pages: List[str]):
        self._add(" ".join(f"[[{p}]]" for p in pages) + "\n")

    def embed(self, page: str):
        self._add(f"![[{page}]]\n")

    # -------------------------
    # Callouts (Obsidian)
    # -------------------------
    def callout(self, kind: str, text: str):
        self._add(f"> [!{kind}]")
        for line in text.splitlines():
            self._add(f"> {line}")
        self._add()

    # -------------------------
    # Code
    # -------------------------
    def code_block(self, code: str, language: str = ""):
        self._add(f"```{language}")
        self._add(code)
        self._add("```\n")

    # -------------------------
    # Metadata footer
    # -------------------------
    def add_tags(self, tags: List[str]):
        self.tags.extend(tags)

    def add_aliases(self, aliases: List[str]):
        self.aliases.extend(aliases)