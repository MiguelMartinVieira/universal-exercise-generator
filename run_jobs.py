"""Script no-interactivo para ejecutar todos los jobs de jobs.yaml."""
import os
import sys
import yaml
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.profile_manager import ProfileManager
from core.pipeline import Pipeline
from core.renderer import LatexRenderer
from core.config import global_config

logging.basicConfig(
    filename="generator.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def get_unique_suffix(root_dir, base_name, extension=".pdf"):
    if not os.path.exists(os.path.join(root_dir, base_name + extension)):
        return ""
    roman = ["_I", "_II", "_III", "_IV", "_V", "_VI", "_VII", "_VIII", "_IX", "_X"]
    for suffix in roman:
        if not os.path.exists(os.path.join(root_dir, base_name + suffix + extension)):
            return suffix
    import time
    return f"_{int(time.time())}"


def generate_pdf_output(exercises, topic, difficulty, renderer, root_dir, manager, course=""):
    print(f"  [PDF] Compilando PDF para '{topic}' dif={difficulty}...")

    context = {
        "titulo": topic,
        "subtitulo": f"{course} - Nivel {difficulty}" if course else f"Nivel {difficulty}",
        "exercises": exercises,
        "show_solutions": False,
    }

    base_folder_name = f"{topic} {course}".strip()
    academic_path = manager.get_config("academic_path", None)
    if academic_path:
        out_dir = os.path.join(root_dir, "2 - Materiales Académicos", academic_path, topic)
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        out_dir = os.path.join(root_dir, "outputs", date_str, base_folder_name)

    out_dir = os.path.normpath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    print(f"  [DIR] {out_dir}")

    base_name_clean = base_folder_name.replace(" ", "_")
    base_name_raw = f"{base_name_clean}_Ejercicios_{difficulty}"
    suffix = get_unique_suffix(out_dir, base_name_raw)
    final_base = f"{base_name_raw}{suffix}"
    tex_path = os.path.join(out_dir, f"{final_base}.tex")

    tpl_name = manager.get_config("latex_template", "base.tex")

    if renderer.render_tex(tpl_name, context, tex_path):
        pdf = renderer.compile_pdf(tex_path, out_dir)
        if pdf:
            print(f"  [OK]  Ejercicios -> {os.path.basename(pdf)}")
        else:
            print(f"  [ERR] pdflatex fallo en ejercicios")
        renderer.clean_aux_files(tex_path, out_dir)
    else:
        print(f"  [ERR] render_tex fallo para ejercicios")

    context["show_solutions"] = True
    final_sol = f"{base_name_clean}_Soluciones_{difficulty}{suffix}"
    tex_path_sol = os.path.join(out_dir, f"{final_sol}.tex")

    if renderer.render_tex(tpl_name, context, tex_path_sol):
        pdf = renderer.compile_pdf(tex_path_sol, out_dir)
        if pdf:
            print(f"  [OK]  Soluciones -> {os.path.basename(pdf)}")
        else:
            print(f"  [ERR] pdflatex fallo en soluciones")
        renderer.clean_aux_files(tex_path_sol, out_dir)
    else:
        print(f"  [ERR] render_tex fallo para soluciones")

    return out_dir


def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    profiles_dir = os.path.join(root_dir, "profiles")
    templates_dir = os.path.join(root_dir, "templates")

    manager = ProfileManager(profiles_dir)
    pipeline = Pipeline(manager)
    renderer = LatexRenderer(templates_dir)

    jobs_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root_dir, "jobs.yaml")
    with open(jobs_file, "r", encoding="utf-8") as f:
        jobs = yaml.safe_load(f)

    print(f"\n{'='*50}")
    print(f"  MASS LAUNCHER — {len(jobs)} jobs")
    print(f"{'='*50}\n")

    ok = 0
    fail = 0
    for i, job in enumerate(jobs):
        p_name  = job.get("profile", "")
        topic   = job.get("topic", "Untitled")
        course  = job.get("course", "")
        diff    = job.get("difficulty", 3)
        qty     = job.get("quantity", 5)
        quality = job.get("quality", "standard")

        print(f"[Job {i+1}/{len(jobs)}] {topic} | dif={diff} | qty={qty} | {quality}")

        exercises = pipeline.run(p_name, topic, diff, qty, model_quality=quality)
        if not exercises:
            print(f"  [FAIL] Generacion fallida\n")
            fail += 1
            continue

        print(f"  [AI]  {len(exercises)} ejercicios generados")
        generate_pdf_output(exercises, topic, diff, renderer, root_dir, manager, course)
        ok += 1
        print()

    print(f"\n{'='*50}")
    print(f"  Completado: {ok} OK / {fail} fallidos")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
