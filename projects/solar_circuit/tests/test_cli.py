# tests/test_cli.py
import subprocess
from pathlib import Path
from typer.testing import CliRunner
from solar_circuit.cli import app

runner = CliRunner()

def test_hello():
    result = runner.invoke(app, ["hello", "Solar"])
    assert "Solar" in result.stdout and result.exit_code == 0

def test_report_save(tmp_path: Path):
    # ダミーのレポートファイルを作成
    report_content = "# Test Report"
    report_file = tmp_path / "test_report.md"
    report_file.write_text(report_content)

    # レポート保存先ディレクトリ
    reports_dir = Path("projects/solar_circuit/workorders/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Work-Order ID
    wo_id = "wo-20250706-999"
    expected_report_path = reports_dir / f"{wo_id}_report.md"

    # 実行前にファイルが存在しないことを確認
    if expected_report_path.exists():
        expected_report_path.unlink()

    # コマンドを実行
    result = runner.invoke(app, ["report", "save", wo_id, str(report_file)])

    # 検証
    assert result.exit_code == 0
    assert f"Report saved to {expected_report_path}" in result.stdout
    assert expected_report_path.exists()
    assert expected_report_path.read_text() == report_content

    # git add が実行されたか（subprocessをモックせずに簡易的に確認）
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    assert str(expected_report_path) in result.stdout

    # 後片付け
    expected_report_path.unlink()
