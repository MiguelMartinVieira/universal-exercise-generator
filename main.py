import os
import sys
import logging
import subprocess
from datetime import datetime

# Setup paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.profile_manager import ProfileManager
from core.pipeline import Pipeline
from core.renderer import LatexRenderer
from core.config import global_config
from core.ui import (
    print_header,
    print_error,
    print_success,
    print_info,
    input_text,
    input_int,
    clear_screen,
)
from core.setup import check_setup

# Configure logging to file to keep console clean
logging.basicConfig(
    filename="generator.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def main():
    print_header()

    # 1. Setup & Check
    root_dir = os.path.dirname(os.path.abspath(__file__))
    profiles_dir = os.path.join(root_dir, "profiles")
    templates_dir = os.path.join(root_dir, "templates")

    if not check_setup(root_dir):
        input("\nPress Enter to exit...")
        return

    # Re-load config might be needed if env changed, but typically redundant if dotenv loaded well.
    # However, global_config loads at import time. We might need to force reload if key was just added.
    if not global_config.best_api_key:
        # Try manual reload of env
        from dotenv import load_dotenv

        load_dotenv(os.path.join(root_dir, ".env"), override=True)

    manager = ProfileManager(profiles_dir)
    pipeline = Pipeline(manager)
    renderer = LatexRenderer(templates_dir)

    # 2. Main Loop
    while True:
        print_header()
        profiles = manager.list_profiles()

        print("AVAILABLE PROFILES:")
        for i, p in enumerate(profiles):
            print(f"{i+1}. {p}")

        mass_opt = len(profiles) + 1
        create_opt = len(profiles) + 2
        exit_opt = len(profiles) + 3

        print(f"\n{mass_opt}. [MASS]  MASS LAUNCHER (Run jobs from jobs.yaml)")
        print(f"{create_opt}. [NEW]   CREATE NEW PROFILE")
        print(f"{exit_opt}. [EXIT]  EXIT")

        selection = input_int("\nSelect Option", min_val=1, max_val=exit_opt)

        if selection == exit_opt:
            print_info("Goodbye!")
            break

        if selection == create_opt:
            create_new_profile_ui(manager)
            continue

        if selection == mass_opt:
            run_mass_launcher(manager, pipeline, renderer, root_dir)
            input("\nPress Enter to continue...")
            continue

        # Profile Selected
        idx = selection - 1
        profile_name = profiles[idx]
        run_standard_mode(profile_name, pipeline, renderer, root_dir, manager)
        input("\nPress Enter to continue...")


def create_new_profile_ui(manager):
    print_info("--- Create New Profile ---")
    name = input_text("Profile Name (e.g., 'Physics')")
    if not name:
        return

    desc = input_text("Description (optional)", default=f"Exercises for {name}")

    if manager.create_profile(name, desc):
        print_success(f"Profile '{name}' created successfully!")
    else:
        print_error("Failed to create profile. Check logs.")

    input("Press Enter...")


def run_mass_launcher(manager, pipeline, renderer, root_dir):
    jobs_file = os.path.join(root_dir, "jobs.yaml")
    if not os.path.exists(jobs_file):
        print_error(f"'{jobs_file}' not found.")
        # Create dummy
        with open(jobs_file, "w") as f:
            f.write(
                "# Mass Generation Jobs\n- topic: 'Derivadas'\n  profile: 'matematicas_bach'\n  quantity: 10\n  difficulty: 3\n  quality: 'pro'\n"
            )
        print_info(f"Created example {jobs_file}. Edit it and run again.")
        return

    import yaml

    try:
        with open(jobs_file, "r", encoding="utf-8") as f:
            jobs = yaml.safe_load(f)
    except Exception as e:
        print_error(f"Error reading yaml: {e}")
        return

    if not isinstance(jobs, list):
        print_error("jobs.yaml must be a list of jobs.")
        return

    print_info(f"Starting Mass Generation of {len(jobs)} jobs...")
    for i, job in enumerate(jobs):
        print(f"\n--- Job {i+1}: {job.get('topic')} ---")
        p_name = job.get("profile", manager.list_profiles()[0])
        topic = job.get("topic", "Untitled")
        course = job.get("course", "")
        diff = job.get("difficulty", 3)
        qty = job.get("quantity", 5)
        quality = job.get("quality", "standard")

        exercises = pipeline.run(p_name, topic, diff, qty, model_quality=quality)
        if exercises:
            generate_pdf_output(exercises, topic, diff, renderer, root_dir, manager, course)
        else:
            print_error("Job failed.")


def run_standard_mode(profile_name, pipeline, renderer, root_dir, manager):
    clear_screen()
    print_header()
    print_info(f"Selected Profile: {profile_name}")

    topic = input_text("Materia/Tema (ej. Funciones, Álgebra)")
    if not topic:
        topic = "General Review"

    course = input_text("Curso (ej. 2º Bach, 4º ESO)")

    difficulty = input_int("Difficulty (1-5)", default=3, min_val=1, max_val=5)
    qty = input_int("Quantity", default=5, min_val=1, max_val=50)

    # Select Quality
    print_info("Select Model Quality:")
    print("   1. Standard (Fast) - Good for simple topics")
    print("   2. Pro (Best Reasoning) - Recommended for Math/Physics")
    q_sel = input_int("Select", default=1, min_val=1, max_val=2)
    model_quality = "pro" if q_sel == 2 else "standard"

    # Run Pipeline
    print(f"\n[AI] Generating content with AI ({model_quality})...")
    exercises = pipeline.run(
        profile_name, topic, difficulty, qty, model_quality=model_quality
    )

    if not exercises:
        print_error("Generation failed after retries.")
        return

    print_success(f"Generated {len(exercises)} exercises.")
    out_dir = generate_pdf_output(
        exercises, topic, difficulty, renderer, root_dir, manager, course
    )

    # Auto-open folder
    if out_dir:
        print_info("Opening output folder...")
        try:
            os.startfile(out_dir)
        except:
            pass  # Linux/Mac support skipped for now as per user OS


def get_unique_suffix(root_dir, base_name, extension=".pdf"):
    """
    Returns a suffix ("" or "_I", "_II"...) to ensure base_name + suffix + extension is unique.
    """
    if not os.path.exists(os.path.join(root_dir, base_name + extension)):
        return ""

    roman_numerals = [
        "_I",
        "_II",
        "_III",
        "_IV",
        "_V",
        "_VI",
        "_VII",
        "_VIII",
        "_IX",
        "_X",
    ]

    for suffix in roman_numerals:
        if not os.path.exists(os.path.join(root_dir, base_name + suffix + extension)):
            return suffix

    # Fallback
    import time

    return f"_{int(time.time())}"


def generate_pdf_output(exercises, topic, difficulty, renderer, root_dir, manager, course=""):
    print("[PDF] Compiling PDF...")

    context = {
        "titulo": topic,
        "subtitulo": f"{course} - Level {difficulty}" if course else f"Level {difficulty}",
        "exercises": exercises,
        "show_solutions": False,
    }

    # Determinar carpeta de destino
    base_folder_name = f"{topic} {course}".strip()
    academic_path = manager.get_config("academic_path", None)
    if academic_path:
        out_dir = os.path.join(root_dir, "2 - Materiales Académicos", academic_path, topic)
    else:
        # Fallback: carpeta outputs/ si no hay academic_path configurado
        date_str = datetime.now().strftime("%Y-%m-%d")
        out_dir = os.path.join(root_dir, "outputs", date_str, base_folder_name)

    # Normalize separators — Google Drive GVFS fails with mixed / and \ in paths
    out_dir = os.path.normpath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # Calculate Unique Suffix for Files
    base_name_clean = base_folder_name.replace(" ", "_")
    base_name_raw = f"{base_name_clean}_Ejercicios_{difficulty}"
    suffix = get_unique_suffix(out_dir, base_name_raw)

    final_base_name = f"{base_name_raw}{suffix}"
    tex_path = os.path.join(out_dir, f"{final_base_name}.tex")

    tpl_name = manager.get_config("latex_template", "base.tex")

    if renderer.render_tex(tpl_name, context, tex_path):
        pdf = renderer.compile_pdf(tex_path, out_dir)
        if pdf:
            print(f"   -> Created: {pdf}")
        renderer.clean_aux_files(tex_path, out_dir)

    context["show_solutions"] = True
    final_sol_name = f"{base_name_clean}_Soluciones_{difficulty}{suffix}"
    tex_path_sol = os.path.join(out_dir, f"{final_sol_name}.tex")

    if renderer.render_tex(tpl_name, context, tex_path_sol):
        pdf = renderer.compile_pdf(tex_path_sol, out_dir)
        if pdf:
            print(f"   -> Created: {pdf}")
        renderer.clean_aux_files(tex_path_sol, out_dir)

    print_success("Done!")
    return out_dir


if __name__ == "__main__":
    main()
