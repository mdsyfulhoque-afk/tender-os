import re
from pathlib import Path
from app.config import DATA_DIR, MAX_CHUNK_TOKENS, atomic_write_json

PATTERNS = {
    "eligibility": r"(eligibility|qualification|experience|turnover|যোগ্যতা|অভিজ্ঞতা)",
    "technical": r"(technical specification|scope of work|কারিগরি বিবরণী)",
    "financial": r"(liquid assets|credit facility|solvency|আর্থিক সক্ষমতা)",
    "forms": r"(standard form|submission form|tender submission letter|ফরম)"
}

def chunk_text(text: str, max_tokens: int = MAX_CHUNK_TOKENS) -> list[str]:
    # Word-boundary chunking (approx 1.3 words per token)
    words = text.split()
    chunks = []
    current_chunk = []
    max_words = int(max_tokens * 1.3)
    
    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= max_words:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def process_chunks(pages: list[dict], tender_id: str) -> list[dict]:
    chunks = []
    current_category = "general"
    current_text = ""
    current_pages = []
    
    for p in pages:
        text = p["text"]
        matched_cat = None
        
        for cat, pattern in PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                matched_cat = cat
                break
                
        if matched_cat and matched_cat != current_category:
            if current_text.strip():
                for sc in chunk_text(current_text):
                    chunks.append({"category": current_category, "text": sc, "pages": current_pages})
            current_category = matched_cat
            current_text = text
            current_pages = [p["page"]]
        else:
            current_text += "\n" + text
            current_pages.append(p["page"])
            
    if current_text.strip():
        for sc in chunk_text(current_text):
            chunks.append({"category": current_category, "text": sc, "pages": current_pages})
            
    out_path = DATA_DIR / tender_id / "normalized_chunks.json"
    atomic_write_json(out_path, chunks)
    return chunks