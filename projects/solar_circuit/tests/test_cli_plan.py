# tests/test_cli_plan.py
from pathlib import Path
from typer.testing import CliRunner
from solar_circuit.cli import app

runner = CliRunner()

def test_plan_validate_valid(tmp_path: Path):
    schema_dir = Path("shared_libs/schemas")
    schema_dir.mkdir(parents=True, exist_ok=True)
    (schema_dir / "gemini.workorder@1.json").write_text("{\"type\": \"object\"}")

    workorder_file = tmp_path / "wo.json"
    workorder_file.write_text("{}")

    result = runner.invoke(app, ["plan", "validate", str(workorder_file)])
    assert result.exit_code == 0
    assert "is valid" in result.stdout

def test_plan_validate_invalid(tmp_path: Path):
    schema_dir = Path("shared_libs/schemas")
    schema_dir.mkdir(parents=True, exist_ok=True)
    (schema_dir / "gemini.workorder@1.json").write_text("{\"type\": \"string\"}")

    workorder_file = tmp_path / "wo.json"
    workorder_file.write_text("{}")

    result = runner.invoke(app, ["plan", "validate", str(workorder_file)])
    assert result.exit_code == 1
    assert "Validation failed" in result.stdout
