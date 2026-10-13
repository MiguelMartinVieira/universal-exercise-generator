import os
import re
import yaml

def map_course(profile_name):
    p = profile_name.lower()
    if "1eso" in p: return "1º ESO"
    if "2eso" in p: return "2º ESO"
    if "3eso" in p: return "3º ESO"
    if "4eso" in p: return "4º ESO"
    if "1bach" in p: return "1º Bach"
    if "2bach" in p: return "2º Bach"
    if "ceu" in p: return "CEU"
    if "ingles" in p: return "Inglés"
    return "General"

def extract_topics(profile_dir):
    prompt_file = os.path.join(profile_dir, "prompts", "base_prompt.txt")
    if not os.path.exists(prompt_file):
        return []
    
    topics = []
    with open(prompt_file, "r", encoding="utf-8") as f:
        for line in f:
            if re.search(r'(?i)(topic is|tema es)', line):
                matches = re.findall(r'"([^"]+)"', line)
                if matches:
                    # Select the first quoted string as the primary topic name
                    topics.append(matches[0])
    return topics

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    profiles_dir = os.path.join(root_dir, "profiles")
    jobs_file = os.path.join(root_dir, "jobs.yaml")
    
    if not os.path.exists(profiles_dir):
        print("Profiles directory not found.")
        return

    profiles = [
        "matematicas_1ESO_Departamental",
        "matematicas_2ESO_Departamental",
        "matematicas_3ESO_Departamental"
    ]
    jobs = []
    difficulties = [1, 2, 3, 3, 4]
    
    for profile in profiles:
        course = map_course(profile)
        profile_path = os.path.join(profiles_dir, profile)
        topics = extract_topics(profile_path)
        
        if not topics:
            topics = ["Repaso General"]
            
        for topic in topics:
            for diff in difficulties:
                job = {
                    "profile": profile,
                    "topic": topic,
                    "course": course,
                    "difficulty": diff,
                    "quantity": 10,
                    "quality": "pro"
                }
                jobs.append(job)

    with open(jobs_file, "w", encoding="utf-8") as f:
        yaml.dump(jobs, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
    print(f"Successfully generated {len(jobs)} jobs across {len(profiles)} profiles in jobs.yaml.")

if __name__ == "__main__":
    main()
