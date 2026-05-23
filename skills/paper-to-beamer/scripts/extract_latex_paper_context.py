#!/usr/bin/env python3
"""Extract a compact Markdown digest from a LaTeX paper workspace."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


INPUT_RE = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")
TITLE_RE = re.compile(r"\\title(?:\[[^\]]*\])?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", re.S)
ABSTRACT_RE = re.compile(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", re.S)
HEADING_RE = re.compile(r"\\(section|subsection|subsubsection)\*?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", re.S)
FIGURE_RE = re.compile(r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}", re.S)
TABLE_RE = re.compile(r"\\begin\{table\*?\}(.*?)\\end\{table\*?\}", re.S)
CAPTION_RE = re.compile(r"\\caption(?:\[[^\]]*\])?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", re.S)
GRAPHICS_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\s*\{([^}]+)\}")
CITE_RE = re.compile(r"\\cite[a-zA-Z*]*\s*(?:\[[^\]]*\]\s*){0,2}\{([^}]+)\}")
BIB_RE = re.compile(r"\\bibliography\s*\{([^}]+)\}")
MACRO_RE = re.compile(r"^\s*\\(?:newcommand|renewcommand|providecommand|def)\s*\\?([A-Za-z@]+)", re.M)
SIMPLE_NEWCOMMAND_RE = re.compile(
    r"\\(?:newcommand|renewcommand|providecommand)\s*\{?\\([A-Za-z@]+)\}?(?:\[[^\]]+\])?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
    re.S,
)


@dataclass
class SourceFile:
    path: Path
    rel: str
    text: str


def strip_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        cut = None
        for i, char in enumerate(line):
            if char == "%" and (i == 0 or line[i - 1] != "\\"):
                cut = i
                break
        lines.append(line[:cut] if cut is not None else line)
    return "\n".join(lines)


def simple_macro_map(text: str) -> dict[str, str]:
    macros = {}
    for name, value in SIMPLE_NEWCOMMAND_RE.findall(text):
        if len(value) > 120:
            continue
        clean = tex_to_text(value)
        if clean:
            macros[name] = clean
    return macros


def tex_to_text(text: str, macros: dict[str, str] | None = None) -> str:
    if macros:
        for name, value in sorted(macros.items(), key=lambda item: len(item[0]), reverse=True):
            text = re.sub(rf"\\{re.escape(name)}\b", value, text)
    text = re.sub(r"\\[a-zA-Z*]+\s*", " ", text)
    text = re.sub(r"[{}$]", "", text)
    text = re.sub(r"~", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def word_limited(text: str, words: int = 90, macros: dict[str, str] | None = None) -> str:
    clean = tex_to_text(text, macros)
    parts = clean.split()
    if len(parts) <= words:
        return clean
    return " ".join(parts[:words]) + " ..."


def resolve_tex(root: Path, current_dir: Path, raw: str) -> Path:
    candidate = (current_dir / raw).expanduser()
    if candidate.suffix != ".tex":
        candidate = candidate.with_suffix(".tex")
    if not candidate.is_absolute():
        candidate = (root / candidate).resolve()
    return candidate


def collect_sources(root: Path, main: Path) -> list[SourceFile]:
    seen: set[Path] = set()
    ordered: list[SourceFile] = []

    def visit(path: Path) -> None:
        path = path.resolve()
        if path in seen or not path.exists():
            return
        seen.add(path)
        text = strip_comments(path.read_text(encoding="utf-8", errors="ignore"))
        ordered.append(SourceFile(path=path, rel=path.relative_to(root).as_posix(), text=text))
        for match in INPUT_RE.finditer(text):
            visit(resolve_tex(root, path.parent, match.group(1)))

    visit(main)
    return ordered


def extract_title(text: str, macros: dict[str, str]) -> str:
    match = TITLE_RE.search(text)
    return tex_to_text(match.group(1), macros) if match else ""


def extract_abstract(text: str, macros: dict[str, str]) -> str:
    match = ABSTRACT_RE.search(text)
    return word_limited(match.group(1), 170, macros) if match else ""


def extract_sections(source: SourceFile, macros: dict[str, str]) -> list[dict[str, str]]:
    matches = list(HEADING_RE.finditer(source.text))
    sections = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(source.text)
        body = source.text[start:end]
        sections.append(
            {
                "level": match.group(1),
                "title": tex_to_text(match.group(2), macros),
                "file": source.rel,
                "summary": word_limited(body, 95, macros),
            }
        )
    return sections


def extract_float_blocks(pattern: re.Pattern[str], source: SourceFile, macros: dict[str, str]) -> list[dict[str, object]]:
    blocks = []
    for block in pattern.finditer(source.text):
        raw = block.group(1)
        caption = CAPTION_RE.search(raw)
        graphics = [g.strip() for g in GRAPHICS_RE.findall(raw)]
        blocks.append(
            {
                "file": source.rel,
                "caption": word_limited(caption.group(1), 55, macros) if caption else "",
                "graphics": graphics,
            }
        )
    return blocks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper_root", help="Paper directory or path to main.tex")
    parser.add_argument("--main", default="main.tex", help="Main TeX filename when paper_root is a directory")
    parser.add_argument("--out", help="Write Markdown digest to this path")
    args = parser.parse_args()

    given = Path(args.paper_root).expanduser().resolve()
    if given.is_file():
        root = given.parent
        main_tex = given
    else:
        root = given
        main_tex = root / args.main
    if not main_tex.exists():
        raise SystemExit(f"main tex not found: {main_tex}")

    sources = collect_sources(root, main_tex)
    combined = "\n\n".join(src.text for src in sources)
    macro_map = simple_macro_map(combined)
    title = extract_title(combined, macro_map)
    abstract = extract_abstract(combined, macro_map)
    sections = [section for src in sources for section in extract_sections(src, macro_map)]
    figures = [fig for src in sources for fig in extract_float_blocks(FIGURE_RE, src, macro_map)]
    tables = [tab for src in sources for tab in extract_float_blocks(TABLE_RE, src, macro_map)]
    cites = sorted({key.strip() for match in CITE_RE.findall(combined) for key in match.split(",") if key.strip()})
    bibs = sorted({name.strip() for match in BIB_RE.findall(combined) for name in match.split(",") if name.strip()})
    macros = sorted(set(MACRO_RE.findall(combined)))[:80]

    lines: list[str] = []
    lines.append("# Paper Presentation Context")
    lines.append("")
    lines.append(f"- Paper root: `{root}`")
    lines.append(f"- Main TeX: `{main_tex.relative_to(root).as_posix()}`")
    if title:
        lines.append(f"- Title: {title}")
    lines.append(f"- Source files read: {len(sources)}")
    lines.append(f"- Sections found: {len(sections)}")
    lines.append(f"- Figures found: {len(figures)}")
    lines.append(f"- Tables found: {len(tables)}")
    lines.append(f"- Citation keys found: {len(cites)}")
    lines.append("")

    if abstract:
        lines.append("## Abstract")
        lines.append("")
        lines.append(abstract)
        lines.append("")

    lines.append("## Source Reading Order")
    lines.append("")
    for src in sources:
        lines.append(f"- `{src.rel}`")
    lines.append("")

    lines.append("## Section Digest")
    lines.append("")
    for section in sections:
        lines.append(f"### {section['title']}")
        lines.append(f"- Level: `{section['level']}`")
        lines.append(f"- File: `{section['file']}`")
        if section["summary"]:
            lines.append(f"- Digest: {section['summary']}")
        lines.append("")

    lines.append("## Figures")
    lines.append("")
    if figures:
        for index, fig in enumerate(figures, 1):
            lines.append(f"{index}. File: `{fig['file']}`")
            if fig["graphics"]:
                lines.append(f"   - Graphics: {', '.join('`' + g + '`' for g in fig['graphics'])}")
            if fig["caption"]:
                lines.append(f"   - Caption: {fig['caption']}")
    else:
        lines.append("- No figure environments found.")
    lines.append("")

    lines.append("## Tables")
    lines.append("")
    if tables:
        for index, table in enumerate(tables, 1):
            lines.append(f"{index}. File: `{table['file']}`")
            if table["caption"]:
                lines.append(f"   - Caption: {table['caption']}")
    else:
        lines.append("- No table environments found.")
    lines.append("")

    lines.append("## Macros To Consider")
    lines.append("")
    if macros:
        lines.append(", ".join(f"`\\{macro}`" for macro in macros))
    else:
        lines.append("- No custom macros detected.")
    lines.append("")

    lines.append("## Bibliography")
    lines.append("")
    if bibs:
        lines.append("- Bibliography files: " + ", ".join(f"`{name}.bib`" for name in bibs))
    if cites:
        preview = ", ".join(cites[:80])
        suffix = " ..." if len(cites) > 80 else ""
        lines.append(f"- Citation key preview: {preview}{suffix}")
    else:
        lines.append("- No citations detected.")
    lines.append("")

    output = "\n".join(lines)
    if args.out:
        out_path = Path(args.out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
