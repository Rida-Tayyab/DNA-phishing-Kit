import json
from collections import Counter, defaultdict
import statistics


def load_features():
    """Load features from features.json or checkpoint."""
    try:
        with open("features.json") as f:
            return json.load(f)
    except FileNotFoundError:
        with open("features_checkpoint.json") as f:
            return json.load(f)


def exfiltration_methods():
    features = load_features()
    
    methods = [kit.get("exfil_method", "unknown") for kit in features.values()]
    counts = Counter(methods)
    total = len(methods)
    
    print("Exfiltration Method Distribution")
    for method, count in counts.most_common():
        pct = (count / total) * 100
        print(f"{method:10s}: {count:4d} kits ({pct:5.1f}%)")
    print(f"Total: {total} kits\n")


def sophistication_scores():
    features = load_features()
    
    scores = [kit.get("sophistication_score", 0) for kit in features.values()]
    
    print("Sophistication Score Distribution")
    print(f"Min:  {min(scores)}")
    print(f"Max:  {max(scores)}")
    print(f"Mean: {statistics.mean(scores):.1f}")
    print(f"Median: {statistics.median(scores):.1f}")
    
    # Find top families by average sophistication
    family_scores = defaultdict(list)
    for kit in features.values():
        family = kit.get("kit_family", "unknown")
        score = kit.get("sophistication_score", 0)
        family_scores[family].append(score)
    
    # Calculate averages and find top 10
    family_averages = {
        family: statistics.mean(scores) 
        for family, scores in family_scores.items()
        if len(scores) >= 3 
    }
    
    top_families = sorted(family_averages.items(), key=lambda x: x[1], reverse=True)[:10]
    
    print("\nTop 10 Most Sophisticated Families (avg score, min 3 kits):")
    for family, avg_score in top_families:
        kit_count = len(family_scores[family])
        print(f"{family:20s}: {avg_score:4.1f} ({kit_count} kits)")
    print()


def brand_distribution():

    features = load_features()
    
    brands = [kit.get("detected_brand", "unknown") for kit in features.values()]
    counts = Counter(brands)
    total = len(brands)
    
    print("Brand Distribution (Top 10)")
    for brand, count in counts.most_common(10):
        pct = (count / total) * 100
        print(f"{brand:15s}: {count:4d} kits ({pct:5.1f}%)")
    print()


def family_consistency():
    features = load_features()
    
    family_53_kits = [kit for kit in features.values() if kit.get("kit_family") == "53"]
    
    if not family_53_kits:
        print("── Question 4: Family '53' not found\n")
        return
    
    print(f"── Question 4: Family '53' Consistency ({len(family_53_kits)} kits) ──")
    
    # Key features to analyze
    key_features = [
        "sophistication_score",
        "form_count", 
        "password_field_count",
        "external_script_count",
        "php_file_count"
    ]
    
    for feature in key_features:
        values = [kit.get(feature, 0) for kit in family_53_kits]
        if values:
            avg = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            min_val = min(values)
            max_val = max(values)
            print(f"{feature:20s}: avg={avg:5.1f}, std={std_dev:4.1f}, range=[{min_val}-{max_val}]")
    print()


def feature_variance():
    features = load_features()
    
    # Numeric features to analyze
    numeric_features = [
        "sophistication_score", "form_count", "password_field_count", 
        "external_script_count", "php_file_count", "js_file_count",
        "credential_type_count", "brand_confidence", "max_directory_depth"
    ]
    
    feature_variances = []
    
    for feature in numeric_features:
        values = [kit.get(feature, 0) for kit in features.values()]
        if len(values) > 1:
            variance = statistics.variance(values)
            feature_variances.append((feature, variance))
    
    # Sort by variance (high to low)
    feature_variances.sort(key=lambda x: x[1], reverse=True)
    
    print("Most Distinctive Features (by variance)")
    print("High variance = good for classification, Low variance = less useful")
    for feature, variance in feature_variances[:10]:
        print(f"{feature:25s}: {variance:8.1f}")
    print()


if __name__ == "__main__":
    exfiltration_methods()
    sophistication_scores()
    brand_distribution()
    family_consistency()
    feature_variance()