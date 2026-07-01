#!/usr/bin/env python3
"""
Generate 2D UMAP coordinates for the threat landscape visualization.
This creates a beautiful scatter plot showing the relationships between all 6,831 phishing kits.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from umap import UMAP
from tqdm import tqdm

def load_kit_data():
    """Load all kit data including features and metadata"""
    print("📊 Loading kit data...")
    
    # Load features
    with open("data/features.json") as f:
        features_data = json.load(f)
    
    # Load metadata 
    with open("data/dataset_manifest.json") as f:
        manifest_data = json.load(f)
    
    # Create kit lookup by hash
    kit_lookup = {kit["hash"]: kit for kit in manifest_data}
    
    return features_data, kit_lookup

def build_feature_matrix(features_data):
    """Build standardized feature matrix from all kits"""
    print("🔧 Building feature matrix...")
    
    # Import the feature builder
    from embedders.embedder import build_feature_vector
    
    kit_hashes = list(features_data.keys())
    feature_vectors = []
    
    for kit_hash in tqdm(kit_hashes, desc="Building vectors"):
        try:
            kit_features = features_data[kit_hash]
            vector = build_feature_vector(kit_features)
            feature_vectors.append(vector)
        except Exception as e:
            print(f"Skipping {kit_hash}: {e}")
            kit_hashes.remove(kit_hash)
    
    # Convert to numpy array and standardize
    X = np.array(feature_vectors)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, kit_hashes, scaler

def generate_umap_coordinates(X_scaled):
    """Generate 2D UMAP coordinates for visualization"""
    print("🗺️  Generating UMAP coordinates...")
    
    # UMAP parameters optimized for visualization
    umap_model = UMAP(
        n_components=2,
        n_neighbors=15,
        min_dist=0.1,
        metric='cosine',
        random_state=42,
        verbose=True
    )
    
    coordinates_2d = umap_model.fit_transform(X_scaled)
    
    return coordinates_2d, umap_model

def create_threat_map_data(coordinates_2d, kit_hashes, kit_lookup, features_data):
    """Create the final dataset for the threat landscape map"""
    print("📍 Creating threat map dataset...")
    
    threat_map_data = []
    family_stats = {}
    
    for i, kit_hash in enumerate(kit_hashes):
        kit_info = kit_lookup.get(kit_hash, {})
        kit_features = features_data.get(kit_hash, {})
        
        family = kit_info.get("family", "unknown")
        
        # Count kits per family
        if family not in family_stats:
            family_stats[family] = 0
        family_stats[family] += 1
        
        threat_map_data.append({
            "hash": kit_hash,
            "family": family,
            "x": float(coordinates_2d[i, 0]),
            "y": float(coordinates_2d[i, 1]),
            "total_files": kit_info.get("total_files", 0),
            "useful_files": kit_info.get("useful_files", 0),
            "php_count": kit_info.get("php_count", 0),
            "detected_brand": kit_features.get("detected_brand", "unknown"),
            "sophistication_score": kit_features.get("sophistication_score", 0),
            "uses_telegram": kit_features.get("uses_telegram", False),
            "steals_card": kit_features.get("steals_card", False),
            "has_bot_detection": kit_features.get("has_bot_detection", False)
        })
    
    return threat_map_data, family_stats

def save_threat_map_data(threat_map_data, family_stats):
    """Save the threat map data for the frontend"""
    print("💾 Saving threat map data...")
    
    # Create frontend data directory
    frontend_data_dir = Path("frontend/phishing-classifier/src/data")
    frontend_data_dir.mkdir(exist_ok=True)
    
    # Save main dataset
    with open(frontend_data_dir / "threat_map.json", "w") as f:
        json.dump(threat_map_data, f, indent=2)
    
    # Save family statistics
    family_list = [
        {"name": family, "count": count} 
        for family, count in sorted(family_stats.items(), key=lambda x: x[1], reverse=True)
    ]
    
    with open(frontend_data_dir / "family_stats.json", "w") as f:
        json.dump({
            "total_kits": len(threat_map_data),
            "total_families": len(family_stats),
            "families": family_list
        }, f, indent=2)
    
    # Create color palette for top families
    top_families = family_list[:20]  # Top 20 families
    colors = [
        "#ff6b6b", "#4ecdc4", "#45b7d1", "#f9ca24", "#6c5ce7",
        "#fd79a8", "#fdcb6e", "#55a3ff", "#fd79a8", "#00b894",
        "#e17055", "#a29bfe", "#ffeaa7", "#fab1a0", "#00cec9",
        "#e84393", "#ff7675", "#74b9ff", "#81ecec", "#a29bfe"
    ]
    
    color_mapping = {}
    for i, family_info in enumerate(top_families):
        color_mapping[family_info["name"]] = colors[i % len(colors)]
    
    # Default color for smaller families
    color_mapping["other"] = "#95a5a6"
    
    with open(frontend_data_dir / "family_colors.json", "w") as f:
        json.dump(color_mapping, f, indent=2)
    
    return frontend_data_dir

def main():
    """Main execution function"""
    print("🚀 Generating Threat Landscape Map")
    print("=" * 50)
    
    # Load data
    features_data, kit_lookup = load_kit_data()
    
    # Build feature matrix
    X_scaled, kit_hashes, scaler = build_feature_matrix(features_data)
    
    # Generate UMAP coordinates
    coordinates_2d, umap_model = generate_umap_coordinates(X_scaled)
    
    # Create threat map dataset
    threat_map_data, family_stats = create_threat_map_data(
        coordinates_2d, kit_hashes, kit_lookup, features_data
    )
    
    # Save for frontend
    frontend_data_dir = save_threat_map_data(threat_map_data, family_stats)
    
    print("\n" + "=" * 50)
    print("✅ Threat landscape map generated successfully!")
    print(f"📊 Total kits: {len(threat_map_data)}")
    print(f"🏷️  Total families: {len(family_stats)}")
    print(f"💾 Data saved to: {frontend_data_dir}")
    print("\n🎯 Top 10 families:")
    
    for family_info in sorted(family_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        family, count = family_info
        percentage = (count / len(threat_map_data)) * 100
        print(f"   {family}: {count} kits ({percentage:.1f}%)")
    
    print(f"\n📁 Files created:")
    print(f"   • threat_map.json ({len(threat_map_data)} data points)")
    print(f"   • family_stats.json (family statistics)")
    print(f"   • family_colors.json (color palette)")

if __name__ == "__main__":
    main()