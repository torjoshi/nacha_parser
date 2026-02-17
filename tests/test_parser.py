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
