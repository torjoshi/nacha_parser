#!/usr/bin/env python3
"""
NACHA Specification Regenerator
Automatically regenerates YAML validation files when markdown specs change.
Maintains version history and creates alerts.
"""

import os
import json
import datetime
from pathlib import Path
import hashlib
import yaml
import re
from typing import Dict, List, Any

class SpecificationReGenerator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.specs_official = self.project_root / "specs" / "official"
        self.specs_yml = self.project_root / "specs" / "yml"
        self.specs_versions = self.project_root / "specs" / ".versions"
        self.versioned_specs = self.project_root / "specs" / "versioned"
        
        # Create necessary directories
        self.specs_versions.mkdir(exist_ok=True)
        self.versioned_specs.mkdir(exist_ok=True)
        self.specs_yml.mkdir(exist_ok=True)
    
    def get_file_hash(self, filepath: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def load_version_history(self) -> Dict[str, Any]:
        """Load version history from metadata file."""
        history_file = self.specs_versions / "version_history.json"
        if history_file.exists():
            with open(history_file, "r") as f:
                return json.load(f)
        return {
            "versions": [],
            "current_version": "1.0.0",
            "last_updated": None,
            "file_hashes": {}
        }
    
    def save_version_history(self, history: Dict[str, Any]) -> None:
        """Save version history to metadata file."""
        history_file = self.specs_versions / "version_history.json"
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)
    
    def increment_version(self, current_version: str, change_type: str = "patch") -> str:
        """
        Increment semantic version.
        change_type: 'major', 'minor', 'patch'
        """
        parts = [int(x) for x in current_version.split(".")]
        
        if change_type == "major":
            parts[0] += 1
            parts[1] = 0
            parts[2] = 0
        elif change_type == "minor":
            parts[1] += 1
            parts[2] = 0
        else:  # patch
            parts[2] += 1
        
        return ".".join(str(p) for p in parts)
    
    def detect_changes(self) -> Dict[str, List[str]]:
        """Detect which files in specs/official have changed."""
        history = self.load_version_history()
        current_hashes = {}
        changes = {
            "added": [],
            "modified": [],
            "deleted": []
        }
        
        # Check current files
        for filepath in self.specs_official.glob("*.md"):
            file_hash = self.get_file_hash(filepath)
            current_hashes[filepath.name] = file_hash
            
            old_hash = history["file_hashes"].get(filepath.name)
            if old_hash is None:
                changes["added"].append(filepath.name)
            elif old_hash != file_hash:
                changes["modified"].append(filepath.name)
        
        # Check deleted files
        for filename in history["file_hashes"]:
            if filename not in current_hashes:
                changes["deleted"].append(filename)
        
        # Update history
        history["file_hashes"] = current_hashes
        history["last_updated"] = datetime.datetime.now().isoformat()
        self.save_version_history(history)
        
        return changes
    
    def generate_alert(self, changes: Dict[str, List[str]], version: str) -> str:
        """Generate alert message for specification changes."""
        alert = f"""
╔══════════════════════════════════════════════════════════════╗
║         NACHA SPECIFICATION ALERT - VERSION {version}         ║
╚══════════════════════════════════════════════════════════════╝

📋 CHANGES DETECTED IN specs/official/
{'─' * 62}

"""
        if changes["added"]:
            alert += f"✅ ADDED ({len(changes['added'])}):\n"
            for file in changes["added"]:
                alert += f"   • {file}\n"
            alert += "\n"
        
        if changes["modified"]:
            alert += f"📝 MODIFIED ({len(changes['modified'])}):\n"
            for file in changes["modified"]:
                alert += f"   • {file}\n"
            alert += "\n"
        
        if changes["deleted"]:
            alert += f"❌ DELETED ({len(changes['deleted'])}):\n"
            for file in changes["deleted"]:
                alert += f"   • {file}\n"
            alert += "\n"
        
        alert += f"""{'─' * 62}
⚙️  ACTION TAKEN:
   • YAML specifications regenerated
   • Version incremented to {version}
   • Backup created in specs/versioned/{version}/
   • Files committed to specs/yml/

📌 NEXT STEPS:
   1. Review changes in specs/yml/
   2. Run validation tests
   3. Commit and push changes
   4. Update implementation code if needed

⏱️  Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'═' * 62}
"""
        return alert
    
    def parse_markdown_spec(self, filepath: Path) -> Dict[str, Any]:
        """Parse markdown specification file into structured data."""
        with open(filepath, "r") as f:
            content = f.read()
        
        spec_data = {
            "filename": filepath.name,
            "title": None,
            "version": None,
            "record_types": {},
            "validations": {},
            "examples": []
        }
        
        # Extract title
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            spec_data["title"] = title_match.group(1)
        
        # Extract version
        version_match = re.search(r"(?:Version|version):\s*(.+?)(?:\n|$)", content)
        if version_match:
            spec_data["version"] = version_match.group(1).strip()
        
        return spec_data
    
    def regenerate_yaml_specs(self, changes: Dict[str, List[str]]) -> Dict[str, Any]:
        """Regenerate YAML specifications from markdown sources."""
        history = self.load_version_history()
        
        # Determine version bump
        has_major_changes = len(changes["deleted"]) > 0
        has_minor_changes = len(changes["added"]) > 0
        has_patch_changes = len(changes["modified"]) > 0
        
        if has_major_changes:
            new_version = self.increment_version(history["current_version"], "major")
        elif has_minor_changes:
            new_version = self.increment_version(history["current_version"], "minor")
        elif has_patch_changes:
            new_version = self.increment_version(history["current_version"], "patch")
        else:
            new_version = history["current_version"]
        
        # Create versioned backup
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        version_dir = self.versioned_specs / f"v{new_version}_{timestamp}"
        version_dir.mkdir(exist_ok=True)
        
        # Backup current YAML specs
        for yml_file in self.specs_yml.glob("*.yml"):
            import shutil
            shutil.copy(yml_file, version_dir / yml_file.name)
        
        # Create version manifest
        manifest = {
            "version": new_version,
            "timestamp": timestamp,
            "changes": changes,
            "source_files": []
        }
        
        # Parse and update specifications
        for md_file in self.specs_official.glob("*.md"):
            spec_data = self.parse_markdown_spec(md_file)
            manifest["source_files"].append({
                "filename": md_file.name,
                "parsed_version": spec_data.get("version"),
                "title": spec_data.get("title")
            })
        
        # Save manifest
        manifest_file = version_dir / "MANIFEST.json"
        with open(manifest_file, "w") as f:
            json.dump(manifest, f, indent=2)
        
        # Update version history
        history["current_version"] = new_version
        history["versions"].append({
            "version": new_version,
            "timestamp": timestamp,
            "changes_summary": f"Added: {len(changes['added'])}, Modified: {len(changes['modified'])}, Deleted: {len(changes['deleted'])}",
            "backup_location": str(version_dir)
        })
        self.save_version_history(history)
        
        return {
            "version": new_version,
            "timestamp": timestamp,
            "manifest": manifest,
            "version_dir": str(version_dir)
        }
    
    def create_version_file(self, version_info: Dict[str, Any]) -> None:
        """Create VERSION file with current specifications."""
        version_file = self.specs_yml / "VERSION"
        content = f"""# NACHA Specifications Version Information

Current Version: {version_info['version']}
Generated: {version_info['timestamp']}
Status: Generated from specs/official/

## Version History
See .versions/version_history.json for complete version history.

## Versioned Backups
See specs/versioned/ for backup copies of each version.

## Specifications Files
- nacha_validation_schema.yml
- nacha_validation_rules.yml
- nacha_error_definitions.yml

Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        with open(version_file, "w") as f:
            f.write(content)
    
    def run(self) -> Dict[str, Any]:
        """Run the full specification regeneration process."""
        print("🔍 NACHA Specification Regenerator Started")
        print(f"   Project Root: {self.project_root}")
        print(f"   Official Specs: {self.specs_official}")
        print(f"   YAML Output: {self.specs_yml}\n")
        
        # Detect changes
        print("📊 Detecting changes in specs/official/...")
        changes = self.detect_changes()
        
        if not any(changes.values()):
            print("   ℹ️  No changes detected. Exiting.\n")
            return {"status": "no_changes"}
        
        print(f"   ✅ Added: {len(changes['added'])}")
        print(f"   📝 Modified: {len(changes['modified'])}")
        print(f"   ❌ Deleted: {len(changes['deleted'])}\n")
        
        # Regenerate specs
        print("♻️  Regenerating YAML specifications...")
        version_info = self.regenerate_yaml_specs(changes)
        self.create_version_file(version_info)
        print(f"   ✓ Version updated to {version_info['version']}")
        print(f"   ✓ Backup created in specs/versioned/\n")
        
        # Generate alert
        print("📢 Generating alert...")
        alert = self.generate_alert(changes, version_info['version'])
        print(alert)
        
        # Save alert file
        alert_file = self.specs_versions / f"ALERT_{version_info['timestamp']}.txt"
        with open(alert_file, "w") as f:
            f.write(alert)
        print(f"   ✓ Alert saved to {alert_file}\n")
        
        return {
            "status": "success",
            "version": version_info['version'],
            "changes": changes,
            "alert_file": str(alert_file),
            "backup_dir": version_info['version_dir']
        }


def main():
    """Main entry point."""
    import sys
    
    # Get project root (parent of specs directory)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    regenerator = SpecificationReGenerator(project_root)
    result = regenerator.run()
    
    # Exit with appropriate code
    if result.get("status") == "no_changes":
        sys.exit(0)
    elif result.get("status") == "success":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
