#!/usr/bin/env python3
import json
import os
import sys
import logging
from typing import List, Dict, Any
import numpy as np
import torch
from dotenv import load_dotenv
from rapidfuzz import process, fuzz
import PyPDF2

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check for required dependencies
try:
    import google.generativeai as genai
    from google.generativeai.generative_models import GenerativeModel
    from google.generativeai.types import GenerationConfig
    from google.generativeai.client import configure
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as e:
    logger.error(f"Missing dependencies: {e}. Install with: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple")
    sys.exit(1)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in .env file")
    sys.exit(1)
GEMINI_MODEL = "gemini-1.5-flash"
EMBEDDER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
ESCO_FILE_PATH = "data/esco_skills.json"
EMBEDDINGS_FILE_PATH = "data/esco_embeddings.npy"
SIMILARITY_THRESHOLD = 0.4  # For embedding-based matching
FUZZY_THRESHOLD = 90  # For fuzzy matching fallback
BATCH_SIZE = 100
TOP_N = 3  # Log top-3 matches for debugging

# Initialize Gemini API client
try:
    configure(api_key=GEMINI_API_KEY)
    gemini_client = GenerativeModel(GEMINI_MODEL)
    logger.info(f"Successfully initialized Gemini client with model: {GEMINI_MODEL}")
except Exception as e:
    logger.error(f"Failed to initialize Gemini client: {e}")
    sys.exit(1)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            logger.info(f"Successfully extracted text from {pdf_path}")
            return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
        return ""

def load_esco_skills(file_path: str) -> List[Dict[str, str]]:
    """Load ESCO skills taxonomy or use default subset."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                esco_skills = json.load(f)
                logger.info(f"Loaded {len(esco_skills)} skills from {file_path}")
                return esco_skills
        except Exception as e:
            logger.error(f"Failed to load ESCO file: {e}")
    logger.warning(f"ESCO file {file_path} not found. Using default subset.")
    return [
        {"skill": "Python programming", "description": "Write and debug code in Python."},
        {"skill": "SQL", "description": "Query relational databases using SQL."},
        {"skill": "Communication", "description": "Effective verbal and written communication."},
        {"skill": "Problem-solving", "description": "Analyze and resolve complex issues."},
        {"skill": "Agile methodologies", "description": "Experience with Agile processes."}
    ]

def load_embedder():
    """Load sentence transformer model."""
    try:
        embedder = SentenceTransformer(EMBEDDER_MODEL)
        logger.info(f"Successfully loaded embedder: {EMBEDDER_MODEL}")
        return embedder
    except Exception as e:
        logger.error(f"Failed to load embedder: {e}")
        sys.exit(1)

def summarize_cv(cv_text: str) -> str:
    """Summarize CV using Gemini API to extract skills."""
    prompt = f"Summarize the following CV, focusing on technical and soft skills. Return a comma-separated list of skills:\n{cv_text}"
    try:
        response = gemini_client.generate_content(
            prompt,
            generation_config=GenerationConfig(
                temperature=0.7,
                max_output_tokens=70
            )
        )
        skill_list = response.text.strip()
        logger.info(f"Extracted skill summary from CV: {skill_list}")
        return skill_list
    except Exception as e:
        logger.error(f"Error in Gemini API call: {e}")
        return ""

def get_embeddings(texts: List[str], embedder: Any, batch_size: int = BATCH_SIZE) -> np.ndarray:
    """Generate embeddings in batches."""
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            batch_embeddings = embedder.encode(batch)
            embeddings.append(batch_embeddings)
        except Exception as e:
            logger.error(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
            return np.array([])
    return np.vstack(embeddings) if embeddings else np.array([])

def load_precomputed_embeddings(file_path: str) -> np.ndarray:
    """Load precomputed embeddings from file."""
    if os.path.exists(file_path):
        try:
            # Try loading with allow_pickle=True first
            embeddings = np.load(file_path, allow_pickle=True)
            logger.info(f"Loaded precomputed embeddings from {file_path}")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to load embeddings: {e}")
            # If loading fails, try to delete the corrupted file
            try:
                os.remove(file_path)
                logger.info(f"Deleted corrupted embeddings file: {file_path}")
            except:
                pass
    logger.warning(f"Embeddings file {file_path} not found.")
    return np.array([])  # Return empty array instead of None

def extract_cv_skills(pdf_path: str, esco_skills: List[Dict[str, str]], embedder: Any) -> Dict[str, List[str]]:
    """Extract and standardize skills from a CV PDF."""
    cv_text = extract_text_from_pdf(pdf_path)
    if not cv_text:
        logger.warning("No text extracted from PDF, returning empty skills.")
        return {"standardized": [], "raw": []}

    skill_summary = summarize_cv(cv_text)
    if not skill_summary:
        return {"standardized": [], "raw": []}

    raw_skills = [s.strip() for s in skill_summary.split(",") if s.strip()]
    
    # Try loading precomputed embeddings
    esco_embeddings = load_precomputed_embeddings(EMBEDDINGS_FILE_PATH)
    if esco_embeddings.size == 0:
        logger.info("Computing ESCO embeddings as precomputed file not found.")
        esco_texts = [skill["skill"] + ": " + skill["description"] for skill in esco_skills]
        esco_embeddings = get_embeddings(esco_texts, embedder)
        if esco_embeddings.size == 0:
            logger.warning("No embeddings generated for ESCO skills.")
            return {"standardized": [], "raw": raw_skills}
    
    raw_skill_embeddings = get_embeddings(raw_skills, embedder)
    similarities = cosine_similarity(raw_skill_embeddings, esco_embeddings)
    standardized_skills = []
    esco_skill_names = [skill["skill"] for skill in esco_skills]

    for i, skill_similarities in enumerate(similarities):
        top_indices = np.argsort(skill_similarities)[-TOP_N:][::-1]  # Top-N indices
        top_scores = skill_similarities[top_indices]
        top_skills = [esco_skills[idx]["skill"] for idx in top_indices]
        
        # Log top-N matches
        logger.info(f"Top-{TOP_N} matches for '{raw_skills[i]}':")
        for skill, score in zip(top_skills, top_scores):
            logger.info(f"  {skill}: {score:.3f}")
        
        # Use embedding match if above threshold
        top_idx = top_indices[0]
        if skill_similarities[top_idx] >= SIMILARITY_THRESHOLD:
            standardized_skills.append(esco_skills[top_idx]["skill"])
        else:
            # Fallback to fuzzy matching
            fuzzy_match = process.extractOne(raw_skills[i], esco_skill_names, scorer=fuzz.WRatio)
            if fuzzy_match and fuzzy_match[1] >= FUZZY_THRESHOLD:
                standardized_skills.append(fuzzy_match[0])
                logger.info(f"Fuzzy match for '{raw_skills[i]}': '{fuzzy_match[0]}' (score: {fuzzy_match[1]})")

    logger.info(f"Standardized skills: {standardized_skills}")
    logger.info(f"Raw skills: {raw_skills}")
    return {"standardized": list(set(standardized_skills)), "raw": list(set(raw_skills))}

def extract_cv_skills_from_text(cv_text: str, esco_skills: List[Dict[str, str]], embedder: Any) -> Dict[str, List[str]]:
    """Extract and standardize skills from CV text (for fallback)."""
    skill_summary = summarize_cv(cv_text)
    if not skill_summary:
        return {"standardized": [], "raw": []}

    raw_skills = [s.strip() for s in skill_summary.split(",") if s.strip()]
    
    esco_embeddings = load_precomputed_embeddings(EMBEDDINGS_FILE_PATH)
    if esco_embeddings.size == 0:
        logger.info("Computing ESCO embeddings as precomputed file not found.")
        esco_texts = [skill["skill"] + ": " + skill["description"] for skill in esco_skills]
        esco_embeddings = get_embeddings(esco_texts, embedder)
        if esco_embeddings.size == 0:
            logger.warning("No embeddings generated for ESCO skills.")
            return {"standardized": [], "raw": raw_skills}
    
    raw_skill_embeddings = get_embeddings(raw_skills, embedder)
    similarities = cosine_similarity(raw_skill_embeddings, esco_embeddings)
    standardized_skills = []
    esco_skill_names = [skill["skill"] for skill in esco_skills]

    for i, skill_similarities in enumerate(similarities):
        top_indices = np.argsort(skill_similarities)[-TOP_N:][::-1]
        top_scores = skill_similarities[top_indices]
        top_skills = [esco_skills[idx]["skill"] for idx in top_indices]
        
        logger.info(f"Top-{TOP_N} matches for '{raw_skills[i]}':")
        for skill, score in zip(top_skills, top_scores):
            logger.info(f"  {skill}: {score:.3f}")
        
        top_idx = top_indices[0]
        if skill_similarities[top_idx] >= SIMILARITY_THRESHOLD:
            standardized_skills.append(esco_skills[top_idx]["skill"])
        else:
            fuzzy_match = process.extractOne(raw_skills[i], esco_skill_names, scorer=fuzz.WRatio)
            if fuzzy_match and fuzzy_match[1] >= FUZZY_THRESHOLD:
                standardized_skills.append(fuzzy_match[0])
                logger.info(f"Fuzzy match for '{raw_skills[i]}': '{fuzzy_match[0]}' (score: {fuzzy_match[1]})")

    logger.info(f"Standardized skills: {standardized_skills}")
    logger.info(f"Raw skills: {raw_skills}")
    return {"standardized": list(set(standardized_skills)), "raw": list(set(raw_skills))}

def main():
    """Main function to run CV skill extraction and save to JSON."""
    esco_skills = load_esco_skills(ESCO_FILE_PATH)
    embedder = load_embedder()
    # For testing, use a PDF file path or fallback to sample text
    pdf_path = "data/sample_cv.pdf"  # Replace with your PDF path
    if not os.path.exists(pdf_path):
        logger.warning(f"PDF file {pdf_path} not found, using sample CV text.")
        cv_text = """
        Mahmoud Salama
        Junior ML Engineer
        Skills: Proficient in Python, Java, and SQL. Experienced in developing machine learning models and working in Agile environments. Strong problem-solving skills and effective communication for team collaboration.
        Projects: Developed an AI-powered Interview Simulation System using NLP and Python.
        """
        skills = extract_cv_skills_from_text(cv_text, esco_skills, embedder)
    else:
        skills = extract_cv_skills(pdf_path, esco_skills, embedder)
    
    # Save skills to JSON file
    output_path = "data/cv_skills.json"
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(skills, f, indent=2)
        logger.info(f"Saved extracted skills to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save skills to {output_path}: {e}")
    
    # Print skills for console output
    print(json.dumps(skills, indent=2))

if __name__ == "__main__":
    main()