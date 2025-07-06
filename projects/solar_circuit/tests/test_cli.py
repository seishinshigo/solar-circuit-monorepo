# tests/test_cli.py
from typer.testing import CliRunner
from solar_circuit.cli import app

def test_hello():
    result = CliRunner().invoke(app, ["hello", "Solar"])
    assert "Solar" in result.stdout and result.exit_code == 0
