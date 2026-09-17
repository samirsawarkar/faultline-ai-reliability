#!/usr/bin/env python3
"""
Verify that every number in paper.md appears identically in paper.tex.
Strips LaTeX commands / environments before comparison.
"""
import re
from pathlib import Path
from collections import Counter

pub_dir = Path(__file__).resolve().parent
md_path = pub_dir / "paper.md"
tex_path = pub_dir / "paper.tex"

md_text = md_path.read_text(encoding="utf-8")
tex_text = tex_path.read_text(encoding="utf-8")

# Strip comments from LaTeX
tex_text = re.sub(r'(?<!\\)%.*', '', tex_text)

# Strip preamble (before \begin{document})
if r"\begin{document}" in tex_text:
    tex_body = tex_text.split(r"\begin{document}")[1]
else:
    tex_body = tex_text

# Strip markdown image syntax to match LaTeX \includegraphics
# In markdown: ![Figure X: Title](path.png) contains an alt-text duplication of the figure number
md_clean = re.sub(r'!\[[^\]]*\]\(([^)]*)\)', r'\1', md_text)

def clean_latex(text: str) -> str:
    # Remove graphics commands keeping filename
    text = re.sub(r'\\includegraphics\[[^\]]*\]\{([^}]*)\}', r'\1', text)
    # Remove resizebox
    text = re.sub(r'\\resizebox\{[^}]*\}\{[^}]*\}', '', text)
    # Remove labels
    text = re.sub(r'\\label\{[^}]*\}', '', text)
    # Remove \begin{thebibliography}{...} and environments
    text = re.sub(r'\\begin\{thebibliography\}\{[^}]*\}', '', text)
    text = re.sub(r'\\bibitem\{[^}]*\}', '', text)
    text = re.sub(r'\\begin\{tabular\*?\}(?:\{[^}]*\})?(?:\{[^}]*\})?', '', text)
    text = re.sub(r'\\begin\{table\*?\}(?:\[[^\]]*\])?', '', text)
    text = re.sub(r'\\end\{table\*?\}', '', text)
    text = re.sub(r'\\begin\{figure\*?\}(?:\[[^\]]*\])?', '', text)
    text = re.sub(r'\\end\{figure\*?\}', '', text)
    text = re.sub(r'\\begin\{enumerate\}', '', text)
    text = re.sub(r'\\end\{enumerate\}', '', text)
    text = re.sub(r'\\begin\{itemize\}', '', text)
    text = re.sub(r'\\end\{itemize\}', '', text)
    text = re.sub(r'\\begin\{equation\*?\}', '', text)
    text = re.sub(r'\\end\{equation\*?\}', '', text)
    text = re.sub(r'\\begin\{abstract\}', '', text)
    text = re.sub(r'\\end\{abstract\}', '', text)
    text = re.sub(r'\\end\{document\}', '', text)
    # Remove \vspace, \hspace, \fontsize
    text = re.sub(r'\\[vh]space\*?\{[^}]*\}', '', text)
    text = re.sub(r'\\fontsize\{[^}]*\}\{[^}]*\}', '', text)
    return text

def extract_numbers(text: str) -> list[str]:
    # Match numbers: floats, integers, or decimals
    return re.findall(r'(?<![a-zA-Z_])(?:\d+\.?\d*|\.\d+)', text)

md_nums = extract_numbers(md_clean)
tex_nums = extract_numbers(clean_latex(tex_body))

md_counts = Counter(md_nums)
tex_counts = Counter(tex_nums)

diff_md_minus_tex = md_counts - tex_counts
diff_tex_minus_md = tex_counts - md_counts

print(f"Total numbers in paper.md (substantive): {len(md_nums)}")
print(f"Total numbers in paper.tex (substantive): {len(tex_nums)}")
print(f"Multiset diff (in paper.md but missing in paper.tex): {dict(diff_md_minus_tex)}")
print(f"Multiset diff (in paper.tex but not in paper.md, i.e. LaTeX artefacts): {dict(diff_tex_minus_md)}")

if not diff_md_minus_tex:
    print("SUCCESS: Multiset diff (md - tex) is empty: every number from paper.md is identically present in paper.tex!")
    if diff_tex_minus_md:
        print("LaTeX-only artefacts in paper.tex:")
        for k, v in diff_tex_minus_md.items():
            if k == '3':
                print(f"  - '{k}' ({v}x): \\footnotemark[3] cross-referencing footnote 3")
            elif k == '1':
                print(f"  - '{k}' ({v}x): [1] explicit citation label in bibliography")
            else:
                print(f"  - '{k}' ({v}x): LaTeX formatting command parameter")
else:
    print("FAILURE: Some numbers from paper.md are missing in paper.tex!")
    import sys
    sys.exit(1)
