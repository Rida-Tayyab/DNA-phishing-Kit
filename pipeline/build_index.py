import json
import numpy as np
import faiss
from pathlib import Path
from tqdm import tqdm

from embedders.embedder import build_all_vectors
from embedders.text_embedder import embed_kit_source


def build_hybrid_index():
    """Build FAISS index with 439-dim hybrid fingerprints (55 structured + 384 text)."""
    
    # Step 1: Load data files
    print("Loading data files...")
    with open("data/features.json") as f:
        features_data = json.load(f)
    
    with open("data/dataset_manifest.json") as f:
        manifest_data = json.load(f)
    
    # Build hash → manifest lookup
    manifest_lookup = {kit["hash"]: kit for kit in manifest_data}
    
    print(f"Loaded {len(features_data)} feature sets")
    print(f"Loaded {len(manifest_lookup)} manifest entries")
    
    # Step 2: Build all structured vectors with normalization
    print("Building normalized structured vectors...")
    structured_vectors, vector_labels, vector_hashes, col_min, col_max = build_all_vectors("data_exploration/data/features.json")
    
    print(f"Built {len(structured_vectors)} normalized vectors")
    
    # Save normalization statistics
    norm_stats = {
        "col_min": col_min,
        "col_max": col_max
    }
    with open("data/normalization_stats.json", "w") as f:
        json.dump(norm_stats, f, indent=2)
    
    print("Normalization statistics saved to normalization_stats.json")
    
    # Initialize FAISS index
    dimension = 439  # 55 + 384
    index = faiss.IndexFlatL2(dimension)
    
    # Metadata storage
    kit_metadata = []
    processed_count = 0
    skipped_count = 0
    
    # Step 3: Process kits in batches using pre-computed structured vectors
    batch_size = 500
    
    for batch_start in tqdm(range(0, len(structured_vectors), batch_size), desc="Processing batches"):
        batch_end = min(batch_start + batch_size, len(structured_vectors))
        
        batch_vectors = []
        batch_metadata = []
        
        # Process each kit in batch
        for i in range(batch_start, batch_end):
            kit_hash = vector_hashes[i]
            kit_family = vector_labels[i]
            structured_vec = structured_vectors[i]
            
            # Get manifest data for text embedding
            if kit_hash not in manifest_lookup:
                skipped_count += 1
                continue
                
            manifest_kit = manifest_lookup[kit_hash]
            kit_root = Path(manifest_kit["kit_root"])
            
            # Skip if kit_root doesn't exist
            if not kit_root.exists():
                skipped_count += 1
                continue
            
            try:
                # Build 384-dim text embedding
                text_vec = embed_kit_source(kit_root, manifest_kit)
                
                # Concatenate to 439-dim hybrid fingerprint
                hybrid_vec = np.concatenate([structured_vec, text_vec])
                
                batch_vectors.append(hybrid_vec)
                batch_metadata.append({
                    "kit_hash": kit_hash,
                    "kit_family": kit_family,
                    "index_id": processed_count
                })
                
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing kit {kit_hash}: {e}")
                skipped_count += 1
                continue
        
        # Add batch to FAISS index
        if batch_vectors:
            batch_array = np.array(batch_vectors, dtype=np.float32)
            
            # L2 normalize for cosine similarity
            faiss.normalize_L2(batch_array)
            
            # Add to index
            index.add(batch_array)
            
            # Store metadata
            kit_metadata.extend(batch_metadata)
        
        print(f"Batch {batch_start//batch_size + 1}: processed {len(batch_vectors)} kits")
    
    # Step 4: Save artifacts
    print("Saving FAISS index and metadata...")
    
    # Save FAISS index
    faiss.write_index(index, "kit_index.faiss")
    
    # Save metadata
    metadata = {
        "total_vectors": index.ntotal,
        "dimension": dimension,
        "processed_kits": processed_count,
        "skipped_kits": skipped_count,
        "kit_metadata": kit_metadata
    }
    
    with open("index_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Print summary
    print("\n── Index Building Summary ──")
    print(f"Total kits processed: {processed_count}")
    print(f"Kits skipped: {skipped_count}")
    print(f"Index dimension: {dimension}")
    print(f"Index size: {index.ntotal} vectors")
    print(f"Saved to: kit_index.faiss")
    print(f"Metadata: index_metadata.json")
    print(f"Normalization stats: normalization_stats.json")


if __name__ == "__main__":
    build_hybrid_index()