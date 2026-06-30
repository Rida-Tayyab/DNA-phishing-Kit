from pathlib import PurePath
import json


def extract_structural_features(kit: dict) -> dict:
    total_files = max(kit.get("total_files", 0), 1)

    files = kit.get("files", [])

    php_ratio = kit.get("php_count", 0) / total_files
    js_ratio = kit.get("js_count", 0) / total_files

    html_pages = sum(
        1 for f in files
        if f.lower().endswith((".html", ".htm", ".php"))
    )

    is_multipage = html_pages > 1

    has_admin_panel = any(
        name.lower() in {
            "admin.php",
            "admin.html",
            "admin.htm",
            "administrator.php",
            "panel.php",
            "dashboard.php",
        }
        for name in (PurePath(f).name for f in files)
    )

    has_config_file = any(
        any(keyword in PurePath(f).name.lower() for keyword in [
            "config",
            "settings",
            "configuration",
            "conf",
        ])
        for f in files
    )

    max_directory_depth = 0

    for f in files:
        depth = len(PurePath(f).parts) - 1
        max_directory_depth = max(max_directory_depth, depth)

    return {
        "php_ratio": round(php_ratio, 3),
        "js_ratio": round(js_ratio, 3),

        "is_multipage": is_multipage,

        "has_admin_panel": has_admin_panel,
        "has_config_file": has_config_file,

        "max_directory_depth": max_directory_depth,

        "has_htaccess": kit.get("has_htaccess", False),
        "has_telegram": kit.get("has_telegram", False),
    }

with open("data/dataset_manifest.json") as f:
    manifest = json.load(f)

for kit in manifest[:5]:
    features = extract_structural_features(kit)
    print(f"Family: {kit['family']}")
    for k, v in features.items():
        print(f"  {k}: {v}")
    print()
