import textwrap
from pathlib import Path

import yaml

from nacha_parser import Parser


def write_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump(data, f)


def test_load_vector_and_parse_string(tmp_path):
    specs_yml = tmp_path / "specs" / "yml"
    specs_yml.mkdir(parents=True)

    # Minimal schema describing record types
    schema = {
        "record_types": {
            "1": {"name": "File Header"},
            "5": {"name": "Batch Header"},
            "6": {"name": "Entry Detail"},
        }
    }

    write_yaml(specs_yml / "nacha_validation_schema.yml", schema)
    write_yaml(specs_yml / "nacha_validation_rules.yml", {})
    write_yaml(specs_yml / "nacha_error_definitions.yml", {})

    parser = Parser(specs_dir=str(specs_yml))

    sample = textwrap.dedent("""
        1HEADERLINEEXAMPLE
        5BATCHHEADERLINE
        6ENTRYDETAILLINE
        """)

    result = parser.parse(sample)

    assert "records" in result
    assert len(result["records"]) == 3
    assert result["records"][0]["record_type"] == "1"
    assert result["records"][0]["schema"]["name"] == "File Header"
    assert result["records"][2]["record_type"] == "6"


def _make_parser_with_field_schema(tmp_path):
    """Return a Parser whose schema declares two fields covering all 94 chars."""
    specs_yml = tmp_path / "specs" / "yml"
    specs_yml.mkdir(parents=True)
    schema = {
        "record_types": {
            "1": {
                "name": "File Header",
                "fields": {
                    "record_type_code": {"position": 1, "length": 1, "type": "numeric"},
                    "rest": {"position": [2, 94], "length": 93, "type": "alphanumeric"},
                },
            }
        }
    }
    write_yaml(specs_yml / "nacha_validation_schema.yml", schema)
    return Parser(specs_dir=str(specs_yml))


def test_validate_valid_record(tmp_path):
    parser = _make_parser_with_field_schema(tmp_path)
    line = "1" + "A" * 93  # exactly 94 chars
    result = parser.validate(line)
    assert result["valid"] is True
    assert result["errors"] == []


def test_validate_wrong_line_length(tmp_path):
    parser = _make_parser_with_field_schema(tmp_path)
    short_line = "1" + "A" * 10  # only 11 chars
    result = parser.validate(short_line)
    assert result["valid"] is False
    length_errors = [e for e in result["errors"] if e["field"] is None]
    assert len(length_errors) == 1
    assert "11" in length_errors[0]["message"]
    assert length_errors[0]["line_no"] == 1


def test_validate_field_length_mismatch(tmp_path):
    parser = _make_parser_with_field_schema(tmp_path)
    # 50 chars total — line-length error AND field 'rest' will be short
    short_line = "1" + "A" * 49
    result = parser.validate(short_line)
    assert result["valid"] is False
    field_errors = [e for e in result["errors"] if e["field"] == "rest"]
    assert len(field_errors) == 1
    assert "expected length 93" in field_errors[0]["message"]


def test_validate_uses_type_prefixed_keys(tmp_path):
    """validate() must handle 'type_1' style keys from the real YAML schema."""
    specs_yml = tmp_path / "specs" / "yml"
    specs_yml.mkdir(parents=True)
    schema = {
        "record_types": {
            "type_1": {
                "name": "File Header",
                "code": "1",
                "fields": {
                    "record_type_code": {"position": 1, "length": 1, "type": "numeric"},
                    "rest": {"position": [2, 94], "length": 93, "type": "alphanumeric"},
                },
            }
        }
    }
    write_yaml(specs_yml / "nacha_validation_schema.yml", schema)
    parser = Parser(specs_dir=str(specs_yml))
    line = "1" + "B" * 93
    result = parser.validate(line)
    assert result["valid"] is True


def test_parse_file(tmp_path):
    specs_yml = tmp_path / "specs" / "yml"
    specs_yml.mkdir(parents=True)

    schema = {"record_types": {"1": {"name": "File Header"}}}
    write_yaml(specs_yml / "nacha_validation_schema.yml", schema)
    write_yaml(specs_yml / "nacha_validation_rules.yml", {})
    write_yaml(specs_yml / "nacha_error_definitions.yml", {})

    content = "1SINGLELINEFORFILE\n"
    sample_file = tmp_path / "sample.ach"
    sample_file.write_text(content)

    parser = Parser(specs_dir=str(specs_yml))
    res = parser.parse_file(str(sample_file))

    assert len(res["records"]) == 1
    assert res["records"][0]["raw"] == "1SINGLELINEFORFILE"
    assert res["records"][0]["schema"]["name"] == "File Header"
