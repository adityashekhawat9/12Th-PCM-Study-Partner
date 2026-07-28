import json
import os
from pathlib import Path

import fitz  # PyMuPDF
import tiktoken
import faiss
import numpy as np
from fastembed import TextEmbedding
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

DATA_DIR = Path(__file__).parent
RAW_DIR = DATA_DIR / "raw"
INDEX_PATH = DATA_DIR / "index.faiss"
METADATA_PATH = DATA_DIR / "metadata.json"
MANIFEST_PATH = DATA_DIR / "manifest.json"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

print("Loading local ONNX embedding model (fastembed)...")
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

def get_embedding(text: str) -> list[float]:
    # fastembed returns a generator of numpy arrays
    return list(embedding_model.embed([text]))[0].tolist()

def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Chunk text by tokens."""
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    
    chunks = []
    i = 0
    while i < len(tokens):
        chunk_tokens = tokens[i:i + chunk_size]
        chunks.append(enc.decode(chunk_tokens))
        i += chunk_size - chunk_overlap
    return chunks

def extract_and_process_pdf(pdf_path: Path, book_info: dict) -> list[dict]:
    """Extract text from PDF, chunk it, and return metadata dictionaries."""
    print(f"Processing {pdf_path.name}...")
    doc = fitz.open(pdf_path)
    chunks_meta = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if not text.strip():
            continue
            
        page_chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        for i, chunk_text_content in enumerate(page_chunks):
            chunks_meta.append({
                "book": book_info["book"],
                "subject": book_info["subject"],
                "page": page_num + 1,
                "text": chunk_text_content.strip()
            })
            
    return chunks_meta

def main():
    RAW_DIR.mkdir(exist_ok=True)
    
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
        
    all_metadata = []
    all_embeddings = []
    
    for book in manifest["books"]:
        filename = book["suggested_filename"]
        base_name = filename.replace(".pdf", "")
        
        pdf_file = RAW_DIR / filename
        pdf_dir = RAW_DIR / base_name
        
        pdf_paths = []
        if pdf_dir.is_dir():
            pdf_paths = sorted(pdf_dir.glob("*.pdf"))
        elif pdf_file.exists():
            pdf_paths = [pdf_file]
            
        if not pdf_paths:
            print(f"Warning: Neither file '{filename}' nor folder '{base_name}/' found in {RAW_DIR}.")
            continue
            
        for path in pdf_paths:
            chunks = extract_and_process_pdf(path, book)
            
            for idx, chunk in enumerate(chunks):
                if idx % 100 == 0:
                    print(f"Embedding chunk {idx}/{len(chunks)} for {path.name}...")
                emb = get_embedding(chunk["text"])
                all_embeddings.append(emb)
                all_metadata.append(chunk)

    if not all_embeddings:
        print("No embeddings generated. Ensure PDFs are present in data/raw/")
        return

    # Build FAISS index
    print("Building FAISS index...")
    dimension = len(all_embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    
    # Convert list of lists to numpy array
    emb_array = np.array(all_embeddings, dtype=np.float32)
    index.add(emb_array)
    
    # Save index
    faiss.write_index(index, str(INDEX_PATH))
    print(f"Saved index to {INDEX_PATH} with {index.ntotal} vectors.")
    
    # Save metadata
    with open(METADATA_PATH, "w") as f:
        json.dump(all_metadata, f, indent=2)
    print(f"Saved metadata to {METADATA_PATH}.")

if __name__ == "__main__":
    main()
