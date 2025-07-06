import typer
import subprocess

app = typer.Typer(help="Solar Circuit CLI")

@app.command("hello")
def hello(
    name: str = typer.Argument("world", help="呼びかける名前")
) -> None:
    """動作確認コマンド"""
    typer.echo(f"Hello {name}!")

@app.command("report")
def report_command(ctx: typer.Context):
    """レポート関連コマンド"""
    pass

@report_command.command("save")
def save_report(
    workorder_id: str = typer.Argument(..., help="WorkOrder ID (例: wo-20240710-001)"),
    report_file: str = typer.Argument(..., help="保存するレポートファイルのパス"),
) -> None:
    """作業報告書を workorders/reports/ に保存します。"""
    try:
        subprocess.run(["./scripts/save_report.sh", workorder_id, report_file], check=True)
        typer.echo(f"Report for {workorder_id} saved successfully.")
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error saving report: {e}", err=True)
        raise typer.Exit(code=1)

def main() -> None:
    app()

if __name__ == "__main__":
    main()
