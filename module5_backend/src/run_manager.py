import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

class RunManager:
    def __init__(self, config_path: str = "backend/configs/config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        self.outputs_dir = Path(self.config.get("outputs_dir", "backend/outputs/runs"))
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def create_run(self, scene_id: str) -> str:
        """Generates a unique run_id and creates its output directory."""
        short_id = str(uuid.uuid4())[:8]
        run_id = f"run_{scene_id}_{short_id}"
        run_dir = self.outputs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_id

    def get_run_dir(self, run_id: str) -> Path:
        """Returns the directory path for a given run_id."""
        return self.outputs_dir / run_id

    def run_exists(self, run_id: str) -> bool:
        """Checks if a run directory exists."""
        return (self.outputs_dir / run_id).exists()

    def save_json(self, run_id: str, filename: str, data: Dict[str, Any]) -> str:
        """Saves a dictionary as a JSON file in the run directory."""
        run_dir = self.get_run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        file_path = run_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return str(file_path)

    def load_json(self, run_id: str, filename: str) -> Optional[Dict[str, Any]]:
        """Loads a JSON file from the run directory."""
        file_path = self.get_run_dir(run_id) / filename
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def is_scene_valid(self, scene_id: str) -> bool:
        """Validates if scene_id exists in config."""
        valid_scenes = [s["scene_id"] for s in self.config.get("demo_scenes", [])]
        return scene_id in valid_scenes

    def is_precomputed(self, scene_id: str) -> bool:
        """Checks if a scene is marked as precomputed in config."""
        for s in self.config.get("demo_scenes", []):
            if s["scene_id"] == scene_id:
                return s.get("precomputed", False)
        return False