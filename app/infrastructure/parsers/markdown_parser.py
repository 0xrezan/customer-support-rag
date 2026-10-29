"""Markdown section parser — heading-aware text splitting."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.utils.text_normalization import clean_extracted_text


@dataclass
class MarkdownSection:
    """A section extracted from a Markdown document."""

    heading: str
    level: int
    text: str
    section_index: int


class MarkdownParser:
    """Split a Markdown document into sections by headings."""

    _HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    def parse(self, content: str) -> list[MarkdownSection]:
        sections: list[MarkdownSection] = []
        matches = list(self._HEADING_RE.finditer(content))

        if not matches:
            # No headings — treat the whole file as one section
            cleaned = clean_extracted_text(content)
            if cleaned:
                sections.append(
                    MarkdownSection(
                        heading="(untitled)",
                        level=1,
                        text=cleaned,
                        section_index=0,
                    )
                )
            return sections

        # Text before the first heading
        preamble = content[: matches[0].start()].strip()
        idx = 0
        if preamble:
            sections.append(
                MarkdownSection(
                    heading="(preamble)",
                    level=0,
                    text=clean_extracted_text(preamble),
                    section_index=idx,
                )
            )
            idx += 1

        for i, match in enumerate(matches):
            level = len(match.group(1))
            heading = match.group(2).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            body = content[start:end].strip()
            cleaned = clean_extracted_text(body)
            sections.append(
                MarkdownSection(
                    heading=heading,
                    level=level,
                    text=cleaned,
                    section_index=idx,
                )
            )
            idx += 1

        return sections
