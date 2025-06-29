import csv
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Input and output paths
input_csv = "data/skills_en.csv"
output_json = "data/esco_skills.json"

# Read CSV and convert to JSON
skills = []
try:
    with open(input_csv, 'r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            skill_entry = {
                "skill": row.get("preferredLabel", "").strip(),
                "description": row.get("description", "").strip()
            }
            if skill_entry["skill"]:  # Skip empty skills
                skills.append(skill_entry)
    logger.info(f"Loaded {len(skills)} skills from {input_csv}")
except Exception as e:
    logger.error(f"Failed to read CSV: {e}")
    exit(1)

# Write to JSON
try:
    with open(output_json, 'w', encoding='utf-8') as json_file:
        json.dump(skills, json_file, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(skills)} skills to {output_json}")
except Exception as e:
    logger.error(f"Failed to write JSON: {e}")
    exit(1)