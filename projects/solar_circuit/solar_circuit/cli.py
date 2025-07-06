# solar_circuit/solar_circuit/cli.py
import json
from pathlib import Path
import shutil
import subprocess
import typer
import jsonschema

app = typer.Typer(help="Solar Circuit CLI")

# --- plan サブコマンド ---
plan_app = typer.Typer(help="Work-Order 関連コマンド")
app.add_typer(plan_app, name="plan")

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

@plan_app.command("validate")
def validate_workorder(
    file: Path = typer.Argument(..., exists=True, readable=True, help="検証する Work-Order JSON ファイル")
):
    """Work-Order を JSON Schema で検証する"""
    schema_path = Path("/home/wandr/seishinshigo_system/shared_libs/schemas/gemini.workorder@1.json")
    if not schema_path.exists():
        typer.echo(f"❌ Schema not found at {schema_path}")
        raise typer.Exit(code=1)

    try:
        with open(schema_path, "r") as f:
            schema = json.load(f)
        with open(file, "r") as f:
            instance = json.load(f)

        jsonschema.validate(instance=instance, schema=schema)
        typer.echo(f"✅ Validation successful for {file}")

    except json.JSONDecodeError:
        typer.echo(f"❌ Invalid JSON in {file}")
        raise typer.Exit(code=1)
    except jsonschema.ValidationError as e:
        typer.echo(f"❌ Validation failed for {file}")
        typer.echo(f"Error: {e.message}")
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"An unexpected error occurred: {e}")
        raise typer.Exit(code=1)

@report_app.command("validate")
def validate_report(
    file: Path = typer.Argument(..., exists=True, readable=True, help="検証する Report JSON ファイル")
):
    """Status-Report を JSON Schema で検証する"""
    schema_dir = Path("/home/wandr/seishinshigo_system/shared_libs/schemas")
    report_schema_path = schema_dir / "gemini.report@1.json"
    workorder_schema_path = schema_dir / "gemini.workorder@1.json"

    if not report_schema_path.exists() or not workorder_schema_path.exists():
        typer.echo(f"❌ Schema files not found in {schema_dir}")
        raise typer.Exit(code=1)

    try:
        with open(report_schema_path, "r") as f:
            report_schema = json.load(f)
        with open(workorder_schema_path, "r") as f:
            workorder_schema = json.load(f)
        with open(file, "r") as f:
            instance = json.load(f)

        schema_store = {
            workorder_schema["$id"]: workorder_schema,
        }
        resolver = jsonschema.RefResolver.from_schema(report_schema, store=schema_store)
        jsonschema.validate(instance=instance, schema=report_schema, resolver=resolver)
        typer.echo(f"✅ Validation successful for {file}")

    except json.JSONDecodeError:
        typer.echo(f"❌ Invalid JSON in {file}")
        raise typer.Exit(code=1)
    except jsonschema.ValidationError as e:
        typer.echo(f"❌ Validation failed for {file}")
        typer.echo(f"Error: {e.message}")
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"An unexpected error occurred: {e}")
        raise typer.Exit(code=1)


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
