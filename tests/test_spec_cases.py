"""
Parametrized tests derived directly from ``test_cases`` in
nacha_error_definitions.yml.  The YAML is the single source of truth;
changing it automatically changes the tests here.

Mapping rules
─────────────
``expected_result: PASS`` + ``records[].data``
    One test per record.  The raw data is padded to 94 characters (the YAML
    entries are illustrative, not production-padded) and fed to
    ``Parser.validate()``.  The test asserts no line-level length errors and
    that the parsed record type matches the declared ``type`` field.

``error_code: ERR_001``
    A short-line input is synthesized and ``validate()`` must report at least
    one line-level error (``field`` is ``None``).

All other ``error_code`` / ``warning_code`` entries
    Collected as parametrized cases but skipped, making the coverage gap
    visible in the test output without hiding any tests.
"""
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from nacha_parser import Parser

# ── Module-level YAML load (required for @pytest.mark.parametrize) ───────────

_SPECS_DIR = Path(__file__).resolve().parents[1] / "specs" / "yml"

# Codes that Parser.validate() currently enforces.
_IMPLEMENTED_CODES = {"ERR_001"}


def _load_test_cases() -> Dict[str, Any]:
    path = _SPECS_DIR / "nacha_error_definitions.yml"
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return data.get("test_cases", {})


_TEST_CASES: Dict[str, Any] = _load_test_cases()


# ── Parameter builders ────────────────────────────────────────────────────────

def _pass_record_params() -> List[pytest.param]:
    """One param per record in PASS test cases that supply ``data``."""
    params = []
    for case_id, tc in _TEST_CASES.items():
        if tc.get("expected_result") != "PASS" or "records" not in tc:
            continue
        for rec in tc["records"]:
            raw: str = rec.get("data", "")
            # Illustrative YAML data is rarely exactly 94 chars; pad so the
            # record-length check doesn't mask the type-identity check.
            padded = raw.ljust(94)[:94]
            params.append(
                pytest.param(
                    padded,
                    str(rec["type"]),
                    id=f"{case_id}·{rec.get('name', 'record')}",
                )
            )
    return params


def _err001_params() -> List[pytest.param]:
    """One param per ``ERR_001`` test case."""
    return [
        pytest.param(tc.get("description", case_id), id=case_id)
        for case_id, tc in _TEST_CASES.items()
        if tc.get("error_code") == "ERR_001"
    ]


def _unimplemented_params() -> List[pytest.param]:
    """Cases whose codes are not yet enforced by ``validate()``."""
    params = []
    for case_id, tc in _TEST_CASES.items():
        code = tc.get("error_code") or tc.get("warning_code")
        if code and code not in _IMPLEMENTED_CODES:
            params.append(pytest.param(code, id=case_id))
    return params


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def parser() -> Parser:
    return Parser(specs_dir=str(_SPECS_DIR))


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw_line,expected_type", _pass_record_params())
def test_pass_case_record(parser, raw_line, expected_type):
    """Records from PASS spec cases must have no length errors and the right type."""
    result = parser.validate(raw_line)
    length_errors = [e for e in result["errors"] if e["field"] is None]
    assert length_errors == [], f"Unexpected length errors: {length_errors}"
    assert result["records"][0]["record_type"] == expected_type


@pytest.mark.parametrize("description", _err001_params())
def test_fail_record_length(parser, description):
    """A record shorter than 94 chars must trigger a line-level error (ERR_001)."""
    short_line = "1" + "X" * 10  # 11 chars, clearly not 94
    result = parser.validate(short_line)
    assert not result["valid"]
    assert any(e["field"] is None for e in result["errors"]), (
        "Expected a line-level length error but none was reported"
    )


@pytest.mark.parametrize("error_code", _unimplemented_params())
def test_unimplemented_case(error_code):
    """Skipped until validate() implements the relevant check."""
    pytest.skip(f"validate() does not yet enforce {error_code}")
