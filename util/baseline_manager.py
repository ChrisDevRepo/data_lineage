
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

class BaselineManager:
    def __init__(self, data_path: str = "data/latest_frontend_lineage.json", baseline_path: str = "tests/baseline_snapshot.json"):
        self.data_path = Path(data_path)
        self.baseline_path = Path(baseline_path)
        self.critical_objects = [
            "spLoadHumanResourcesObjects",
            "spLoadHumanResourcesObjects" # Add other critical ones
        ]

    def load_current_data(self) -> List[Dict[str, Any]]:
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        with open(self.data_path, 'r') as f:
            return json.load(f)

    def generate_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Build ID lookup map
        id_map = {node.get("id"): node.get("name", "UNKNOWN") for node in data}

        metrics = {
            "total_objects": len(data),
            "parse_success_count": sum(1 for node in data if node.get("parse_success", False)),
            "object_details": {}
        }
        
        # Track metrics for ALL objects
        for node in data:
            name = node.get("name")
            if not name:
                continue
            
            # Extract inputs/outputs names for strict relation check
            # Inputs/Outputs are lists of IDs in frontend_lineage.json
            inputs = sorted([id_map.get(iid, f"UNKNOWN_ID:{iid}") for iid in node.get("inputs", [])])
            outputs = sorted([id_map.get(oid, f"UNKNOWN_ID:{oid}") for oid in node.get("outputs", [])])

            metrics["object_details"][name] = {
                "inputs_count": len(inputs),
                "outputs_count": len(outputs),
                "inputs": inputs,  # Store actual names
                "outputs": outputs, # Store actual names
                "parse_success": node.get("parse_success", False),
                "parse_error": node.get("parse_error"),
                "is_critical": name in self.critical_objects
            }
        
        return metrics

    def create_snapshot(self):
        data = self.load_current_data()
        metrics = self.generate_metrics(data)
        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.baseline_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"✅ Baseline snapshot created at {self.baseline_path}")
        print(f"   Total Objects: {metrics['total_objects']}")
        print(f"   Parse Success: {metrics['parse_success_count']}")

    def verify_against_snapshot(self) -> bool:
        if not self.baseline_path.exists():
            print(f"❌ Baseline file not found: {self.baseline_path}")
            return False
            
        with open(self.baseline_path, 'r') as f:
            baseline = json.load(f)
            
        current_data = self.load_current_data()
        current_metrics = self.generate_metrics(current_data)
        
        errors = []
        
        # 1. Total Count Check
        if current_metrics["total_objects"] != baseline["total_objects"]:
            errors.append(f"Total objects mismatch: Expected {baseline['total_objects']}, Found {current_metrics['total_objects']}")
            
        # 2. Critical Object Check
        for name, base_d in baseline["object_details"].items():
            curr_d = current_metrics["object_details"].get(name)
            if not curr_d:
                errors.append(f"Object {name} missing in current data")
                continue
                
            if curr_d["inputs_count"] != base_d["inputs_count"]:
                errors.append(f"{name} inputs count mismatch: Expected {base_d['inputs_count']}, Found {curr_d['inputs_count']}")
            elif curr_d["inputs"] != base_d["inputs"]:
                 errors.append(f"{name} inputs content mismatch: Expected {base_d['inputs']}, Found {curr_d['inputs']}")
                
            if curr_d["outputs_count"] != base_d["outputs_count"]:
                errors.append(f"{name} outputs count mismatch: Expected {base_d['outputs_count']}, Found {curr_d['outputs_count']}")
            elif curr_d["outputs"] != base_d["outputs"]:
                 errors.append(f"{name} outputs content mismatch: Expected {base_d['outputs']}, Found {curr_d['outputs']}")
        
        if errors:
            print("❌ Baseline Verification FAILED:")
            for e in errors:
                print(f"   - {e}")
            return False
        else:
            print("✅ Baseline Verification PASSED")
            return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["create", "verify"])
    args = parser.parse_args()
    
    manager = BaselineManager()
    if args.action == "create":
        manager.create_snapshot()
    else:
        success = manager.verify_against_snapshot()
        sys.exit(0 if success else 1)
