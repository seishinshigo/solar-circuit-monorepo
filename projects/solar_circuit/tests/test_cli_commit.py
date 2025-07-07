# tests/test_cli_commit.py
import subprocess
from typer.testing import CliRunner
from solar_circuit.cli import app

runner = CliRunner()

def test_commit():
    # gitリポジトリを初期化して、コミット対象のファイルを作成
    subprocess.run(["git", "init"])
    subprocess.run(["git", "config", "user.name", "test"])
    subprocess.run(["git", "config", "user.email", "test@example.com"])
    with open("wo-20250707-001.txt", "w") as f:
        f.write("test")
    subprocess.run(["git", "add", "wo-20250707-001.txt"])

    result = runner.invoke(app, ["commit", "test commit"])
    assert result.exit_code == 0
    assert "Commit completed" in result.stdout
