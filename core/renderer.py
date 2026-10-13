import os
import subprocess
import logging
import re
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


class LatexRenderer:
    def __init__(self, templates_dir: str):
        self.templates_dir = templates_dir
        # Configure Jinja2 to match the legacy template style [[ var ]] and [% block %]
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            block_start_string="[%",
            block_end_string="%]",
            variable_start_string="[[",
            variable_end_string="]]",
            comment_start_string="[#",
            comment_end_string="#]",
        )

    def render_tex(self, template_name: str, context: dict, output_path: str) -> bool:
        """Renders the .tex file from template."""
        try:
            template = self.env.get_template(template_name)
            rendered = template.render(**context)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rendered)
            return True
        except Exception as e:
            logger.error(f"Render failed: {e}")
            return False

    def compile_pdf(self, tex_path: str, output_dir: str) -> str:
        """Compiles .tex to .pdf using pdflatex."""

        # Ensure output dir exists
        os.makedirs(output_dir, exist_ok=True)

        # Copy logo.png if exists
        import shutil

        logo_path = os.path.join(self.templates_dir, "logo.png")
        if os.path.exists(logo_path):
            try:
                shutil.copy(logo_path, os.path.join(output_dir, "logo.png"))
            except Exception as e:
                logger.warning(f"Failed to copy logo.png: {e}")

        # pdflatex run (twice for references)
        cmd = [
            "pdflatex",
            "-interaction=nonstopmode",
            f"-output-directory={output_dir}",
            tex_path,
        ]

        try:
            # First pass
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Second pass (for refs/page numbers)
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            pdf_name = os.path.splitext(os.path.basename(tex_path))[0] + ".pdf"
            pdf_path = os.path.join(output_dir, pdf_name)

            if os.path.exists(pdf_path):
                return pdf_path
            else:
                logger.error("PDF file was not created.")
                return ""
        except FileNotFoundError:
            logger.error("pdflatex not found. Ensure MiKTeX or TeX Live is installed.")
            return ""
        except Exception as e:
            logger.error(f"Compilation error: {e}")
            return ""

    def clean_aux_files(self, tex_path: str, output_dir: str):
        """Removes .aux, .log, .out, .tex files."""
        base = os.path.splitext(os.path.basename(tex_path))[0]
        extensions = [".aux", ".log", ".out", ".tex"]  # Limpieza completa

        for ext in extensions:
            f = os.path.join(output_dir, base + ext)
            if os.path.exists(f):
                os.remove(f)

        # Also clean logo.png which is a temporary artifact for compilation
        logo_out = os.path.join(output_dir, "logo.png")
        if os.path.exists(logo_out):
            try:
                os.remove(logo_out)
            except Exception:
                pass
