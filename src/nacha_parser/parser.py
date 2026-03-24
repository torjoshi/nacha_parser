from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


class Parser:
    """Simple NACHA parser that uses YAML specs from `specs/yml` as a vector.

    The parser is intentionally lightweight: it loads all YAML files found in
    the provided `specs_dir` and exposes them as `vector`. Parsing a NACHA
    file/string returns a list of records with minimal mapping to the loaded
    schema (when available).

    Call ``validate()`` to enforce field positional integrity against the schema.
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

    def validate(self, source: str) -> Dict[str, Any]:
        """Parse ``source`` and validate each record against the YAML schema.

        For every record the method checks:

        1. The raw line is exactly 94 characters (NACHA standard).
        2. Each field declared in the matching record-type schema is extracted
           using its ``position`` and compared against the declared ``length``.

        Returns a dict with the same ``records`` and ``vector`` keys as
        :meth:`parse`, plus:

        * ``errors`` – list of dicts with keys ``line_no``, ``record_type``,
          ``field`` (``None`` for line-level errors), and ``message``.
        * ``valid`` – ``True`` when ``errors`` is empty.
        """
        parsed = self.parse(source)
        records = parsed["records"]
        errors: List[Dict[str, Any]] = []

        schema = self.vector.get("nacha_validation_schema", {}) or {}
        record_types: Dict[str, Any] = (
            schema.get("record_types", {}) if isinstance(schema, dict) else {}
        )

        for rec in records:
            line: str = rec["raw"]
            line_no: int = rec["line_no"]
            rt: str = rec["record_type"]

            # Rule 1: every NACHA record must be exactly 94 characters.
            if len(line) != 94:
                errors.append({
                    "line_no": line_no,
                    "record_type": rt,
                    "field": None,
                    "message": f"Record length is {len(line)}, expected 94",
                })

            # Rule 2: each declared field must occupy the right slice.
            rt_def = self._find_record_type_def(record_types, rt)
            if rt_def is None:
                continue

            for field_name, field_spec in rt_def.get("fields", {}).items():
                pos = field_spec.get("position")
                expected_len: Optional[int] = field_spec.get("length")
                if pos is None or expected_len is None:
                    continue

                # Convert 1-based YAML positions to a Python slice.
                if isinstance(pos, list):
                    start, end = pos[0] - 1, pos[1]   # [start, end] inclusive
                else:
                    start, end = pos - 1, pos          # single character

                actual_value = line[start:end]
                if len(actual_value) != expected_len:
                    errors.append({
                        "line_no": line_no,
                        "record_type": rt,
                        "field": field_name,
                        "message": (
                            f"Field '{field_name}' at position {pos}: "
                            f"expected length {expected_len}, got {len(actual_value)}"
                        ),
                    })

        return {
            "records": records,
            "vector": self.vector,
            "errors": errors,
            "valid": len(errors) == 0,
        }

    def _find_record_type_def(
        self, record_types: Dict[str, Any], rt: str
    ) -> Optional[Dict[str, Any]]:
        """Return the schema dict for *rt* that contains a ``fields`` key.

        Handles two key formats found in the wild:
        * Direct keys: ``"1"``, ``"5"``, … (used in tests and simple schemas)
        * Prefixed keys: ``"type_1"``, ``"type_5"``, … (used in the project YAML)
        Falls back to scanning every entry for a matching ``code`` value.
        """
        for key in (rt, str(rt), f"type_{rt}"):
            candidate = record_types.get(key)
            if isinstance(candidate, dict) and "fields" in candidate:
                return candidate

        # Last resort: scan by the `code` field declared inside each entry.
        for val in record_types.values():
            if isinstance(val, dict) and val.get("code") == rt and "fields" in val:
                return val

        return None
