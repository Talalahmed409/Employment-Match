import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
EMBEDDER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.3  # Lowered to capture related skills (e.g., PyTorch -> Python)
FUZZY_THRESHOLD = 80  # Lowered to improve fuzzy matching

def load_skills(file_path):
    """Load skills from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('raw', [])
    except Exception as e:
        logging.error(f"Error loading skills from {file_path}: {e}")
        return []

def compute_embeddings(skills, model):
    """Compute embeddings for a list of skills."""
    try:
        return model.encode(skills, batch_size=100, show_progress_bar=False)
    except Exception as e:
        logging.error(f"Error computing embeddings: {e}")
        return np.array([])

def match_skills(cv_skills, job_skills, model):
    """Match raw skills from CV and job description."""
    if not cv_skills or not job_skills:
        logging.warning("Empty skill list provided")
        return {"match_score": 0.0, "matched_skills": [], "missing_skills": job_skills, "extra_skills": cv_skills}

    # Compute embeddings
    cv_embeddings = compute_embeddings(cv_skills, model)
    job_embeddings = compute_embeddings(job_skills, model)

    if cv_embeddings.size == 0 or job_embeddings.size == 0:
        logging.error("Failed to compute embeddings")
        return {"match_score": 0.0, "matched_skills": [], "missing_skills": job_skills, "extra_skills": cv_skills}

    # Compute cosine similarity matrix
    similarity_matrix = cosine_similarity(cv_embeddings, job_embeddings)

    matched_skills = []
    missing_skills = job_skills.copy()
    extra_skills = cv_skills.copy()

    # Match skills based on embedding similarity
    for i, cv_skill in enumerate(cv_skills):
        max_sim = np.max(similarity_matrix[i])
        max_idx = np.argmax(similarity_matrix[i])
        job_skill = job_skills[max_idx]
        logging.info(f"Comparing '{cv_skill}' to '{job_skill}': similarity={max_sim:.3f}")

        if max_sim >= SIMILARITY_THRESHOLD:
            matched_skills.append({"cv_skill": cv_skill, "job_skill": job_skill, "similarity": float(max_sim)})  # Convert to float
            if job_skill in missing_skills:
                missing_skills.remove(job_skill)
            if cv_skill in extra_skills:
                extra_skills.remove(cv_skill)
        else:
            # Fallback to fuzzy matching
            for job_skill in job_skills:
                fuzzy_score = fuzz.ratio(cv_skill.lower(), job_skill.lower())
                logging.info(f"Fuzzy match '{cv_skill}' to '{job_skill}': score={fuzzy_score}")
                if fuzzy_score >= FUZZY_THRESHOLD:
                    matched_skills.append({"cv_skill": cv_skill, "job_skill": job_skill, "fuzzy_score": float(fuzzy_score)})  # Convert to float
                    if job_skill in missing_skills:
                        missing_skills.remove(job_skill)
                    if cv_skill in extra_skills:
                        extra_skills.remove(cv_skill)
                    break

    # Calculate match score
    match_score = (len(matched_skills) / len(job_skills)) * 100 if job_skills else 0.0

    return {
        "match_score": round(match_score, 2),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "extra_skills": extra_skills
    }

def main():
    # Example input files (replace with actual paths)
    cv_skills_file = "data/cv_skills.json"
    job_skills_file = "data/job_skills.json"

    # Load skills
    cv_skills = load_skills(cv_skills_file)
    job_skills = load_skills(job_skills_file)

    # Initialize embedder
    try:
        model = SentenceTransformer(EMBEDDER_MODEL)
    except Exception as e:
        logging.error(f"Error loading embedder model: {e}")
        return

    # Match skills
    result = match_skills(cv_skills, job_skills, model)

    # Output result
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()