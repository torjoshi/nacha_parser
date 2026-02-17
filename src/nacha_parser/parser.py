from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


class Parser:
    """Simple NACHA parser that uses YAML specs from `specs/yml` as a vector.

    The parser is intentionally lightweight: it loads all YAML files found in
    the provided `specs_dir` and exposes them as `vector`. Parsing a NACHA
    file/string returns a list of records with minimal mapping to the loaded
    schema (when available).
    """

    def __init__(self, specs_dir: Optional[str] = None):
        # Default to project_root/specs/yml. project_root is three parents up
        if specs_dir:
            self.specs_dir = Path(specs_dir)
        else:
            project_root = Path(__file__).resolve().parents[3]
            self.specs_dir = project_root / "specs" / "yml"

        self.vector = self.load_vector()

    def load_vector(self) -> Dict[str, Any]:
        """Load all YAML files in `specs_dir` into a dictionary.

        Each YAML file is loaded under its stem (filename without suffix), e.g.
        `nacha_validation_schema.yml` -> `vector['nacha_validation_schema']`.
        """
        result: Dict[str, Any] = {}
        if not self.specs_dir.exists():
            return result

        for yml in sorted(self.specs_dir.glob("*.yml")):
            try:
                with open(yml, "r") as f:
                    result[yml.stem] = yaml.safe_load(f) or {}
            except Exception:
                # Keep loading other files even if one fails
                result[yml.stem] = {}

        return result

    def parse(self, source: str) -> Dict[str, Any]:
        """Parse NACHA content from a string or a file path.

        Returns a dict with `records` and the loaded `vector`.
        Each record contains `raw`, `line_no`, `record_type` and optionally
        `schema` when the loaded validation schema defines a matching
        record type.
        """
        content = None
        p = Path(source)
        if p.exists():
            content = p.read_text()
        else:
            content = source

        # Normalize line endings and split into lines
        normalized = content.replace("\r\n", "\n")
        normalized = normalized.replace("\r", "\n")
        lines = normalized.splitlines()

        records: List[Dict[str, Any]] = []
        schema = self.vector.get("nacha_validation_schema", {}) or {}
        if isinstance(schema, dict):
            record_types = schema.get("record_types", {})
        else:
            record_types = {}

        for idx, line in enumerate(lines):
            # Skip empty lines (avoid creating records for blank lines)
            if not line.strip():
                continue

            rt = line[0]
            rec: Dict[str, Any] = {
                "raw": line,
                "line_no": idx + 1,
                "record_type": rt,
            }

            # Attach any matching schema info (keys are strings)
            rec_schema = record_types.get(str(rt))
            if not rec_schema:
                rec_schema = record_types.get(rt)

            if rec_schema:
                rec["schema"] = rec_schema

            records.append(rec)

        return {"records": records, "vector": self.vector}

    def parse_file(self, filepath: str) -> Dict[str, Any]:
        return self.parse(filepath)
