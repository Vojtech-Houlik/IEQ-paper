from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "TWO_PAPER_ROADMAP.md",
    ROOT / "thermal_comfort_paper" / "00_progress" / "progress.md",
    ROOT / "ieq_paper" / "00_progress" / "progress.md",
]


def markdown_to_plain_lines(path: Path) -> list[str]:
    lines: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            text = line[level:].strip()
            prefix = "" if level == 1 else "  " * (level - 1)
            lines.append(f"{prefix}{text.upper() if level == 1 else text}")
            lines.append("")
        elif line.startswith("- ["):
            lines.append("  " + line)
        elif line.startswith("- "):
            lines.append("  " + line)
        elif line.startswith("|"):
            continue
        elif line.startswith("```"):
            continue
        else:
            lines.append(line)
    return lines


def write_pdf(markdown_path: Path, pdf_path: Path) -> None:
    lines = markdown_to_plain_lines(markdown_path)
    wrapped: list[str] = []
    for line in lines:
        if not line:
            wrapped.append("")
            continue
        indent = len(line) - len(line.lstrip(" "))
        wrapped.extend(
            textwrap.wrap(
                line,
                width=95,
                subsequent_indent=" " * indent,
                break_long_words=False,
                break_on_hyphens=False,
            )
            or [""]
        )

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    page_lines = 47
    with PdfPages(pdf_path) as pdf:
        for start in range(0, len(wrapped), page_lines):
            fig = plt.figure(figsize=(8.27, 11.69))
            fig.patch.set_facecolor("white")
            page = wrapped[start : start + page_lines]
            fig.text(
                0.07,
                0.96,
                "\n".join(page),
                ha="left",
                va="top",
                family="DejaVu Sans",
                fontsize=8.8,
                color="#111827",
                linespacing=1.25,
            )
            fig.text(
                0.93,
                0.035,
                f"{markdown_path.name} | page {start // page_lines + 1}",
                ha="right",
                va="bottom",
                family="DejaVu Sans",
                fontsize=7,
                color="#6B7280",
            )
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)


def main() -> None:
    for doc in DOCS:
        write_pdf(doc, doc.with_suffix(".pdf"))
        print(f"Wrote {doc.with_suffix('.pdf')}")


if __name__ == "__main__":
    main()
