from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEX_PATH = ROOT / "06_Paper" / "IEQ.tex"
REPORT_PATH = ROOT / "06_Paper" / "IEQ_WORD_COUNTS.md"


IDEAL_RANGES = {
    "Abstract": (150, 250),
    "Introduction": (1300, 2000),
    "Introduction / opening argument": (900, 1300),
    "Introduction / Research Questions": (100, 200),
    "Introduction / Contribution": (300, 500),
    "Dataset Description": (1500, 2200),
    "Dataset Description / opening text": (700, 1000),
    "Dataset Description / Data Cleaning and Imputation": (800, 1200),
    "Analysis": (900, 1300),
    "Analysis / Modeling Setup": (500, 800),
    "Analysis / Tuning Workflow": (300, 500),
    "Results": (1200, 1800),
    "Results / Main Tuned Benchmark": (700, 1000),
    "Results / Best Hyperparameters": (150, 300),
    "Results / Fine-Tuning Results": (500, 800),
    "Preliminary Literature Benchmark": (300, 600),
    "Transfer Learning": (600, 1000),
    "Discussion": (1000, 1500),
    "Future Work": (300, 600),
    "Conclusion": (250, 450),
    "Publishable total": (6000, 8000),
}

SECTION_GUIDE = [
    (
        "Abstract",
        "150-250",
        "Short summary of the whole paper.",
        "Problem, Belgian classroom dataset, three-class target, model comparison, best result, and practical decision-support value.",
    ),
    (
        "Introduction",
        "1300-2000",
        "Motivate why the study matters and place it in the literature.",
        "Two main paragraphs under one heading: first practical use and energy-aware IEQ trade-offs; second review gaps and how this paper follows from them. Research questions and contributions can remain directly after it.",
    ),
    (
        "Dataset Description",
        "1500-2200",
        "Make the empirical basis clear and reproducible.",
        "Dataset origin, classroom types, occupants, measured IEQ domains, survey scale, target definition, predictor groups, missingness, imputation, and leakage prevention.",
    ),
    (
        "Analysis",
        "900-1300",
        "Explain exactly how the models were trained and compared.",
        "Model families, preprocessing pipeline, cross-validation design, tuning strategy, metrics, why macro F1 is primary, and how feature importance is evaluated.",
    ),
    (
        "Results",
        "1200-1800",
        "Report the evidence without over-interpreting it.",
        "Main benchmark, confusion matrices, best hyperparameters, feature importance, sensitivity checks, and what the results show about difficulty of individual classroom IEQ prediction.",
    ),
    (
        "Preliminary Literature Benchmark",
        "300-600",
        "Compare results with related work carefully.",
        "Explain why some papers report higher scores and why this task is harder: individual votes, three classes, classroom setting, sensor/context inputs, mixed school types.",
    ),
    (
        "Transfer Learning",
        "600-1000",
        "Show whether the approach generalizes beyond one setting.",
        "Describe school-type transfer, domain shift, primary-only results, possible external dataset, and what this means for model reuse across schools.",
    ),
    (
        "Discussion",
        "1000-1500",
        "Convert results into meaning, limitations, and practical implications.",
        "Energy-aware decision support, why separate thresholds are insufficient, where the model is useful, where it is not reliable enough, limitations, and implications for monitoring design.",
    ),
    (
        "Future Work",
        "300-600",
        "Define what must happen before real-world use.",
        "Prospective classroom deployment, dashboard testing, occupied-building validation, calibration, transfer to other schools/seasons, and autonomous control only as future work.",
    ),
    (
        "Conclusion",
        "250-450",
        "Close the paper with the main claim and evidence.",
        "One compact recap: dataset, best model, main finding, practical value, limitations, and next step toward real operation.",
    ),
]

DRAFT_ONLY_SECTIONS = {"My Questions"}
SKIP_ENVIRONMENTS = {"figure", "table", "tabular", "tikzpicture"}


@dataclass
class Block:
    key: str
    level: int
    title: str
    parent: str | None = None
    text: list[str] = field(default_factory=list)

    @property
    def words(self) -> int:
        return count_words(" ".join(self.text))


def remove_comments(line: str) -> str:
    chars: list[str] = []
    escaped = False
    for char in line:
        if char == "%" and not escaped:
            break
        chars.append(char)
        escaped = char == "\\" and not escaped
        if char != "\\":
            escaped = False
    return "".join(chars)


def strip_balanced_macro(text: str, macro: str) -> str:
    marker = f"\\{macro}"
    while marker in text:
        start = text.find(marker)
        brace_start = text.find("{", start + len(marker))
        if brace_start == -1:
            return text[:start]

        depth = 0
        end = brace_start
        while end < len(text):
            if text[end] == "{":
                depth += 1
            elif text[end] == "}":
                depth -= 1
                if depth == 0:
                    end += 1
                    break
            end += 1
        text = text[:start] + text[end:]
    return text


def extract_heading(line: str) -> tuple[str, str, str] | None:
    match = re.match(r"\\(section|subsection|paragraph)\{([^{}]+)\}(.*)", line.strip())
    if not match:
        return None
    return match.group(1), match.group(2).strip(), match.group(3).strip()


def clean_latex(text: str) -> str:
    text = re.sub(r"\$[^$]*\$", " ", text)
    text = re.sub(r"\\\[[\s\S]*?\\\]", " ", text)
    text = re.sub(r"\\\([\s\S]*?\\\)", " ", text)

    for command in [
        "cite",
        "citep",
        "citet",
        "parencite",
        "textcite",
        "autocite",
        "ref",
        "label",
        "includegraphics",
        "addbibresource",
    ]:
        text = re.sub(rf"\\{command}(?:\[[^\]]*\])*\{{[^{{}}]*\}}", " ", text)

    text = re.sub(r"\\(textbf|textit|emph|texttt|mathbf|mathrm)\{([^{}]*)\}", r"\2", text)
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", " ", text)
    text = text.replace(r"\%", " percent ")
    text = text.replace(r"\&", " and ")
    text = text.replace(r"\_", "_")
    text = text.replace(r"~", " ")
    text = text.replace("--", " ")
    text = re.sub(r"[{}]", " ", text)
    return text


def count_words(text: str) -> int:
    cleaned = clean_latex(text)
    words = re.findall(r"\b(?=[A-Za-z0-9]*[A-Za-z])[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b", cleaned)
    return len(words)


def parse_tex() -> tuple[dict[str, Block], list[str]]:
    lines = TEX_PATH.read_text(encoding="utf-8").splitlines()

    blocks: dict[str, Block] = {}
    order: list[str] = []
    current_section: str | None = None
    current_block: str | None = None
    in_document = False
    in_abstract = False
    skip_env: str | None = None
    skipping_supervisor_note = False
    supervisor_depth = 0

    def ensure_block(key: str, level: int, title: str, parent: str | None = None) -> None:
        if key not in blocks:
            blocks[key] = Block(key=key, level=level, title=title, parent=parent)
            order.append(key)

    for raw_line in lines:
        line = remove_comments(raw_line).strip()
        if not line:
            continue

        if line == r"\begin{document}":
            in_document = True
            continue
        if not in_document:
            continue
        if line == r"\end{document}":
            break
        if line.startswith(r"\printbibliography") or r"\printbibliography" in line:
            break

        begin_env = re.match(r"\\begin\{([^{}]+)\}", line)
        end_env = re.match(r"\\end\{([^{}]+)\}", line)
        if begin_env and begin_env.group(1) in SKIP_ENVIRONMENTS:
            skip_env = begin_env.group(1)
            continue
        if skip_env:
            if end_env and end_env.group(1) == skip_env:
                skip_env = None
            continue

        if line == r"\begin{abstract}":
            in_abstract = True
            ensure_block("Abstract", 0, "Abstract")
            current_block = "Abstract"
            continue
        if line == r"\end{abstract}":
            in_abstract = False
            current_block = None
            continue

        if skipping_supervisor_note:
            supervisor_depth += line.count("{") - line.count("}")
            if supervisor_depth <= 0:
                skipping_supervisor_note = False
            continue
        if line.startswith(r"\supervisornote"):
            supervisor_depth = line.count("{") - line.count("}")
            if supervisor_depth > 0:
                skipping_supervisor_note = True
            continue
        line = strip_balanced_macro(line, "supervisornote")

        heading = extract_heading(line)
        if heading:
            kind, title, rest = heading
            if kind == "section":
                current_section = title
                opening_label = "opening argument" if title == "Introduction" else "opening text"
                current_block = f"{title} / {opening_label}"
                ensure_block(title, 1, title)
                ensure_block(current_block, 2, opening_label, parent=title)
            elif kind == "subsection" and current_section:
                current_block = f"{current_section} / {title}"
                ensure_block(current_block, 2, title, parent=current_section)
            elif kind == "paragraph" and current_block:
                rest = f"{title}. {rest}"

            if rest and current_block:
                blocks[current_block].text.append(rest)
            continue

        if in_abstract:
            blocks["Abstract"].text.append(line)
        elif current_block:
            blocks[current_block].text.append(line)

    return blocks, order


def aggregate_counts(blocks: dict[str, Block]) -> dict[str, int]:
    counts = {key: block.words for key, block in blocks.items()}
    for key, block in blocks.items():
        if block.parent:
            counts[block.parent] = counts.get(block.parent, 0) + block.words
    publishable_total = 0
    for key, block in blocks.items():
        if block.parent is not None:
            continue
        if block.title in DRAFT_ONLY_SECTIONS:
            continue
        publishable_total += counts.get(key, 0)
    counts["Publishable total"] = publishable_total
    return counts


def status_for(count: int, target: tuple[int, int] | None) -> tuple[str, str]:
    if target is None:
        return "-", "-"
    low, high = target
    if count < low:
        return "short", f"+{low - count} to minimum"
    if count > high:
        return "long", f"-{count - high} to maximum"
    return "ok", "within range"


def target_text(target: tuple[int, int] | None) -> str:
    if target is None:
        return "-"
    return f"{target[0]}-{target[1]}"


def make_report() -> str:
    blocks, order = parse_tex()
    counts = aggregate_counts(blocks)

    rows: list[tuple[str, int, str, str, str]] = []
    main_keys = [
        "Abstract",
        "Introduction",
        "Introduction / opening argument",
        "Introduction / Research Questions",
        "Introduction / Contribution",
        "Dataset Description",
        "Dataset Description / opening text",
        "Dataset Description / Data Cleaning and Imputation",
        "Analysis",
        "Analysis / Modeling Setup",
        "Analysis / Tuning Workflow",
        "Results",
        "Results / Main Tuned Benchmark",
        "Results / Best Hyperparameters",
        "Results / Fine-Tuning Results",
        "Preliminary Literature Benchmark",
        "Transfer Learning",
        "Discussion",
        "Future Work",
        "Conclusion",
        "Publishable total",
    ]

    for key in main_keys:
        count = counts.get(key, 0)
        target = IDEAL_RANGES.get(key)
        status, delta = status_for(count, target)
        rows.append((key, count, target_text(target), status, delta))

    draft_rows: list[tuple[str, int]] = []
    for key in order:
        block = blocks[key]
        if block.parent is None and block.title in DRAFT_ONLY_SECTIONS:
            draft_rows.append((block.title, counts.get(key, 0)))

    updated = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# IEQ Manuscript Length Plan",
        "",
        f"Generated from `{TEX_PATH.relative_to(ROOT).as_posix()}` on {updated}.",
        "",
        "Counting rule: prose only. The script excludes references, figures, tables, captions, LaTeX commands, and `\\supervisornote{...}` draft notes.",
        "",
        "Regenerate this file after edits with:",
        "",
        "```powershell",
        "python .\\03_Code\\_project_tools\\update_ieq_word_counts.py",
        "```",
        "",
        "## Recommended Structure",
        "",
        "| Part | Ideal words | Role | What to write in this paper |",
        "|---|---:|---|---|",
    ]
    for part, target, role, content in SECTION_GUIDE:
        lines.append(f"| {part} | {target} | {role} | {content} |")

    lines.extend(
        [
            "",
        "## Current vs Ideal Length",
        "",
        "| Part | Current words | Ideal words | Status | Gap |",
        "|---|---:|---:|---|---:|",
        ]
    )
    for part, count, target, status, delta in rows:
        lines.append(f"| {part} | {count} | {target} | {status} | {delta} |")

    if draft_rows:
        lines.extend(
            [
                "",
                "## Draft-only Sections",
                "",
                "| Section | Current words |",
                "|---|---:|",
            ]
        )
        for title, count in draft_rows:
            lines.append(f"| {title} | {count} |")

    lines.extend(
        [
            "",
            "## Practical Interpretation",
            "",
            "- The manuscript is still short mainly because Discussion, Transfer Learning, and Conclusion are not developed yet.",
            "- The current Introduction is now structurally close to the desired shape, but can still grow slightly if more detailed review synthesis is needed.",
            "- The publishable target is roughly 6,000-8,000 prose words before references.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    REPORT_PATH.write_text(make_report(), encoding="utf-8")
    print(f"Updated {REPORT_PATH.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
