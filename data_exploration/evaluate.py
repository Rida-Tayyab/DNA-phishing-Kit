import json
import random
from pathlib import Path
from tqdm import tqdm
from collections import defaultdict

from classifier import classify_kit


def evaluate_classification(sample_size=200):
    """Evaluate classification accuracy on random sample of kits."""
    
    with open("features.json") as f:
        features_data = json.load(f)
    
    with open("data_exploration/dataset_manifest.json") as f:
        manifest_data = json.load(f)
    
    manifest_lookup = {kit["hash"]: kit for kit in manifest_data}
    
    valid_kits = []
    for kit_hash, kit_features in features_data.items():
        if kit_hash in manifest_lookup:
            manifest_entry = manifest_lookup[kit_hash]
            kit_root = Path(manifest_entry["kit_root"])
            if kit_root.exists():
                valid_kits.append((kit_hash, kit_features, manifest_entry))
    
    sample_kits = random.sample(valid_kits, min(sample_size, len(valid_kits)))
    
    correct = 0
    total = 0
    results = []
    
    for kit_hash, kit_features, manifest_entry in tqdm(sample_kits, desc="Evaluating"):
        kit_root = Path(manifest_entry["kit_root"])
        actual_family = kit_features.get("kit_family", "unknown")
        
        try:
            result = classify_kit(kit_root, manifest_entry, exclude_hash=kit_hash)
            predicted_family = result["predicted_family"]
            confidence = result["confidence"]
            
            is_correct = (predicted_family == actual_family)
            if is_correct:
                correct += 1
            
            total += 1
            
            results.append({
                "kit_hash": kit_hash,
                "actual_family": actual_family,
                "predicted_family": predicted_family,
                "confidence": confidence,
                "correct": is_correct
            })
            
        except Exception as e:
            continue
    
    accuracy = (correct / total * 100) if total > 0 else 0
    
    print(f"── Evaluation Results ──")
    print(f"Total kits evaluated: {total}")
    print(f"Overall accuracy: {accuracy:.1f}%")
    
    # Family size analysis
    family_sizes = defaultdict(int)
    for v in features_data.values():
        family_sizes[v.get("kit_family", "unknown")] += 1
    
    large_family_correct = 0
    large_family_total = 0
    small_family_correct = 0
    small_family_total = 0
    
    for result in results:
        size = family_sizes[result["actual_family"]]
        if size >= 5:
            large_family_total += 1
            if result["correct"]:
                large_family_correct += 1
        else:
            small_family_total += 1
            if result["correct"]:
                small_family_correct += 1
    
    if large_family_total > 0:
        large_acc = large_family_correct / large_family_total * 100
        print(f"Families with 5+ kits: {large_acc:.1f}%")
    
    if small_family_total > 0:
        small_acc = small_family_correct / small_family_total * 100
        print(f"Families with <5 kits: {small_acc:.1f}%")
    
    # Confidence analysis
    high_conf = [r for r in results if r["confidence"] >= 0.8]
    if high_conf:
        high_acc = sum(r["correct"] for r in high_conf) / len(high_conf) * 100
        print(f"High confidence predictions: {high_acc:.1f}%")
    
    return results


if __name__ == "__main__":
    random.seed(42)
    results = evaluate_classification(200)