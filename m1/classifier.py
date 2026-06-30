import json
import numpy as np
import faiss
from pathlib import Path
from collections import Counter

from embedders.embedder import build_feature_vector, normalize_vector
from embedders.text_embedder import embed_kit_source

# Load index and metadata at module level
index = faiss.read_index("kit_index.faiss")

with open("index_metadata.json") as f:
    metadata = json.load(f)

with open("data/features.json") as f:
    features_data = json.load(f)

with open("data/normalization_stats.json") as f:
    norm_stats = json.load(f)

kit_lookup = {item["index_id"]: item for item in metadata["kit_metadata"]}
col_min = norm_stats["col_min"] 
col_max = norm_stats["col_max"]


def classify_kit(kit_root: Path, kit_manifest_entry: dict, exclude_hash: str = None) -> dict:
    """
    Classify a phishing kit by finding similar kits in the FAISS index.
    
    Args:
        kit_root: Path to kit directory
        kit_manifest_entry: Kit metadata from manifest (contains kit hash)
        exclude_hash: Hash to exclude from results (usually the kit itself)
        
    Returns:
        Dict with predicted_family, confidence, and top_5_neighbours
    """
    
    kit_hash = kit_manifest_entry["hash"]
    
    if kit_hash not in features_data:
        raise ValueError(f"Kit hash {kit_hash} not found in features.json")
    
    kit_features = features_data[kit_hash]
    
    # Build raw structured vector, then normalize using saved stats
    raw_structured_vec = build_feature_vector(kit_features)
    structured_vec = normalize_vector(raw_structured_vec, col_min, col_max)
    text_vec = embed_kit_source(kit_root, kit_manifest_entry)
    
    hybrid_vec = np.concatenate([structured_vec, text_vec])
    
    query_vec = np.array([hybrid_vec], dtype=np.float32)
    faiss.normalize_L2(query_vec)
    
    k_search = 10 if exclude_hash else 5
    distances, indices = index.search(query_vec, k_search)
    
    all_neighbors = []
    
    for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
        if idx in kit_lookup:
            neighbor_hash = kit_lookup[idx].get("kit_hash")
            family = kit_lookup[idx]["kit_family"]
            
            if exclude_hash and neighbor_hash == exclude_hash:
                continue
                
            all_neighbors.append((family, float(dist), neighbor_hash))
        else:
            all_neighbors.append(("unknown", float(dist), "unknown"))
    
    top_5_neighbours = all_neighbors[:5]
    neighbor_families = [family for family, _, _ in top_5_neighbours]
    
    if neighbor_families:
        family_counts = Counter(neighbor_families)
        predicted_family = family_counts.most_common(1)[0][0]
        confidence = family_counts[predicted_family] / len(neighbor_families)
    else:
        predicted_family = "unknown"
        confidence = 0.0
    
    return {
        "predicted_family": predicted_family,
        "confidence": confidence,
        "top_5_neighbours": [(family, dist) for family, dist, _ in top_5_neighbours]
    }