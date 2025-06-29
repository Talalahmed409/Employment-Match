#!/usr/bin/env python3
"""
Generate embeddings for ESCO skills using sentence-transformers
"""

import json
import os
import sys
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
EMBEDDER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
ESCO_FILE_PATH = "data/esco_skills.json"
EMBEDDINGS_FILE_PATH = "data/esco_embeddings.npy"
BATCH_SIZE = 100

def load_esco_skills(file_path: str):
    """Load ESCO skills from JSON file."""
    if not os.path.exists(file_path):
        logger.error(f"ESCO file not found: {file_path}")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            skills = json.load(f)
            logger.info(f"Loaded {len(skills)} skills from {file_path}")
            return skills
    except Exception as e:
        logger.error(f"Failed to load ESCO skills: {e}")
        return []

def generate_embeddings():
    """Generate embeddings for ESCO skills."""
    try:
        # Load ESCO skills
        esco_skills = load_esco_skills(ESCO_FILE_PATH)
        if not esco_skills:
            logger.error("No ESCO skills loaded")
            return False
        
        # Load sentence transformer model
        logger.info(f"Loading sentence transformer model: {EMBEDDER_MODEL}")
        embedder = SentenceTransformer(EMBEDDER_MODEL)
        
        # Prepare texts for embedding
        texts = [skill["skill"] + ": " + skill["description"] for skill in esco_skills]
        logger.info(f"Generating embeddings for {len(texts)} skill descriptions")
        
        # Generate embeddings in batches
        embeddings = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            batch_embeddings = embedder.encode(batch)
            embeddings.append(batch_embeddings)
            logger.info(f"Processed batch {i//BATCH_SIZE + 1}/{(len(texts) + BATCH_SIZE - 1)//BATCH_SIZE}")
        
        # Combine all embeddings
        all_embeddings = np.vstack(embeddings)
        logger.info(f"Generated embeddings shape: {all_embeddings.shape}")
        
        # Save embeddings
        os.makedirs(os.path.dirname(EMBEDDINGS_FILE_PATH), exist_ok=True)
        np.save(EMBEDDINGS_FILE_PATH, all_embeddings)
        logger.info(f"Saved embeddings to {EMBEDDINGS_FILE_PATH}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return False

def main():
    """Main function."""
    logger.info("Starting embedding generation...")
    
    if generate_embeddings():
        logger.info("Embedding generation completed successfully")
    else:
        logger.error("Embedding generation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()