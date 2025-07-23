import pdfplumber
import re
import json
from pathlib import Path

PDF_PATH = Path("/Users/shekar/blend/hackathon/uploads/Selling-Guide_06-4-2025_Highlighted.pdf")
OUTPUT_PATH = Path("/Users/shekar/blend/hackathon/uploads/selling_guide_chunks.json")

# Regex pattern for Fannie Mae guideline/section headers (e.g., B3-5.3-01, Section 2.1, etc.)
HEADER_PATTERN = re.compile(r"(B\d+-\d+(?:\.\d+)*-\d+|Section \d+(?:\.\d+)*)", re.IGNORECASE)

def parse_and_chunk_pdf(pdf_path, output_path):
    chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        current_chunk = None
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            lines = text.split("\n")
            for line in lines:
                header_match = HEADER_PATTERN.match(line.strip())
                if header_match:
                    # Start a new chunk
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = {
                        "id": f"{header_match.group(1)}_p{page_num}",
                        "title": header_match.group(1),
                        "content": line.strip(),
                        "page": page_num
                    }
                else:
                    if current_chunk:
                        current_chunk["content"] += "\n" + line.strip()
            # If no header found on page, treat the whole page as a chunk
            if not current_chunk and text.strip():
                current_chunk = {
                    "id": f"page_{page_num}",
                    "title": f"Page {page_num}",
                    "content": text.strip(),
                    "page": page_num
                }
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk)
    # Save chunks as JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"Extracted {len(chunks)} chunks. Saved to {output_path}")

if __name__ == "__main__":
    parse_and_chunk_pdf(PDF_PATH, OUTPUT_PATH) 