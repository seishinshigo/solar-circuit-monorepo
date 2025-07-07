# solar_circuit/solar_circuit/cli.py
import json
import shutil
import subprocess
from pathlib import Path
import typer
import jsonschema

app = typer.Typer(help="Solar Circuit CLI")

# --- plan サブコマンド --------------------------------------------------
plan_app = typer.Typer(help="Work-Order 関連コマンド")
app.add_typer(plan_app, name="plan")

# --- report サブコマンド ------------------------------------------------
report_app = typer.Typer(help="作業レポート関連コマンド")
app.add_typer(report_app, name="report")


# ╭─────────────────────────── 基本コマンド ───────────────────────────╮
@app.command("hello")
def hello(
    name: str = typer.Argument("world", help="呼びかける名前 (省略可)")
):
    """動作確認 Hello コマンド"""
    typer.echo(f"Hello {name}!")
# ╰────────────────────────────────────────────────────────────────────╯


# ╭──────────────────── Work-Order / Report Validate ─────────────────╮
@plan_app.command("validate")
def validate_workorder(
    file: Path = typer.Argument(..., exists=True, readable=True)
):
    """Work-Order JSON をスキーマ検証"""
    schema_path = Path("shared_libs/schemas/gemini.workorder@1.json")
    _validate_json(file, schema_path)


@report_app.command("validate")
def validate_report(
    file: Path = typer.Argument(..., exists=True, readable=True)
):
    """Status-Report JSON をスキーマ検証 (外部 $ref 対応)"""
    schema_dir = Path("shared_libs/schemas")
    report_schema = schema_dir / "gemini.report@1.json"
    work_schema   = schema_dir / "gemini.workorder@1.json"

    with work_schema.open() as f:
        work_def = json.load(f)
    with report_schema.open() as f:
        rep_def = json.load(f)

    with file.open() as f:
        instance = json.load(f)

    resolver = jsonschema.RefResolver.from_schema(rep_def, store={work_def["$id"]: work_def})
    jsonschema.validate(instance, rep_def, resolver=resolver)
    typer.echo(f"✅ {file} is valid.")


def _validate_json(file: Path, schema_path: Path):
    try:
        schema = json.loads(schema_path.read_text())
        data   = json.loads(file.read_text())
        jsonschema.validate(instance=data, schema=schema)
        typer.echo(f"✅ {file} is valid.")
    except (json.JSONDecodeError, jsonschema.ValidationError) as e:
        typer.echo(f"❌ Validation failed: {e}")
        raise typer.Exit(code=1)
# ╰────────────────────────────────────────────────────────────────────╯


@report_app.command("create")
def create_report(
    id: str = typer.Argument(..., help="Work-Order ID (wo-YYYYMMDD-XXX)"),
):
    """指定された Work-Order ID のレポートスケルトンを生成"""
    template_path = Path("templates/report_template.md")
    report_dir = Path("workorders/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{id}_report.md"

    if report_path.exists():
        typer.echo(f"⚠️ Report already exists: {report_path}")
        raise typer.Exit(code=1)

    template_content = template_path.read_text()
    # WO_ID をテンプレートに埋め込む
    filled_content = template_content.replace("[WO-YYYYMMDD-XXX]", id)
    filled_content = filled_content.replace("[ワークオーダーのタイトル]", f"Work Order {id}") # 仮のタイトル

    report_path.write_text(filled_content)
    typer.echo(f"✅ Report skeleton created at {report_path}")


# ╭────────────────────────── report save ───────────────────────────╮
@report_app.command("save")
def save(
    id: str  = typer.Argument(..., help="Work-Order ID (wo-YYYYMMDD-XXX)"),
    file: Path = typer.Argument(..., exists=True, readable=True)
):
    """Markdown レポートを所定ディレクトリへ保存し git add"""
    dst_dir  = Path("projects/solar_circuit/workorders/reports")
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst_path = dst_dir / f"{id}_report.md"
    shutil.move(str(file), dst_path)
    typer.echo(f"✅ Report saved to {dst_path}")

    try:
        subprocess.run(["git", "add", str(dst_path)], check=True)
        typer.echo("📂 git add executed.")
    except Exception:
        typer.echo("⚠️ git add failed (ignored).")
# ╰───────────────────────────────────────────────────────────────────╯


# ╭──────────────────────────── commit ──────────────────────────────╮
@app.command("commit")
def commit(msg: str = typer.Argument(..., help="Git commit message")):
    """
    1) ステージ済み差分から Work-Order ID を推測し report save → git add  
    2) git add -A → git commit を実行
    """
    # 1. WO_ID 推測（インデックス差分）
    try:
        wo_id = subprocess.check_output(
            "git diff --cached --name-only | grep -oE 'wo-[0-9]{8}-[0-9]{3}' | head -n1 || true",
            shell=True, text=True).strip()
    except subprocess.CalledProcessError:
        wo_id = ""

    if wo_id:
        report_path = Path(f"projects/solar_circuit/workorders/reports/{wo_id}_report.md")
        if report_path.exists():
            typer.echo(f"ℹ️ Report already exists → {report_path}")
        else:
            typer.echo(f"📝 Generating report for {wo_id}")
            subprocess.run(["sc", "report", "save", wo_id, "README.md"], check=False)  # README.md などダミー指定
    else:
        typer.echo("⚠️  No Work-Order ID found in staged diff – skipping report generation.")

    # 2. git add -A & commit
    subprocess.run(["git", "add", "-A"], check=True)
    subprocess.run(["git", "commit", "-m", msg], check=True)
    typer.echo("✅ Commit completed.")
# ╰──────────────────────────────────────────────────────────────────╯


if __name__ == "__main__":
    app()
