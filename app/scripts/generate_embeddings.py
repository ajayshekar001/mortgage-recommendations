import json
import time
from pathlib import Path
import google.generativeai as genai
from app.core.config import settings  # or set API key manually

# Configure Gemini API
genai.configure(api_key=settings.GOOGLE_API_KEY)

CHUNKS_PATH = Path("/Users/shekar/blend/hackathon/uploads/selling_guide_chunks.json")
OUTPUT_PATH = Path("/Users/shekar/blend/hackathon/uploads/selling_guide_chunks_with_embeddings.json")

# Configure Gemini
# EMBEDDING_MODEL = "models/embedding-gecko-001"

def truncate_to_bytes(text, limit=10000):
    return text.encode("utf-8")[:limit].decode("utf-8", errors="ignore")

def get_embedding(text: str):
    try:
        safe_text = truncate_to_bytes(text)
        response = genai.embedText(
            model="models/embedding-gecko-001",
            text=safe_text
        )
        # Try both possible response formats
        if hasattr(response, "embedding"):
            return response.embedding
        elif "embedding" in response:
            return response["embedding"]
        elif "embeddings" in response:
            return response["embeddings"][0]["values"]
        else:
            print(f"Unexpected embedding response format: {response}")
            return None
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

def generate_embeddings(chunks_path, output_path):
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    for i, chunk in enumerate(chunks):
        text = chunk.get("content", "")
        embedding = get_embedding(text)
        chunk["embedding"] = embedding
        print(f"[{i+1}/{len(chunks)}] Embedded chunk {chunk.get('id', i)}")
        time.sleep(0.2)  # Gemini rate limit control

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(chunks)} chunks with embeddings to {output_path}")

if __name__ == "__main__":
    generate_embeddings(CHUNKS_PATH, OUTPUT_PATH) 