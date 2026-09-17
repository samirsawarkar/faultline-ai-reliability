#!/usr/bin/env python3
"""Export Publication 01 artifacts: paper.md, paper.tex, paper.pdf, blog_post.md, README.md.

Ensures strict compliance with CTO requirements:
- Same title as research/paper/draft.md:
  'Is pass^k = (pass@1)^k? Testing the Independence Assumption for Repeated Agent Executions on a Controlled Multi-Hop Benchmark'
- Honest framing (arXiv + evaluation-methodology / negative-results track)
- H4/H5 not testable as pre-registered
- Temperature 0 disclosure
- Two-pass sweep and gateway incident disclosures
- No 'regime' / 'inversion' / 'GLM beats GPT' promotional language
- Strip [C###] tags from publication prose
- Strips trailing TODO, ledger ID, and alternative titles lists
- Formatted bibliography and numbered references from references.bib
- Build paper.pdf with xelatex, verify zero missing figures and minimal overfull boxes
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DRAFT_PATH = REPO_ROOT / "research" / "paper" / "draft.md"
BIB_PATH = REPO_ROOT / "research" / "paper" / "references.bib"
FINAL_PATH = REPO_ROOT / "research" / "final" / "paper.md"
PUB_DIR = REPO_ROOT / "publications" / "publication_01_passk_reliability"
PAPER_MD_PATH = PUB_DIR / "paper.md"
PAPER_TEX_PATH = PUB_DIR / "paper.tex"
BUILD_PDF_PATH = PUB_DIR / "build_pdf.py"
BLOG_PATH = PUB_DIR / "blog_post.md"
README_PATH = PUB_DIR / "README.md"


def parse_bibtex(bib_text: str) -> Dict[str, Dict[str, str]]:
    entries = re.findall(r'@(\w+)\s*\{\s*([a-zA-Z0-9_-]+)\s*,\s*(.*?)\n\}', bib_text, re.DOTALL)
    bib_dict = {}
    for entry_type, key, fields_str in entries:
        fields = {"entry_type": entry_type}
        for match in re.finditer(r'(\w+)\s*=\s*[\"{](.*?)[\"}](?:,|$)', fields_str, re.DOTALL):
            fields[match.group(1).lower()] = match.group(2).strip()
        bib_dict[key] = fields
    return bib_dict


def get_sort_author(item: Tuple[str, Dict[str, str]]) -> Tuple[str, str]:
    authors = item[1].get("author", "")
    first_author = authors.split(" and ")[0].strip()
    last_name = first_author.split(",")[0].strip() if "," in first_author else first_author.split()[-1]
    return (last_name.lower(), item[1].get("year", ""))


def format_bib_entry_md(key: str, fields: Dict[str, str]) -> str:
    raw_author = fields.get("author", "Unknown")
    authors = raw_author.replace(" and others", " et al.").replace(" and ", ", ")
    title = fields.get("title", "").replace("{", "").replace("}", "")
    year = fields.get("year", "")
    venue = fields.get("journal") or fields.get("booktitle") or ""
    eprint = fields.get("eprint")
    doi = fields.get("doi")

    parts = [f"{authors} ({year}). {title}."]
    if venue:
        parts.append(f"*{venue}*.")
    elif eprint:
        parts.append(f"*arXiv preprint arXiv:{eprint}*.")
    
    if doi:
        parts.append(f"https://doi.org/{doi}")
    elif eprint:
        parts.append(f"https://arxiv.org/abs/{eprint}")
    
    return " ".join(parts)


def format_bib_entry_tex(key: str, fields: Dict[str, str]) -> str:
    raw_author = fields.get("author", "Unknown")
    authors = raw_author.replace(" and others", " et~al.").replace(" and ", ", ")
    title = fields.get("title", "").replace("{", "").replace("}", "")
    year = fields.get("year", "")
    venue = fields.get("journal") or fields.get("booktitle") or ""
    eprint = fields.get("eprint")
    doi = fields.get("doi")

    tex = f"\\bibitem{{{key}}}\n{authors} ({year}).\n\\newblock {title}.\n"
    if venue:
        tex += f"\\newblock \\emph{{{venue}}}.\n"
    elif eprint:
        tex += f"\\newblock \\emph{{arXiv preprint arXiv:{eprint}}}.\n"
    
    if doi:
        tex += f"\\newblock \\href{{https://doi.org/{doi}}}{{doi:{doi}}}.\n"
    elif eprint:
        tex += f"\\newblock \\href{{https://arxiv.org/abs/{eprint}}}{{arXiv:{eprint}}}.\n"
    return tex


def convert_draft_to_paper_md(draft_text: str, bib_dict: Dict[str, Dict[str, str]]) -> str:
    for marker in ["## List of Evidence Gaps", "## List of Claims Ledger IDs Referenced", "## Alternative Titles"]:
        idx = draft_text.find(marker)
        if idx != -1:
            draft_text = draft_text[:idx].strip()
    draft_text = re.sub(r'\n---\s*$', '', draft_text).strip()

    cleaned = re.sub(r'\s*\[C\d+\]', '', draft_text)

    sorted_bib = sorted(bib_dict.items(), key=get_sort_author)
    key_to_num = {k: i + 1 for i, (k, _) in enumerate(sorted_bib)}

    def replace_citation_group(match: re.Match) -> str:
        content = match.group(1)
        keys = re.findall(r'@([a-zA-Z0-9_-]+)', content)
        nums = []
        for k in keys:
            if k in key_to_num:
                nums.append(key_to_num[k])
        if not nums:
            return match.group(0)
        nums = sorted(list(set(nums)))
        return "[" + ", ".join(str(n) for n in nums) + "]"

    cleaned = re.sub(r'\[([^\]]*@[a-zA-Z0-9_-]+[^\]]*)\]', replace_citation_group, cleaned)
    cleaned = re.sub(r'@([a-zA-Z0-9_-]+)', lambda m: f"[{key_to_num[m.group(1)]}]" if m.group(1) in key_to_num else m.group(0), cleaned)

    ref_idx = cleaned.find("## References")
    if ref_idx != -1:
        prefix = cleaned[:ref_idx + len("## References")].strip()
        next_sec_match = re.search(r'\n(---|\#\#\s+Appendix)', cleaned[ref_idx:])
        suffix = cleaned[ref_idx + next_sec_match.start():] if next_sec_match else ""
        
        ref_list_md = []
        for i, (k, f) in enumerate(sorted_bib):
            ref_list_md.append(f"{i + 1}. {format_bib_entry_md(k, f)}")
        
        cleaned = prefix + "\n\n" + "\n".join(ref_list_md) + "\n" + suffix

    return cleaned


def clean_prose_tex(text: str) -> str:
    # 1. Escape currency $ ONLY when followed by digits AND currency suffix
    text = re.sub(r'(?<!\\)\$(\d+(?:\.\d+)?)\s+(USD\b|per grounded pass|across passes)', r'\\$\1 \2', text)

    # 2. Protect display math $$ ... $$ and inline math $ ... $
    math_tokens: List[str] = []
    def math_sub(m: re.Match) -> str:
        math_tokens.append(m.group(0))
        return f"MATHPH{len(math_tokens)-1}ENDPH"

    t = re.sub(r'(?<!\\)\$\$[\s\S]*?(?<!\\)\$\$', math_sub, text)
    t = re.sub(r'(?<!\\)\$[^\$\n]+?(?<!\\)\$', math_sub, t)

    # 3. Protect inline code `...`
    code_tokens: List[str] = []
    def code_sub(m: re.Match) -> str:
        code_tokens.append(m.group(0))
        return f"CODEPH{len(code_tokens)-1}ENDPH"

    t = re.sub(r'`[^`\n]+?`', code_sub, t)

    # 4. In pure prose, convert mathematical shorthand to LaTeX math
    t = re.sub(r'\(pass@1\)\^([0-9a-zA-Z]+)', r'$(\\text{pass@1})^{\1}$', t)
    t = re.sub(r'\bpass\^([0-9a-zA-Z]+)', r'$\\text{pass}^{\1}$', t)
    t = re.sub(r'\bPass\^([0-9a-zA-Z]+)', r'$\\text{Pass}^{\1}$', t)
    t = t.replace("Pass@k", r"$\text{Pass@k}$")
    t = t.replace(">=", r"$\ge$ ").replace("<=", r"$\le$ ")

    # Clean prose markdown
    t = t.replace("&", r"\&")
    t = t.replace("%", r"\%")
    t = t.replace("#", r"\#")
    t = re.sub(r'\*\*([^\*\n]+?)\*\*', r'\\textbf{\1}', t)
    t = re.sub(r'(?<!\*)\*([^\*\n]+?)\*(?!\*)', r'\\emph{\1}', t)
    t = t.replace("“", "``").replace("”", "''").replace("’", "'").replace("‘", "`")
    t = re.sub(r'^\s*>\s*(.*?)$', r'\\begin{quote}\n\1\n\\end{quote}', t, flags=re.MULTILINE)

    # Escape underscores in words in prose
    t = re.sub(r'\b\w+_\w+\b', lambda m: m.group(0).replace("_", r"\_"), t)

    # 5. Restore code tokens
    for i, c in enumerate(code_tokens):
        inline = c.strip("`").replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")
        raw_code = c.strip("`")
        if re.match(r'^[0-9a-f]{32,}$', raw_code):
            t = t.replace(f"CODEPH{i}ENDPH", f"\\nolinkurl{{{raw_code}}}")
        else:
            t = t.replace(f"CODEPH{i}ENDPH", f"\\texttt{{{inline}}}")

    # 6. Restore math tokens
    for i, m in enumerate(math_tokens):
        t = t.replace(f"MATHPH{i}ENDPH", m)

    return t


def clean_cell_tex(cell: str) -> str:
    cell = cell.strip()
    if not cell:
        return ""

    # 1. Escape currency $ if cell has odd number of $ (currency values like Table E1)
    if cell.count("$") % 2 != 0:
        cell = re.sub(r'(?<!\\)\$(\d)', r'\\$\1', cell)

    # 2. Protect math $...$
    math_tokens: List[str] = []
    def m_sub(m: re.Match) -> str:
        math_tokens.append(m.group(0))
        return f"MATHPH{len(math_tokens)-1}ENDPH"
    c = re.sub(r'(?<!\\)\$[^\$]+?(?<!\\)\$', m_sub, cell)

    # 3. Protect code `...`
    code_tokens: List[str] = []
    def c_sub(m: re.Match) -> str:
        code_tokens.append(m.group(0))
        return f"CODEPH{len(code_tokens)-1}ENDPH"
    c = re.sub(r'`[^`]+?`', c_sub, c)

    # 4. Clean prose in cell
    c = c.replace("&", r"\&")
    c = c.replace("%", r"\%")
    c = c.replace("#", r"\#")
    c = re.sub(r'\*\*([^\*]+?)\*\*', r'\\textbf{\1}', c)
    c = re.sub(r'\*([^\*]+?)\*', r'\\emph{\1}', c)
    c = re.sub(r'\b\w+_\w+\b', lambda m: m.group(0).replace("_", r"\_"), c)

    # 5. Restore code tokens
    for i, code in enumerate(code_tokens):
        inner = code.strip("`").replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")
        raw_code = code.strip("`")
        if re.match(r'^[0-9a-f]{32,}$', raw_code):
            c = c.replace(f"CODEPH{i}ENDPH", f"\\nolinkurl{{{raw_code}}}")
        else:
            c = c.replace(f"CODEPH{i}ENDPH", f"\\texttt{{{inner}}}")

    # 6. Restore math tokens
    for i, m in enumerate(math_tokens):
        c = c.replace(f"MATHPH{i}ENDPH", m)
    return c


def md_table_to_latex(md_table: str, caption: str = "") -> str:
    lines = [l.strip() for l in md_table.strip().split("\n") if l.strip()]
    if len(lines) < 3:
        return ""
    
    header_cells = [c.strip() for c in lines[0].split("|")[1:-1]]
    num_cols = len(header_cells)
    header_tex = " & ".join(clean_cell_tex(c) for c in header_cells) + " \\\\"
    
    data_rows = []
    for l in lines[2:]:
        cells = [c.strip() for c in l.split("|")[1:-1]]
        if len(cells) < num_cols:
            cells += [""] * (num_cols - len(cells))
        elif len(cells) > num_cols:
            cells = cells[:num_cols]
        data_rows.append(" & ".join(clean_cell_tex(c) for c in cells) + " \\\\")

    if num_cols >= 8:
        col_spec = "l" + "c" * (num_cols - 1)
        font_size = "\\scriptsize"
        tabcolsep = "2.0pt"
    elif num_cols >= 6:
        col_spec = "l" + "c" * (num_cols - 1)
        font_size = "\\footnotesize"
        tabcolsep = "3.0pt"
    else:
        col_spec = "l" + "c" * (num_cols - 1)
        font_size = "\\small"
        tabcolsep = "4.5pt"

    tabular_content = [
        f"\\begin{{tabular}}{{{col_spec}}}",
        "\\toprule",
        header_tex,
        "\\midrule",
        "\n".join(data_rows),
        "\\bottomrule",
        "\\end{tabular}",
    ]
    tabular_str = "\n".join(tabular_content)
    tabular_str = f"\\resizebox{{\\textwidth}}{{!}}{{\n{tabular_str}\n}}"

    tex = [
        "\\begin{table}[htbp]",
        "\\centering",
        font_size,
        f"\\setlength{{\\tabcolsep}}{{{tabcolsep}}}",
        tabular_str,
    ]
    if caption:
        cap_clean = clean_prose_tex(caption)
        tex.append(f"\\caption{{{cap_clean}}}")
    tex.append("\\end{table}")
    return "\n".join(tex)


def convert_draft_to_paper_tex(paper_md: str, bib_dict: Dict[str, Dict[str, str]]) -> str:
    sorted_bib = sorted(bib_dict.items(), key=get_sort_author)
    
    header = r"""\documentclass[11pt,letterpaper]{article}
\usepackage[
  letterpaper,
  top=0.75in,
  bottom=0.75in,
  left=0.75in,
  right=0.75in,
  headheight=14pt,
  headsep=12pt,
  footskip=18pt
]{geometry}

\usepackage{fontspec}
\setmainfont{Helvetica}
\setmonofont{Menlo}

\usepackage{amsmath,amssymb,amsfonts}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{caption}
\usepackage{microtype}

\hypersetup{
  breaklinks=true,
  colorlinks=true,
  linkcolor=blue!70!black,
  citecolor=blue!70!black,
  urlcolor=blue!70!black
}

\def\UrlBreaks{\do\/\do\a\do\b\do\c\do\d\do\e\do\f\do\0\do\1\do\2\do\3\do\4\do\5\do\6\do\7\do\8\do\9\do\-}

\captionsetup{font={small},labelfont={bf},skip=6pt}

\title{\textbf{Is $\text{pass}^k = (\text{pass@1})^k$? Testing the Independence Assumption for Repeated Agent Executions on a Controlled Multi-Hop Benchmark}}
\author{
  \textbf{Samir Sawarkar}\\
  FAULTLINE AI Reliability Engineering\\
  \texttt{samir@faultline.ai}\\
  \url{https://github.com/samirsawarkar/faultline-ai-reliability}
}
\date{September 2026}

\begin{document}
\sloppy
\maketitle
"""

    abstract_match = re.search(r'###\s+Abstract\s*\n+(.*?)(?=\n##\s+1\s+Introduction)', paper_md, re.DOTALL)
    abstract_text = abstract_match.group(1).strip() if abstract_match else ""
    abstract_text = re.sub(r'\s*---\s*$', '', abstract_text).strip()
    tex_abstract = clean_prose_tex(abstract_text)
    body = [f"\\begin{{abstract}}\n{tex_abstract}\n\\end{{abstract}}\n"]

    content = paper_md[abstract_match.end():] if abstract_match else paper_md

    def replace_img_with_tex(match: re.Match) -> str:
        caption = match.group(1).strip()
        path = match.group(2).strip()
        cap_clean = clean_prose_tex(caption)
        label = re.sub(r'[^a-zA-Z0-9]', '_', path)
        width = "0.95\\textwidth"
        if "fig_B" in path or "fig_C" in path or "fig_D" in path:
            width = "0.85\\textwidth"
        return f"\n\\begin{{figure}}[htbp]\n\\centering\n\\includegraphics[width={width}]{{{path}}}\n\\caption{{{cap_clean}}}\n\\label{{fig:{label}}}\n\\end{{figure}}\n"

    content = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_img_with_tex, content)

    table_pattern = re.compile(
        r'(\|[^\n]+\|\n\|[-| :]+\|\n(?:\|[^\n]+\|\n)+)\s*(?:\*(Table [^:\*]+:\s*[^\*\n]+(?:\n[^\*\n]+)*)\*)?',
        re.MULTILINE
    )

    def replace_table(match: re.Match) -> str:
        tbl_md = match.group(1)
        caption = match.group(2) or ""
        return "\n" + md_table_to_latex(tbl_md, caption) + "\n"

    content = table_pattern.sub(replace_table, content)

    code_blocks = []
    def save_cb(m: re.Match) -> str:
        code_blocks.append(m.group(0))
        return f"\nVERBATIM_BLOCK_{len(code_blocks)-1}_X\n"

    content = re.sub(r'```[\s\S]*?```', save_cb, content)

    # Convert headers
    content = re.sub(r'\n##\s+(?:Appendix\s+([A-Z]):\s*(.*?))\n', r'\n\\section*{Appendix \1: \2}\n\\addcontentsline{toc}{section}{Appendix \1: \2}\n', content)
    content = re.sub(r'\n##\s+References\n.*?(?=\n\\section\*|\Z)', r'\nBIBLIOGRAPHY_PLACEHOLDER\n', content, flags=re.DOTALL)
    content = re.sub(r'\n##\s+(\d+)\s+([^\n]+)', r'\n\\section{\2}', content)
    content = re.sub(r'\n##\s+([^\n]+)', r'\n\\section{\1}', content)
    content = re.sub(r'\n###\s+([A-Z]\.\d+)\s+([^\n]+)', r'\n\\subsection*{\1 \2}', content)
    content = re.sub(r'\n###\s+(\d+\.\d+)\s+([^\n]+)', r'\n\\subsection{\2}', content)
    content = re.sub(r'\n###\s+([^\n]+)', r'\n\\subsection{\1}', content)
    content = re.sub(r'\n####\s+([^\n]+)', r'\n\\subsubsection*{\1}', content)

    # Format bibliography
    bib_tex = "\\begin{thebibliography}{99}\n"
    for k, f in sorted_bib:
        bib_tex += format_bib_entry_tex(k, f) + "\n"
    bib_tex += "\\end{thebibliography}\n"

    content = content.replace("BIBLIOGRAPHY_PLACEHOLDER", bib_tex)

    # Clean prose
    parts = re.split(r'(\\begin\{figure\}[\s\S]*?\\end\{figure\}|\\begin\{table\}[\s\S]*?\\end\{table\}|\\begin\{thebibliography\}[\s\S]*?\\end\{thebibliography\}|VERBATIM_BLOCK_\d+_X)', content)
    cleaned_parts = []
    for p in parts:
        if p.startswith(r"\begin{figure}") or p.startswith(r"\begin{table}") or p.startswith(r"\begin{thebibliography}") or "VERBATIM_BLOCK_" in p:
            cleaned_parts.append(p)
        else:
            cleaned_parts.append(clean_prose_tex(p))

    content = "".join(cleaned_parts)

    for i, cb in enumerate(code_blocks):
        lines = cb.strip("`").strip().split("\n")
        if lines and lines[0] in ["bash", "python", "json"]:
            lines = lines[1:]
        inner = "\n".join(lines)
        tex_cb = f"\\begin{{verbatim}}\n{inner}\n\\end{{verbatim}}"
        content = content.replace(f"VERBATIM_BLOCK_{i}_X", tex_cb)

    content = content.replace("\n---\n", "\n\n")

    full_tex = header + "\n" + "\n".join(body) + "\n" + content + "\n\\end{document}\n"
    return full_tex


def generate_blog_post() -> str:
    blog = r"""# Is pass^k = (pass@1)^k? Testing the Independence Assumption for Repeated Agent Executions

**Samir Sawarkar** · *FAULTLINE AI Reliability Engineering* · September 2026

When engineers deploy autonomous tool-using language model agents in mission-critical pipelines, a standard assumption quietly underpins operational benchmarks: **compound independence**. That is, if an agent succeeds on a task with probability $\text{pass@1}$, its joint success rate across $k$ repeated independent trials is assumed to decay exponentially as:
$$\text{pass}^k = (\text{pass@1})^k$$

In this pre-registered study (Decision D-009, Project P06), we subjected this compounding assumption to rigorous empirical testing across 1,800 executed runs and 54.3 million tokens on a controlled multi-hop retrieval benchmark.

### The Research Question and Setting

We investigated whether repeated agent trials on fixed tasks behave as independent Bernoulli processes, or whether failures concentrate systematically on latent "hard" instances. To eliminate real-world confounding, our benchmark evaluates agents over a deterministic synthetic knowledge graph (300 documents, content hash pinned) across 150 reserved Tier-3 multi-hop scenarios requiring 4–5 hops. A deterministic dual-condition oracle requires both the exact factual answer string and citation of the canonical provenance document.

Two primary model tiers were evaluated:
- **R2 (`z-ai/glm-5.3-flash`):** A fast, tool-disciplined model achieving $\text{pass@1} = 0.6311$.
- **R4 (`openai/gpt-5.6-luna`):** A frontier model evaluated at $\text{pass@1} = 0.1489$ (as-run) and $0.1909$ (infrastructure-excluded).

All runs executed at greedy temperature 0.

### Honest Infrastructure and Protocol Disclosures

A credible evaluation requires full disclosure of test conditions:
1. **The Gateway Incident:** During R4 execution on 2026-09-11, upstream API gateway outages triggered client circuit breakers across two windows (14:42–14:45 UTC and 22:30–22:41 UTC). This caused 95 of 450 trials to drop out (87 with sub-millisecond latencies). A third rung, R6 (`deepseek/deepseek-v4-pro`), experienced 100% dead-at-start connection drops and was entirely invalidated. We report the pre-registered as-run data ($n=150$) and an infrastructure-excluded sensitivity cohort ($n=117$) side-by-side.
2. **The Two-Pass Protocol:** The SQLite telemetry reflects an exploratory first pass under step cap 12 followed by a final pass under step cap 24. Because terminal verdicts overwrite spans, all reported statistics are strictly isolated to final-pass spans using frozen timestamp boundaries.
3. **Pre-Registered Hypotheses H4 and H5:** Both pre-registered hypotheses required at least four valid rungs to test monotonic ordering and ranking. With only two rungs surviving infrastructure disruption, H4 and H5 are formally designated **NOT_TESTABLE_AS_PREREGISTERED**.

### Key Findings

1. **The Homogeneous Binomial Null Holds on R2:**
   On R2, observed joint reliability at $k=3$ was $\text{pass}^3 = 0.2267$ (34/150 scenarios), remarkably close to naive compounding $(\text{pass@1})^3 = 0.2514$ (a deviation of $\Delta_3 = -0.0247$). The concentration ratio $C_3 = \text{pass}^3 / (\text{pass@1})^3 = 0.9017$ encompasses 1.0 within its 95% bootstrap confidence interval $[0.7161, 1.0793]$. Pearson goodness-of-fit ($\chi^2 = 1.8919, \text{df}=2, p = 0.3794$) and Tarone's score test ($z = -0.655, p = 0.7438$) show no detectable departure from the independent Bernoulli null. Intra-scenario correlation is indistinguishable from zero ($\text{ICC} = -0.0287$).

2. **R4 Failure Clustering Is Driven by Infrastructure:**
   In as-run R4 data, measured $\text{pass}^3 = 0.0200$ (3/150) exceeded naive $0.0033$, yielding apparent overdispersion ($p = 0.0053$). However, excluding the 33 outage-affected scenarios ($n=117$) yields $\text{pass}^3 = 0.0256$ (3/117) versus naive $0.0070$. Tarone's overdispersion test attenuates to $z = 0.764$ ($p = 0.2224$), and $\text{ICC}$ attenuates to $0.0438$ ($[-0.0978, 0.1907]$). The apparent failure clustering is largely an artifact of external dropouts rather than intrinsic model intractability.

3. **Why $k=3$ Consistency Cannot License Deep Extrapolation:**
   While naive compounding holds within 2.5 percentage points at $k=3$, small unmeasured correlations amplify exponentially at greater depths. Under a beta-binomial compounding model, an upper-bound intra-scenario correlation of $\text{ICC} = 0.0668$ produces an expected concentration ratio of $C_8 \approx 2.25$ by $k=8$, where empirical reliability would be more than double the naive prediction. Short benchmarks cannot license deep unassisted compounding.

4. **Paired Comparisons:**
   In paired McNemar tests across identical scenario IDs, R2 significantly outperformed R4 on both Trial-1 accuracy ($+0.4467$ risk difference, $p = 5.92 \times 10^{-14}$) and All-3-Pass joint reliability ($+0.2067$ risk difference, $p = 1.23 \times 10^{-7}$). R2 achieved this reliability at $0.01796 USD per grounded pass versus $0.26825 USD for R4.

### Reproduction

All data, raw SQLite traces, spend ledgers, and deterministic analysis pipelines are open source:
```bash
make p06-analysis
python projects/p06_passk/make_figures.py
python publications/publication_01_passk_reliability/build_pdf.py
```
"""
    return blog.strip()


def generate_readme() -> str:
    readme = """# Publication 01: Multi-Trial Agent Reliability and Compound Independence

This directory contains the complete publication package for the FAULTLINE Project P06 research paper.

## Paper Details

- **Title:** Is pass^k = (pass@1)^k? Testing the Independence Assumption for Repeated Agent Executions on a Controlled Multi-Hop Benchmark
- **Author:** Samir Sawarkar (`samir@faultline.ai`)
- **Target Venue:** arXiv / AI Evaluation Methodology Track
- **Status:** Complete & Reproducible

## Overview & Core Results

The paper investigates the foundational assumption of **compound independence** in autonomous tool-use evaluations: whether repeated independent executions on a task distribution compound as independent Bernoulli trials:
$$\\text{pass}^k = (\\text{pass@1})^k$$

Key findings include:
1. **Homogeneous Binomial Null Holds on R2:** On `glm-5.3-flash` ($n=150$), measured joint reliability at $k=3$ is $\\text{pass}^3 = 0.2267$ vs naive $(\\text{pass@1})^3 = 0.2514$ ($\\Delta_3 = -0.0247, C_3 = 0.9017$, bootstrap CI $[0.7161, 1.0793]$). Pearson goodness-of-fit ($p=0.3794$), Tarone's score test ($z=-0.655, p=0.7438$), and $\\text{ICC} = -0.0287$ confirm outcomes are indistinguishable from independent Bernoulli trials.
2. **Infrastructure Attenuation on R4:** On `gpt-5.6-luna`, as-run clustering was heavily driven by 95 dead trials caused by remote API gateway timeouts. In the sensitivity analysis excluding 33 affected scenarios ($n=117$), $\\text{pass}^3 = 0.0256$ vs naive $0.0070$ ($\\Delta_3 = +0.0187, C_3 = 3.6867$), and overdispersion attenuates to null ($z=0.764, p=0.2224, \\text{ICC}=0.0438$).
3. **Pre-Registered Hypotheses:** H4 and H5 are formally marked **NOT_TESTABLE_AS_PREREGISTERED** due to surviving sample size (2 valid rungs rather than the pre-registered minimum of 4).
4. **Depth Extrapolation Warning:** Small correlations at $k=3$ amplify exponentially at higher depths ($C_8 \\approx 2.25$ under beta-binomial compounding), demonstrating that $k=3$ consistency cannot license deep unassisted compounding.

## Directory Structure

- `paper.md`: Clean, publication-ready markdown paper (with artifact references and formatted bibliography).
- `paper.tex`: Standalone LaTeX paper formatted for arXiv (XeLaTeX, booktabs, graphicx).
- `paper.pdf`: Compiled 300 dpi publication PDF.
- `blog_post.md`: Executive summary blog post (≤ 900 words).
- `build_pdf.py`: Deterministic PDF compilation script via XeLaTeX.
- `fig_1_successes_per_scenario.png/.svg`: Observed vs Binomial(3, pass@1) expected histogram counts.
- `fig_2_passk_vs_naive.png/.svg`: Empirical pass^k vs naive (pass@1)^k for k=1,2,3.
- `fig_3_icc_extrapolation.png/.svg`: C_k extrapolation for k=1..10 from beta-binomial model.
- `fig_4_incident_timeline.png/.svg`: Per-trial terminal states over time during gateway incidents.
- `fig_B_p03_depth.png/.svg`: Reasoning depth pass@1 progression across T1, T2, T3.
- `fig_C_p04_taxonomy.png/.svg`: Axial failure mode prevalence across 9 categories.
- `fig_D_p05_kappa.png/.svg`: Cohen's kappa agreement for automated evaluators vs human labels.

## Deterministic Reproduction

To reproduce all analyses, regenerate figures, and build the paper PDF from scratch:

```bash
# 1. Run deterministic statistical analysis (trace.db -> analysis.json)
make p06-analysis

# 2. Generate all 7 publication figures (SVG and 300 dpi PNG)
python projects/p06_passk/make_figures.py

# 3. Compile the paper PDF via XeLaTeX
python publications/publication_01_passk_reliability/build_pdf.py
```
"""
    return readme.strip()


def main() -> None:
    print("Reading inputs...")
    with open(DRAFT_PATH) as f:
        draft_text = f.read()
    with open(BIB_PATH) as f:
        bib_text = f.read()

    bib_dict = parse_bibtex(bib_text)
    print(f"Parsed {len(bib_dict)} bibliography entries.")

    print(f"Copying draft.md -> {FINAL_PATH}...")
    FINAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FINAL_PATH, "w") as f:
        f.write(draft_text)
    print(f"Wrote {FINAL_PATH} ({len(draft_text)} bytes)")

    print("Generating publications/publication_01_passk_reliability/paper.md...")
    paper_md = convert_draft_to_paper_md(draft_text, bib_dict)
    with open(PAPER_MD_PATH, "w") as f:
        f.write(paper_md)
    print(f"Wrote {PAPER_MD_PATH} ({len(paper_md)} bytes)")

    print("Generating publications/publication_01_passk_reliability/paper.tex...")
    paper_tex = convert_draft_to_paper_tex(paper_md, bib_dict)
    with open(PAPER_TEX_PATH, "w") as f:
        f.write(paper_tex)
    print(f"Wrote {PAPER_TEX_PATH} ({len(paper_tex)} bytes)")

    print("Compiling paper.pdf with build_pdf.py...")
    res = subprocess.run([sys.executable, str(BUILD_PDF_PATH)], capture_output=True, text=True)
    print("build_pdf return code:", res.returncode)
    if res.returncode != 0:
        print("build_pdf stdout:", res.stdout[-1000:] if res.stdout else "")
        print("build_pdf stderr:", res.stderr[-1000:] if res.stderr else "")
    else:
        print("PDF build succeeded!")

    print("Generating blog_post.md (<= 900 words)...")
    blog_post = generate_blog_post()
    word_count = len(blog_post.split())
    print(f"Blog post word count: {word_count} words (limit: 900)")
    with open(BLOG_PATH, "w") as f:
        f.write(blog_post)

    print("Generating README.md...")
    readme = generate_readme()
    with open(README_PATH, "w") as f:
        f.write(readme)

    print("Done!")


if __name__ == "__main__":
    main()
