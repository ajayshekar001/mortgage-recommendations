import json
import re
from pathlib import Path

CHUNKS_PATH = Path("/Users/shekar/blend/hackathon/uploads/selling_guide_chunks.json")
OUTPUT_PATH = Path("/Users/shekar/blend/hackathon/uploads/selling_guide_relationships.json")

# Regex for guideline/section references (e.g., B3-5.3-01, Section B2-1.2-01)
REFERENCE_PATTERN = re.compile(r"(B\d+-\d+(?:\.\d+)*-\d+|Section B\d+-\d+(?:\.\d+)*-\d+)", re.IGNORECASE)


def extract_relationships(chunks_path, output_path):
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    
    relationships = []
    id_set = {chunk["id"].split("_p")[0] for chunk in chunks}  # Set of all possible target IDs
    
    for chunk in chunks:
        source_id = chunk["id"]
        content = chunk["content"]
        # Find all references in the content
        for match in REFERENCE_PATTERN.finditer(content):
            ref = match.group(1)
            # Normalize reference to match chunk IDs (strip 'Section ' if present)
            target_id = ref.replace("Section ", "").strip()
            if target_id in id_set:
                relationships.append({
                    "source_id": source_id,
                    "target_id": target_id,
                    "relationship_type": "refers_to",
                    "context": content[max(0, match.start()-40):match.end()+40]  # 40 chars before/after
                })
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(relationships, f, indent=2, ensure_ascii=False)
    print(f"Extracted {len(relationships)} relationships. Saved to {output_path}")

if __name__ == "__main__":
    extract_relationships(CHUNKS_PATH, OUTPUT_PATH) 