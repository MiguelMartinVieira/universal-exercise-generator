# 📚 Universal Exercise Generator — Autonomous AI Curriculum & Problem-Set Engine

[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![LLM Orchestration](https://img.shields.io/badge/LLMs-Google%20Gemini%20%26%20OpenAI-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev/)
[![LaTeX Engine](https://img.shields.io/badge/Rendering-Automated%20LaTeX%20%2F%20PDF-008080?style=flat-square&logo=latex&logoColor=white)](templates/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

> An autonomous batch-generation factory producing publication-grade academic STEM problem sets and verified solution keys from declarative YAML curriculum specifications. Deployed in production at **Academia Ítaca** to generate hundreds of verified academic problem sets spanning secondary education to elite university entrance exams.

---

## 🏛️ Pipeline Architecture

```mermaid
flowchart TD
    Config["📋 Batch Jobs Specification<br/>(jobs.yaml)"] --> Launcher["⚙️ Mass Launcher Dispatcher<br/>(main.py / run_jobs.py)"]

    subgraph ProfileLayer ["1. Curriculum & Pedagogical Context"]
        Profile["📂 Subject Profile (profiles/{name}/)<br/>• config.yaml (model, validation, academic_path)<br/>• base_prompt.txt (system persona)<br/>• resources/ (theory & syllabus references)"]
    end

    Launcher --> ProfileLayer

    subgraph GenerationLayer ["2. LLM Orchestration & Prompt Synthesis"]
        LLM["🤖 Model Cascade (Gemini Flash / Pro)<br/>• Exercise statement synthesis<br/>• Step-by-step rigorous solutions<br/>• Pedagogical sanity checks"]
    end

    ProfileLayer --> GenerationLayer

    subgraph RenderingLayer ["3. LaTeX Sanitization & Compilation"]
        Sanitizer["🧹 Syntax & KaTeX Sanitizer<br/>(core/validator.py)"]
        Renderer["📄 LaTeX Jinja/Format Renderer<br/>(templates/base.tex)"]
        Compiler["⚡ Automated PDF Compiler (pdflatex / tectonic)"]
        
        Sanitizer --> Renderer
        Renderer --> Compiler
    end

    GenerationLayer --> RenderingLayer

    subgraph RoutingLayer ["4. Dynamic Filesystem Routing"]
        Tree["📂 Hierarchical Knowledge Repository<br/>{Subject}/{Course}/{Topic}/ProblemSet.pdf"]
    end

    Compiler --> RoutingLayer
```

---

## ⚡ Key Architectural Highlights

### 1. Declarative Curriculum Specifications
Every academic subject and level is declared as an isolated profile without modifying application code:
```yaml
# profiles/matematicas_2bach_ciencias/config.yaml
name: "Matemáticas II — 2º Bachillerato Ciencias"
subject: "Matemáticas"
level: "2_BACH"
academic_path: "1. Matemáticas/Matemáticas - 2º BACH/Ciencias/Ítaca"
validation:
  require_step_by_step_solutions: true
  enforce_latex_math_blocks: true
```

### 2. Autonomous Mass Batch Launcher
Enables batch execution of entire multi-topic curriculum syllabi in a single scheduled execution pass via `jobs.yaml`:
```bash
python main.py
# Select Option 11 (MASS LAUNCHER)
```

### 3. LaTeX Sanitization & Robust Fallbacks
Raw LLM outputs frequently produce invalid LaTeX escapes or conflicting symbol definitions. 
- `core/validator.py` applies AST-like regex sanitization to mathematical delimeters (`$`, `$$`, `\begin{align*}`).
- Verifies balance of delimiters before spawning compilation subprocesses.

---

## 🚀 Quickstart

```bash
# Clone the repository
git clone https://github.com/MiguelMartinVieira/universal-exercise-generator.git
cd universal-exercise-generator

# Install dependencies via uv
uv sync

# Configure API credentials
cp .env.example .env

# Run generator CLI
python main.py
```
