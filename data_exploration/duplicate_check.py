import json
import numpy as np
import faiss
from collections import defaultdict


def check_real_duplicates(threshold=0.01):
    """
    Check for true duplicate kits by finding nearest neighbor distances.
    
    Args:
        threshold: Distance threshold below which kits are considered duplicates
        
    Returns:
        Dict with duplicate statistics and analysis
    """
    
    # Load FAISS index
    print("Loading FAISS index...")
    index = faiss.read_index("kit_index.faiss")
    
    # Load metadata for analysis
    with open("index_metadata.json") as f:
        metadata = json.load(f)
    
    kit_lookup = {item["index_id"]: item for item in metadata["kit_metadata"]}
    
    print(f"Analyzing {index.ntotal} vectors...")
    
    # Reconstruct all vectors from FAISS index
    all_vectors = index.reconstruct_n(0, index.ntotal)
    
    print("Searching for nearest neighbors...")
    # Search for top-2 neighbors for each vector (self + nearest other)
    distances, indices = index.search(all_vectors, 2)
    
    # Analyze nearest neighbor distances (2nd neighbor = nearest other kit)
    duplicate_count = 0
    unique_count = 0
    duplicate_pairs = []
    family_duplicates = defaultdict(list)
    
    for i in range(len(distances)):
        # Distance to nearest other kit (excluding self)
        nearest_other_distance = distances[i][1]
        nearest_other_idx = indices[i][1]
        
        if nearest_other_distance < threshold:
            duplicate_count += 1
            
            # Get family information
            kit1_info = kit_lookup.get(i, {})
            kit2_info = kit_lookup.get(nearest_other_idx, {})
            
            family1 = kit1_info.get("kit_family", "unknown")
            family2 = kit2_info.get("kit_family", "unknown")
            
            duplicate_pairs.append({
                "kit1_idx": i,
                "kit2_idx": nearest_other_idx,
                "distance": float(nearest_other_distance),
                "family1": family1,
                "family2": family2,
                "same_family": family1 == family2
            })
            
            family_duplicates[family1].append(i)
            
        else:
            unique_count += 1
    
    # Calculate statistics
    total_kits = len(distances)
    duplicate_percentage = (duplicate_count / total_kits) * 100
    
    # Analyze cross-family vs within-family duplicates
    same_family_duplicates = sum(1 for pair in duplicate_pairs if pair["same_family"])
    cross_family_duplicates = len(duplicate_pairs) - same_family_duplicates
    
    # Count families with duplicates
    families_with_duplicates = len([f for f, kits in family_duplicates.items() if len(kits) > 1])
    
    print(f"\n── Duplicate Analysis Results ──")
    print(f"Total kits analyzed: {total_kits}")
    print(f"Kits with duplicates: {duplicate_count} ({duplicate_percentage:.1f}%)")
    print(f"Unique kits: {unique_count} ({100-duplicate_percentage:.1f}%)")
    print(f"Distance threshold: {threshold}")
    
    print(f"\n── Duplicate Breakdown ──")
    print(f"Same-family duplicates: {same_family_duplicates}")
    print(f"Cross-family duplicates: {cross_family_duplicates}")
    print(f"Families with internal duplicates: {families_with_duplicates}")
    
    # Show some example duplicates
    print(f"\n── Sample Duplicate Pairs ──")
    for i, pair in enumerate(duplicate_pairs[:5]):
        dist = pair["distance"]
        f1, f2 = pair["family1"], pair["family2"]
        same = "✓" if pair["same_family"] else "✗"
        print(f"{i+1}. {f1} ↔ {f2} (distance: {dist:.6f}) {same}")
    
    # Distance distribution
    distances_to_nearest = [distances[i][1] for i in range(len(distances))]
    
    print(f"\n── Distance Distribution ──")
    print(f"Min distance to nearest: {min(distances_to_nearest):.6f}")
    print(f"Max distance to nearest: {max(distances_to_nearest):.6f}")
    print(f"Mean distance to nearest: {np.mean(distances_to_nearest):.6f}")
    
    # Count by distance ranges
    zero_distance = sum(1 for d in distances_to_nearest if d < 0.001)
    very_close = sum(1 for d in distances_to_nearest if 0.001 <= d < 0.01)
    close = sum(1 for d in distances_to_nearest if 0.01 <= d < 0.1)
    
    print(f"Exact duplicates (d < 0.001): {zero_distance}")
    print(f"Very close (0.001 ≤ d < 0.01): {very_close}")  
    print(f"Close (0.01 ≤ d < 0.1): {close}")
    
    return {
        "total_kits": total_kits,
        "duplicate_count": duplicate_count,
        "unique_count": unique_count,
        "duplicate_percentage": duplicate_percentage,
        "same_family_duplicates": same_family_duplicates,
        "cross_family_duplicates": cross_family_duplicates,
        "families_with_duplicates": families_with_duplicates,
        "duplicate_pairs": duplicate_pairs,
        "distances_to_nearest": distances_to_nearest
    }


if __name__ == "__main__":
    results = check_real_duplicates(threshold=0.01)