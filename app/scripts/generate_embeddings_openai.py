import json
import time
import logging
from pathlib import Path
from openai import OpenAI
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure OpenAI API
client = OpenAI(api_key=settings.OPENAI_API_KEY)

CHUNKS_PATH = Path("/Users/shekar/blend/hackathon/uploads/selling_guide_chunks.json")
OUTPUT_PATH = Path("/Users/shekar/blend/hackathon/uploads/selling_guide_chunks_with_openai_embeddings.json")

def truncate_to_bytes(text, limit=10000):
    return text.encode("utf-8")[:limit].decode("utf-8", errors="ignore")

def get_embedding(text: str):
    try:
        safe_text = truncate_to_bytes(text)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=safe_text
        )
        logging.info(f"Successfully generated embedding for text: {safe_text[:50]}...")
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"Embedding error: {e}")
        return None

def generate_embeddings(chunks_path, output_path):
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    for i, chunk in enumerate(chunks):
        text = chunk.get("content", "")
        embedding = get_embedding(text)
        chunk["embedding"] = embedding
        logging.info(f"[{i+1}/{len(chunks)}] Embedded chunk {chunk.get('id', i)}")
        time.sleep(0.2)  # OpenAI rate limit control

        # Save the updated chunks after each embedding generation
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        logging.info(f"Updated embeddings saved to {output_path}")

    logging.info(f"✅ All {len(chunks)} chunks with OpenAI embeddings saved to {output_path}")

if __name__ == "__main__":
    generate_embeddings(CHUNKS_PATH, OUTPUT_PATH) 