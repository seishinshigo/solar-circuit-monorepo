# solar_circuit/solar_circuit/cli.py
from pathlib import Path
import shutil
import subprocess
import typer

app = typer.Typer(help="Solar Circuit CLI")

# ── report サブコマンド ────────────────────────────────
report_app = typer.Typer(help="作業レポート関連コマンド")
app.add_typer(report_app, name="report")

@app.command("hello")
def hello(
    name: str = typer.Argument(  # ← Argument に変更
        "world",
        help="呼びかける名前 (省略可, デフォルト: world)",
    )
):
    """動作確認 Hello コマンド"""
    typer.echo(f"Hello {name}!")

@report_app.command("save")
def save(
    id: str = typer.Argument(..., help="Work-Order ID (wo-YYYYMMDD-XXX)"),
    file: Path = typer.Argument(
        ..., exists=True, readable=True, help="レポート Markdown ファイル"
    ),
):
    """Markdown レポートを所定ディレクトリへ移動し git add する"""
    dst_dir = Path("projects/solar_circuit/workorders/reports")
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst_path = dst_dir / f"{id}_report.md"
    shutil.move(str(file), dst_path)
    typer.echo(f"✅ Report saved to {dst_path}")

    try:
        subprocess.check_call(["git", "add", str(dst_path)])
        typer.echo("📂 git add executed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        typer.echo("⚠️ git add failed—but file is saved.")

if __name__ == "__main__":
    app()
