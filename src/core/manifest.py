import json
from pathlib import Path

def load_manifest(manifest_path: str = "data/jobs/.manifest.json") -> dict:
    path = Path(manifest_path)
    if not path.exists():
        return {}

    return json.loads(path.read_text(encoding="utf-8"))

def save_manifest(manifest: dict, manifest_path: str = "data/jobs/.manifest.json"):
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")