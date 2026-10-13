import logging
import re
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from google import genai
from google.genai import types

from .config import global_config

logger = logging.getLogger(__name__)


class PipelineTeoria:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or global_config.best_api_key
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def run(
        self,
        topic: str,
        context_files: List[str] = None,
        model_name: str = "gemini-2.5-flash",
        max_retries: int = 5,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Executes the theory generation pipeline using Text parsing instead of JSON mode.
        """
        if not self.client:
            logger.error("No API KEY found.")
            return None

        prompt_parts = self._build_prompt(topic, context_files)
        final_prompt = "\n".join(prompt_parts)

        for attempt in range(max_retries):
            logger.info(
                f"--- Attempt {attempt + 1}/{max_retries} for Theory Generation (Text Mode) ---"
            )

            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=final_prompt,
                    config=types.GenerateContentConfig(
                        candidate_count=1,
                        max_output_tokens=8192,
                        temperature=1.0,
                    ),
                )

                if response.text:
                    sections = self._parse_text_to_sections(response.text)
                    if sections:
                        self._clean_data(sections)
                        return sections
                    else:
                        logger.warning("Generation yielded 0 sections. Retrying...")
            except Exception as e:
                logger.error(f"Generation error: {e}")

            logger.warning("Retrying...")

        logger.error("Max retries reached. Generation failed.")
        return None

    def _build_prompt(self, topic: str, context_files: List[str]) -> List[str]:

        context_text = ""
        if context_files:
            for fpath in context_files:
                if os.path.exists(fpath):
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            content = f.read()
                            context_text += f"\n--- DOCUMENT: {os.path.basename(fpath)} ---\n{content}\n"
                    except Exception as e:
                        logger.error(f"Failed to load resource {fpath}: {e}")

        final_prompt = f"""
ROLE: Expert Math Teacher / Textbook Author writing a LaTeX textbook chapter.
TASK: Write a detailed, very pedagogical, theory chapter on the TOPIC provided below.

TOPIC: {topic}

INSTRUCTIONS:
You must return the generated theory in a specific custom TEXT format (NOT JSON, NOT HTML, NOT Markdown), so we can parse it easily.
DO NOT use backticks, DO NOT use HTML tags (no <ul>, <li>, <ol>, <b>, <i>, <br>, <p> etc.), DO NOT use Markdown formatting (* for bold, _ for italic, # for headers).

ALL OUTPUT MUST BE PURE LaTeX-COMPATIBLE TEXT. For lists, use LaTeX \\begin{{itemize}} ... \\item ... \\end{{itemize}} or \\begin{{enumerate}} ... \\item ... \\end{{enumerate}}.

FORMAT RULES:
1. Every section starts with: `<SECTION> Section Title` on a new line.
2. Inside the section, you output multiple blocks. Each block starts with a tag and ends with an end tag.
3. The allowed block tags are `<TEXTO>`, `<DEFINICION>`, `<EJEMPLO>`, `<NOTA>`, and `<TIKZ>`.
4. End the blocks with `</TEXTO>`, `</DEFINICION>`, `</EJEMPLO>`, `</NOTA>`, and `</TIKZ>`.
5. For `<TIKZ>`, provide an optional caption on the same line like: `<TIKZ> Caption text here`. Then on the NEXT line(s) output ONLY pgfplots axis code (\\begin{{axis}}...\\end{{axis}}) or raw tikz drawing commands. Do NOT include \\begin{{tikzpicture}} or \\end{{tikzpicture}}. End the block with `</TIKZ>`.
6. For other blocks, write the instructional text. Use LaTeX formatting for math:
   - Inline math: $...$
   - Display math: $$...$$
   - Fractions: \\frac{{a}}{{b}}
   - Square roots: \\sqrt{{x}}
   - Greek letters: \\alpha, \\beta, etc.
7. For lists, ALWAYS use LaTeX: \\begin{{itemize}} \\item ... \\end{{itemize}} or \\begin{{enumerate}} \\item ... \\end{{enumerate}}. NEVER use HTML lists or Markdown lists.
8. For bold text, use \\textbf{{...}}. For italic, use \\textit{{...}}.

CRITICAL RULES:
- NEVER output HTML tags like <ul>, <li>, <ol>, <b>, <i>, <br>, <p>, <table>, <td>, <tr>.
- NEVER use Markdown-style ** for bold or * for italic or _ for italic.
- NEVER use Markdown-style headings (#, ##, ###).
- NEVER use triple backticks (```).
- For TikZ drawings: use ONLY pgfplots \\begin{{axis}}...\\end{{axis}} environments with \\addplot. Do NOT try to draw raw \\draw commands for function plots. For simple diagrams (triangles, circles), raw \\draw is fine but use stealth arrows instead of ->.
- ALL text outside of $ or $$ must be valid LaTeX text (no unescaped special characters like _, #, %, &, ^).
- Ensure every \\begin{{...}} has a matching \\end{{...}}.

EXAMPLE OUTPUT:
<SECTION> Introduction
<TEXTO>
In this chapter, we will study the concept of polynomials. A polynomial is an algebraic expression of the form:
$$P(x) = a_n x^n + a_{{n-1}} x^{{n-1}} + \\cdots + a_1 x + a_0$$
where $a_n, a_{{n-1}}, \\ldots, a_0$ are real numbers called \\textbf{{coefficients}}.
</TEXTO>
<DEFINICION>
A \\textbf{{polynomial}} of degree $n$ is an expression $P(x) = a_n x^n + \\cdots + a_0$ where $a_n \\neq 0$.
</DEFINICION>
<EJEMPLO>
Consider $P(x) = 3x^2 + 2x - 1$. This is a polynomial of degree 2.
\\begin{{itemize}}
\\item The leading coefficient is $a_2 = 3$.
\\item The constant term is $a_0 = -1$.
\\end{{itemize}}
</EJEMPLO>
<TIKZ> Graph of a Parabola
\\begin{{axis}}[
    axis lines=middle,
    xlabel={{$x$}},
    ylabel={{$y$}},
    xmin=-4, xmax=4,
    ymin=-5, ymax=10,
    grid=major
]
\\addplot[blue, thick, domain=-3:3, samples=50] {{3*x^2 + 2*x - 1}};
\\end{{axis}}
</TIKZ>

CONTEXT MATERIAL (If any, use it as inspiration for the level and topics to cover):
{context_text}
"""
        return [final_prompt]

    def _parse_text_to_sections(self, text: str) -> List[Dict[str, Any]]:
        sections = []

        # Split by <SECTION>
        parts = text.split("<SECTION>")
        for part in parts:
            part = part.strip()
            if not part:
                continue

            # First line is the title
            lines = part.split("\n", 1)
            title = lines[0].strip()
            content_str = lines[1] if len(lines) > 1 else ""

            current_section = {"titulo": title, "bloques": []}

            # Pattern matches <TAG>( optional caption)\n(content)\n</TAG>
            pattern = r"<(TEXTO|DEFINICION|EJEMPLO|NOTA|TIKZ)>(.*?)\n(.*?)</\1>"
            matches = re.finditer(pattern, content_str, re.DOTALL | re.IGNORECASE)

            for match in matches:
                tag = match.group(1).lower()
                caption = match.group(2).strip()
                content = match.group(3).strip()

                block = {"tipo": tag, "contenido": content}
                if tag == "tikz":
                    block["titulo"] = caption if caption else "Figura"

                current_section["bloques"].append(block)

            if current_section["bloques"]:
                sections.append(current_section)

        return sections

    def _clean_data(self, data: List[Dict[str, Any]]):
        for sec in data:
            if "bloques" in sec:
                for b in sec["bloques"]:
                    if b.get("tipo") == "tikz":
                        b["contenido"] = self._fix_tikz(b["contenido"])
                    else:
                        if "contenido" in b:
                            b["contenido"] = self._fix_text(b["contenido"])

    def _fix_tikz(self, text: str) -> str:
        if not text:
            return ""

        # Strip any accidental \begin{tikzpicture} / \end{tikzpicture} wrappers
        text = re.sub(
            r"\\begin\{tikzpicture\}\s*(\[.*?\])?\s*(.*?)\s*\\end\{tikzpicture\}",
            r"\2",
            text,
            flags=re.DOTALL,
        )

        # Strip triple backticks that LLMs sometimes emit
        text = re.sub(r"```\w*\n?", "", text)

        # Replace -> with {stealth} in \draw commands (babel spanish conflict)
        # We'll use stealth arrows which don't conflict
        text = text.replace("->", "-{stealth}")
        text = text.replace("<-", "{stealth}-")

        # Wrap in tikzpicture
        text = f"\\begin{{tikzpicture}}\n{text}\n\\end{{tikzpicture}}"

        return text

    def _fix_text(self, text: str) -> str:
        if not text:
            return ""

        # ---- 0. Fix malformed LaTeX braces ----
        # LLM sometimes outputs \end{enumerate> instead of \end{enumerate}
        text = re.sub(r"\\end\{(\w+)>", r"\\end{\1}", text)
        text = re.sub(r"\\begin\{(\w+)>", r"\\begin{\1}", text)

        # Remove stray TikZ/draw commands that leaked into text blocks
        text = re.sub(r"\\draw\[.*?\].*?;\n?", "", text)
        text = re.sub(r"\\node\s+.*?;\n?", "", text)
        text = re.sub(r"\\fill\[.*?\].*?;\n?", "", text)

        # Remove leftover </TIKZ> or </SECTION> tags
        text = re.sub(
            r"</?(TIKZ|SECTION|TEXTO|DEFINICION|EJEMPLO|NOTA)>",
            "",
            text,
            flags=re.IGNORECASE,
        )

        # ---- 1. Remove triple backticks ----
        text = re.sub(r"```\w*\n?", "", text)

        # ---- 2. Convert HTML to LaTeX ----
        # Bold: <b>...</b> or <strong>...</strong>
        text = re.sub(r"<b>(.*?)</b>", r"\\textbf{\1}", text, flags=re.IGNORECASE)
        text = re.sub(
            r"<strong>(.*?)</strong>", r"\\textbf{\1}", text, flags=re.IGNORECASE
        )
        # Italic: <i>...</i> or <em>...</em>
        text = re.sub(r"<i>(.*?)</i>", r"\\textit{\1}", text, flags=re.IGNORECASE)
        text = re.sub(r"<em>(.*?)</em>", r"\\textit{\1}", text, flags=re.IGNORECASE)

        # Line breaks
        text = re.sub(r"<br\s*/?>", r"\\\\\\\\ ", text, flags=re.IGNORECASE)
        text = re.sub(r"<p>", r"\n\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</p>", r"", text, flags=re.IGNORECASE)

        # Convert HTML unordered lists to LaTeX itemize
        def _html_ul_to_latex(match):
            inner = match.group(1)
            items = re.findall(r"<li>(.*?)</li>", inner, re.DOTALL | re.IGNORECASE)
            if not items:
                return inner
            latex_items = "\n".join(f"\\item {item.strip()}" for item in items)
            return f"\\begin{{itemize}}\n{latex_items}\n\\end{{itemize}}"

        text = re.sub(
            r"<ul>(.*?)</ul>", _html_ul_to_latex, text, flags=re.DOTALL | re.IGNORECASE
        )

        # Convert HTML ordered lists to LaTeX enumerate
        def _html_ol_to_latex(match):
            inner = match.group(1)
            items = re.findall(r"<li>(.*?)</li>", inner, re.DOTALL | re.IGNORECASE)
            if not items:
                return inner
            latex_items = "\n".join(f"\\item {item.strip()}" for item in items)
            return f"\\begin{{enumerate}}\n{latex_items}\n\\end{{enumerate}}"

        text = re.sub(
            r"<ol>(.*?)</ol>", _html_ol_to_latex, text, flags=re.DOTALL | re.IGNORECASE
        )

        # Strip any remaining HTML tags
        text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)

        # ---- 3. Convert Markdown to LaTeX ----
        # Bold: **text** -> \textbf{text}
        text = re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", text)
        # Italic: *text* -> \textit{text} (but not inside math)
        text = re.sub(r"(?<!\$)\*(?!\*)(.*?)(?<!\*)\*(?!\$)", r"\\textit{\1}", text)

        # ---- 4. Fix unescaped special LaTeX characters outside math mode ----
        text = self._escape_special_outside_math(text)

        # ---- 5. Ensure balanced environments ----
        text = self._balance_environments(text)

        return text

    def _escape_special_outside_math(self, text: str) -> str:
        """Escape special LaTeX characters that appear outside of math mode."""
        # Split text into math and non-math segments
        # Pattern matches $...$ or $$...$$ blocks
        segments = re.split(r"(\$\$.*?\$\$|\$.*?\$)", text, flags=re.DOTALL)

        result = []
        for i, seg in enumerate(segments):
            if i % 2 == 1:
                # This is a math segment, leave it alone
                result.append(seg)
            else:
                # Non-math segment: escape dangerous characters
                # Don't escape \ (backslash) because it's used for LaTeX commands
                # Don't escape { } because they're used for LaTeX grouping
                # Escape: _ # % & (only if not already escaped)
                seg = re.sub(r"(?<!\\)_(?![{])", r"\\_", seg)
                # & outside of tabular
                # Don't touch & as it may be in align environments
                # # outside of \# commands
                seg = re.sub(r"(?<!\\)#(?!\{)", r"\\#", seg)
                result.append(seg)

        return "".join(result)

    def _balance_environments(self, text: str) -> str:
        """Ensure every \\begin{env} has a matching \\end{env}."""
        begins = re.findall(r"\\begin\{(\w+)\}", text)
        ends = re.findall(r"\\end\{(\w+)\}", text)

        # Count occurrences
        begin_counts = {}
        end_counts = {}
        for b in begins:
            begin_counts[b] = begin_counts.get(b, 0) + 1
        for e in ends:
            end_counts[e] = end_counts.get(e, 0) + 1

        # Add missing \end{} tags
        for env, count in begin_counts.items():
            end_count = end_counts.get(env, 0)
            if count > end_count:
                diff = count - end_count
                for _ in range(diff):
                    text += f"\n\\end{{{env}}}"
                    logger.warning(f"Added missing \\end{{{env}}}")

        return text
