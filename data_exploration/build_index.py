import json
import numpy as np
import faiss
from pathlib import Path
from tqdm import tqdm


from embedders.embedder import build_feature_vector
from embedders.text_embedder import embed_kit_source


def build_hybrid_index():
    
    with open("data_exploration/data/features.json") as f:
        features_data = json.load(f)
    
    with open("data_exploration/data/dataset_manifest.json") as f:
        manifest_data = json.load(f)
    
    manifest_lookup = {kit["hash"]: kit for kit in manifest_data}
    
    print(f"Loaded {len(features_data)} feature sets")
    print(f"Loaded {len(manifest_lookup)} manifest entries")
    
    #Initialize FAISS index
    dimension = 439 
    index = faiss.IndexFlatL2(dimension)
    
    # Metadata storage
    kit_metadata = []
    processed_count = 0
    skipped_count = 0
    
    #Process kits in batches
    kit_items = list(features_data.items())
    batch_size = 500
    
    for batch_start in tqdm(range(0, len(kit_items), batch_size), desc="Processing batches"):
        batch_end = min(batch_start + batch_size, len(kit_items))
        batch_items = kit_items[batch_start:batch_end]
        
        batch_vectors = []
        batch_metadata = []
        
        for kit_hash, kit_data in batch_items:

            if kit_hash not in manifest_lookup:
                skipped_count += 1
                continue
                
            manifest_kit = manifest_lookup[kit_hash]
            kit_root = Path(manifest_kit["kit_root"])
            

            if not kit_root.exists():
                skipped_count += 1
                continue
            
            try:
                
                structured_vec = build_feature_vector(kit_data)
                
        
                text_vec = embed_kit_source(kit_root, kit_data)
                
                
                hybrid_vec = np.concatenate([structured_vec, text_vec])
                
                batch_vectors.append(hybrid_vec)
                batch_metadata.append({
                    "kit_hash": kit_hash,
                    "kit_family": kit_data.get("kit_family", "unknown"),
                    "index_id": processed_count
                })
                
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing kit {kit_hash}: {e}")
                skipped_count += 1
                continue
        
        if batch_vectors:
            batch_array = np.array(batch_vectors, dtype=np.float32)
            
            faiss.normalize_L2(batch_array)
            
            index.add(batch_array)
            
            kit_metadata.extend(batch_metadata)
        
        print(f"Batch {batch_start//batch_size + 1}: processed {len(batch_vectors)} kits")
    
    print("Saving FAISS index and metadata...")
    
    faiss.write_index(index, "kit_index.faiss")
    
    metadata = {
        "total_vectors": index.ntotal,
        "dimension": dimension,
        "processed_kits": processed_count,
        "skipped_kits": skipped_count,
        "kit_metadata": kit_metadata
    }
    
    with open("index_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print("\n── Index Building Summary ──")
    print(f"Total kits processed: {processed_count}")
    print(f"Kits skipped: {skipped_count}")
    print(f"Index dimension: {dimension}")
    print(f"Index size: {index.ntotal} vectors")
    print(f"Saved to: kit_index.faiss")
    print(f"Metadata: index_metadata.json")


if __name__ == "__main__":
    build_hybrid_index()