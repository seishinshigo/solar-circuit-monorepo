# tests/test_cli_error.py
import typer
from typer.testing import CliRunner
from solar_circuit.cli import app

runner = CliRunner()

def test_cli_no_args():
    result = runner.invoke(app, [])
    assert result.exit_code != 0
    assert "Usage" in result.output