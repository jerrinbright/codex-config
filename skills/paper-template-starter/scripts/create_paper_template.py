#!/usr/bin/env python3
"""Create a compact LaTeX research paper starter workspace."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PROFILES = {
    "generic": [
        ("abstract", "Abstract"),
        ("intro", "Introduction"),
        ("related", "Related Work"),
        ("method", "Method"),
        ("experiments", "Experiments"),
        ("discussion", "Discussion"),
        ("conclusion", "Conclusion"),
    ],
    "ml": [
        ("abstract", "Abstract"),
        ("intro", "Introduction"),
        ("related", "Related Work"),
        ("problem", "Problem Setup"),
        ("method", "Method"),
        ("training", "Optimization and Training Details"),
        ("experiments", "Experiments"),
        ("ablations", "Ablations"),
        ("limitations", "Limitations"),
        ("conclusion", "Conclusion"),
    ],
    "vision": [
        ("abstract", "Abstract"),
        ("intro", "Introduction"),
        ("related", "Related Work"),
        ("problem", "Problem Setup"),
        ("method", "Method"),
        ("experiments", "Experiments"),
        ("ablations", "Ablations"),
        ("limitations", "Limitations"),
        ("conclusion", "Conclusion"),
    ],
    "systems": [
        ("abstract", "Abstract"),
        ("intro", "Introduction"),
        ("background", "Background and Motivation"),
        ("design", "System Design"),
        ("implementation", "Implementation"),
        ("evaluation", "Evaluation"),
        ("discussion", "Discussion"),
        ("conclusion", "Conclusion"),
    ],
}


SECTION_PROMPTS = {
    "abstract": [
        "TODO: State the problem, core idea, main evidence, and takeaway in 150-200 words.",
        "TODO: Avoid claims that are not yet supported by experiments.",
    ],
    "intro": [
        "TODO: Motivate the research gap with a concrete failure mode or workflow pain.",
        "TODO: End with 3-4 crisp contributions.",
    ],
    "related": [
        "TODO: Group prior work by technical idea, not by paper list.",
        "TODO: Make the contrast to this work explicit at the end of each paragraph.",
    ],
    "problem": [
        "TODO: Define inputs, outputs, assumptions, and notation only as needed.",
        "TODO: Keep formalism lightweight until the method requires it.",
    ],
    "method": [
        "TODO: Explain the representation, pipeline, and optimization story.",
        "TODO: Prefer one overview figure plus focused subsections.",
    ],
    "training": [
        "TODO: Record losses, schedules, sampling choices, and implementation details.",
        "TODO: Move exhaustive hyperparameters to the supplement if needed.",
    ],
    "experiments": [
        "TODO: Describe datasets, baselines, metrics, and the evaluation protocol.",
        "TODO: Use tables/figures for evidence and prose for interpretation.",
    ],
    "ablations": [
        "TODO: Validate which components matter and why.",
        "TODO: Use XX placeholders until measured results are available.",
    ],
    "limitations": [
        "TODO: State known limitations honestly and connect them to future work.",
    ],
    "discussion": [
        "TODO: Explain what the results imply, where the method works, and where it may fail.",
    ],
    "conclusion": [
        "TODO: Restate the contribution and the strongest evidence in one short paragraph.",
    ],
    "background": [
        "TODO: Give only the background needed to understand the design choices.",
    ],
    "design": [
        "TODO: Present the architecture, invariants, and main design tradeoffs.",
    ],
    "implementation": [
        "TODO: Capture engineering details needed for reproducibility.",
    ],
    "evaluation": [
        "TODO: Define workloads, baselines, metrics, and measurement setup.",
    ],
}


def tex_escape(text: str) -> str:
    return re.sub(r"([\\{}$&#_%])", r"\\\1", text)


def slug_from_title(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "paper"


def write_file(path: Path, content: str, *, force: bool, skip_existing: bool) -> bool:
    if path.exists() and not force:
        if skip_existing:
            return False
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def section_tex(key: str, title: str, paper_title: str) -> str:
    if key == "abstract":
        prompts = "\n".join(f"% {line}" for line in SECTION_PROMPTS[key])
        return f"""{prompts}
\\begin{{abstract}}
TODO: Draft a concise abstract for \\emph{{{tex_escape(paper_title)}}}. State the problem, the key idea, and the main expected evidence.
\\end{{abstract}}
"""

    prompts = "\n".join(f"% {line}" for line in SECTION_PROMPTS.get(key, ["TODO: Fill this section."]))
    return f"""\\section{{{tex_escape(title)}}}
{prompts}

TODO: Write this section.
"""


def main_tex(title: str, venue: str, sections: list[tuple[str, str]]) -> str:
    body = []
    for key, _title in sections:
        body.append(f"\\input{{sections/{key}}}")
    venue_line = f"\\\\ {tex_escape(venue)}" if venue else ""
    return f"""\\documentclass[10pt]{{article}}

\\usepackage[margin=1in]{{geometry}}
\\usepackage{{booktabs}}
\\usepackage{{graphicx}}
\\usepackage{{amsmath,amssymb}}
\\usepackage{{hyperref}}
\\usepackage{{xcolor}}

\\graphicspath{{{{figures/}}}}

\\title{{{tex_escape(title)}}}
\\author{{Author Name{venue_line}}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle

% TODO: Replace this starter structure with the target venue style when ready.
% TODO: Keep claims marked XX until backed by experiments.

{chr(10).join(body)}

% Uncomment after adding real citations to refs.bib.
% \\bibliographystyle{{plain}}
% \\bibliography{{refs}}

\\end{{document}}
"""


def supplementary_tex(title: str) -> str:
    return f"""\\documentclass[10pt]{{article}}

\\usepackage[margin=1in]{{geometry}}
\\usepackage{{booktabs}}
\\usepackage{{graphicx}}
\\usepackage{{amsmath,amssymb}}
\\usepackage{{hyperref}}

\\graphicspath{{{{figures/}}}}

\\title{{Supplementary Material for {tex_escape(title)}}}
\\author{{Author Name}}
\\date{{}}

\\begin{{document}}
\\maketitle

\\section{{Additional Implementation Details}}
TODO: Add training details, hyperparameters, architecture diagrams, or derivations.

\\section{{Additional Experiments}}
TODO: Add extended quantitative results, ablations, and qualitative examples.

\\section{{Reproducibility Checklist}}
\\begin{{itemize}}
  \\item TODO: Datasets and preprocessing.
  \\item TODO: Baselines and evaluation protocol.
  \\item TODO: Compute, runtime, and key hyperparameters.
\\end{{itemize}}

% Uncomment after adding real citations to refs.bib.
% \\bibliographystyle{{plain}}
% \\bibliography{{refs}}

\\end{{document}}
"""


def refs_bib() -> str:
    return """@comment{Add BibTeX entries here.}

@comment{Example:
  @inproceedings{example2026paper,
    title={Example Paper Title},
    author={Doe, Jane and Smith, John},
    booktitle={Conference Name},
    year={2026}
  }
}
"""


def paper_plan(title: str, profile: str, venue: str, sections: list[tuple[str, str]]) -> str:
    section_list = "\n".join(f"- [ ] Draft {name}" for _key, name in sections if name != "Abstract")
    venue_line = f"\nVenue: {venue}" if venue else ""
    return f"""# {title}

Profile: {profile}{venue_line}

## Drafting Checklist

- [ ] Finalize one-sentence thesis.
- [ ] List 3-4 contributions.
- [ ] Identify primary figure.
- [ ] Define datasets, baselines, and metrics.
- [ ] Mark unsupported claims as XX.
{section_list}
- [ ] Compile `main.tex`.
- [ ] Compile `supplementary.tex` if used.

## Figure Plan

- [ ] Figure 1: Problem and method overview.
- [ ] Figure 2: Core technical mechanism.
- [ ] Figure 3: Main qualitative result or workflow.

## Table Plan

- [ ] Table 1: Main quantitative comparison.
- [ ] Table 2: Ablation or component analysis.
- [ ] Table 3: Runtime, robustness, or supplementary result.
"""


def create_template(args: argparse.Namespace) -> list[Path]:
    target = Path(args.target).expanduser().resolve()
    profile = args.profile.lower()
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile '{args.profile}'. Choose one of: {', '.join(sorted(PROFILES))}")

    title = args.title.strip() if args.title else "Working Paper Title"
    venue = args.venue.strip() if args.venue else ""
    sections = PROFILES[profile]

    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    files = {
        target / "main.tex": main_tex(title, venue, sections),
        target / "supplementary.tex": supplementary_tex(title),
        target / "refs.bib": refs_bib(),
        target / "notes" / "paper_plan.md": paper_plan(title, profile, venue, sections),
        target / "figures" / ".gitkeep": "",
        target / "tables" / ".gitkeep": "",
    }
    for key, section_title in sections:
        files[target / "sections" / f"{key}.tex"] = section_tex(key, section_title, title)

    for path, content in files.items():
        if write_file(path, content, force=args.force, skip_existing=args.skip_existing):
            written.append(path)

    return written


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="Folder where the paper template should be created")
    parser.add_argument("--title", default="Working Paper Title", help="Paper title")
    parser.add_argument("--venue", default="", help="Optional target venue, e.g. WACV 2027")
    parser.add_argument("--profile", default="generic", choices=sorted(PROFILES), help="Template profile")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--skip-existing", action="store_true", help="Leave existing files untouched")
    args = parser.parse_args(argv)
    if args.force and args.skip_existing:
        parser.error("--force and --skip-existing cannot be used together")
    return args


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
        written = create_template(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if written:
        print("created:")
        for path in written:
            print(f"  {path}")
    else:
        print("no files created; all target files already existed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
