from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


CODE_ROOT = Path(__file__).resolve().parents[2]
NOTE_DIR = CODE_ROOT / "ieq_paper" / "02_outputs" / "supplementary_experiments" / "notes"
FIGURE_DIR = CODE_ROOT / "ieq_paper" / "02_outputs" / "supplementary_experiments" / "figures"

MARKDOWN_PATH = NOTE_DIR / "ieq_three_vs_five_class_article_brief.md"
PDF_PATH = NOTE_DIR / "ieq_three_vs_five_class_article_brief.pdf"
CONFUSION_MATRIX_PATH = FIGURE_DIR / "ieq_5240_three_vs_five_extra_trees_confusion_matrices.png"


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
        elif line.startswith("- "):
            lines.append("  " + line)
        elif line.startswith("`") and line.endswith("`"):
            lines.append(line.strip("`"))
        elif line.startswith("|") or line.startswith("```"):
            continue
        else:
            lines.append(line)
    return lines


def wrapped_lines(lines: list[str], width: int = 93) -> list[str]:
    result: list[str] = []
    for line in lines:
        if not line:
            result.append("")
            continue
        indent = len(line) - len(line.lstrip(" "))
        result.extend(
            textwrap.wrap(
                line,
                width=width,
                subsequent_indent=" " * indent,
                break_long_words=False,
                break_on_hyphens=False,
            )
            or [""]
        )
    return result


def add_text_pages(pdf: PdfPages, markdown_path: Path) -> None:
    lines = wrapped_lines(markdown_to_plain_lines(markdown_path))
    page_lines = 46
    total_pages = (len(lines) + page_lines - 1) // page_lines
    for page_index, start in enumerate(range(0, len(lines), page_lines), start=1):
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.patch.set_facecolor("white")
        page = lines[start : start + page_lines]
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
            f"{markdown_path.name} | page {page_index}/{total_pages + 1}",
            ha="right",
            va="bottom",
            family="DejaVu Sans",
            fontsize=7,
            color="#6B7280",
        )
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)


def add_confusion_matrix_page(pdf: PdfPages, image_path: Path) -> None:
    image = plt.imread(image_path)
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.03, 0.06, 0.94, 0.88])
    ax.imshow(image)
    ax.axis("off")
    fig.text(
        0.5,
        0.965,
        "Confusion matrices for the 5,240-row IEQ sensitivity comparison",
        ha="center",
        va="top",
        family="DejaVu Sans",
        fontsize=12,
        color="#111827",
    )
    fig.text(
        0.97,
        0.025,
        image_path.name,
        ha="right",
        va="bottom",
        family="DejaVu Sans",
        fontsize=7,
        color="#6B7280",
    )
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(PDF_PATH) as pdf:
        add_text_pages(pdf, MARKDOWN_PATH)
        add_confusion_matrix_page(pdf, CONFUSION_MATRIX_PATH)
    print(f"Wrote {PDF_PATH}")


if __name__ == "__main__":
    main()
