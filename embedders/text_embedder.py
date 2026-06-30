import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')


def embed_kit_source(kit_root: Path, kit_data: dict) -> np.ndarray:
    """
    Embed the source code of a phishing kit using semantic text embedding.
    
    Args:
        kit_root: Path to kit directory
        kit_data: Kit metadata dictionary
        
    Returns:
        384-dimensional numpy array from SentenceTransformer
    """
    
    all_files = kit_data.get("files", [])
    source_files = [
        f for f in all_files 
        if f.lower().endswith((".php", ".js"))
    ]
    
    source_content = []
    
    for rel_path in source_files[:10]:
        file_path = kit_root / rel_path
        
        if not file_path.exists():
            continue
            
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if len(content.strip()) > 20:
                source_content.append(content)
        except Exception:
            continue
    
    combined_source = "\n".join(source_content)
    truncated_source = combined_source[:512]
    
    if not truncated_source.strip():
        truncated_source = "empty_kit"
    
    embedding = model.encode(truncated_source)
    return embedding