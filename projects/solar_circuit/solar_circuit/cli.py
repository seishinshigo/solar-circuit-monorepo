# solar_circuit/solar_circuit/cli.py
import json
import shutil
import subprocess
from pathlib import Path
import typer
import jsonschema

import datetime
import re

app = typer.Typer(help="Solar Circuit CLI")

# --- wo サブコマンド --------------------------------------------------
wo_app = typer.Typer(help="Work-Order 関連コマンド")
app.add_typer(wo_app, name="wo")

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


from solar_circuit.report_generator import generate_report_from_work_id

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
    work_id: str = typer.Argument(..., help="Work-Order ID (例: 20250709-001)"),
    force: bool = typer.Option(False, "--force", "-f", help="強制上書きモード")
):
    """指定された Work-Order ID のレポートを生成・更新"""
    try:
        # work_idを正規化
        formatted_id = work_id if work_id.startswith("WO-") else f"WO-{work_id}"
        generate_report_from_work_id(formatted_id, force)
        typer.echo(f"✅ Report for {formatted_id} processed successfully.")
    except FileNotFoundError as e:
        typer.echo(f"❌ Error: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"❌ An unexpected error occurred: {e}")
        raise typer.Exit(code=1)


@wo_app.command("create-from-chat")
def create_wo_from_chat(
    title: str = typer.Argument(..., help="ワークオーダーのタイトル"),
    description: str = typer.Argument("", help="ワークオーダーの詳細説明"),
    priority: str = typer.Option("medium", "--priority", "-p", help="優先度 (low, medium, high)"),
    due_date: str = typer.Option(None, "--due", "-d", help="期日 (YYYY-MM-DD)")
):
    """チャットからの依頼をワークオーダーとして生成し、処理を進める"""
    try:
        # テンプレートの読み込み
        template_path = Path("projects/solar_circuit/templates/workorder_template.json")
        if not template_path.exists():
            typer.echo(f"❌ ワークオーダーテンプレートが見つかりません: {template_path}")
            raise typer.Exit(code=1)
        with open(template_path, "r", encoding="utf-8") as f:
            wo_template = json.load(f)

        # 新しいワークオーダーIDの生成
        today = datetime.date.today()
        date_str = today.strftime("%Y%m%d")
        # 既存のWOをチェックして連番を決定
        incoming_dir = Path("projects/solar_circuit/workorders/incoming")
        existing_wo_files = list(incoming_dir.glob(f"WO-{date_str}-*.json"))
        next_seq = len(existing_wo_files) + 1
        wo_id = f"WO-{date_str}-{next_seq:03d}"

        # テンプレートに値を埋め込む
        wo_template["id"] = wo_id
        wo_template["title"] = title
        wo_template["priority"] = priority
        if due_date:
            wo_template["due"] = f"{due_date}T23:59:00+09:00"
        else:
            # デフォルトで3日後を設定
            default_due = today + datetime.timedelta(days=3)
            wo_template["due"] = f"{default_due.strftime("%Y-%m-%d")}T23:59:00+09:00"

        # file_path と related_docs の更新
        doc_filename = f"{wo_id}_workorder.md"
        wo_template["file_path"] = f"collaboration/design_docs/{doc_filename}"
        wo_template["metadata"]["related_docs"] = f"collaboration/design_docs/{doc_filename}"

        # description を steps_formatted に追加
        wo_template["steps_formatted"] = f"- [ ] {description}"

        # 新しいワークオーダーファイルを保存
        new_wo_path = incoming_dir / f"{wo_id}.json"
        with open(new_wo_path, "w", encoding="utf-8") as f:
            json.dump(wo_template, f, ensure_ascii=False, indent=2)
        typer.echo(f"✅ Work-Order created: {new_wo_path}")

        # 関連ドキュメントファイルを作成
        design_docs_dir = Path("projects/solar_circuit/collaboration/design_docs")
        design_docs_dir.mkdir(parents=True, exist_ok=True)
        related_doc_path = design_docs_dir / doc_filename
        related_doc_path.write_text(f"# {title}\n\n{description}", encoding="utf-8")
        typer.echo(f"✅ Related document created: {related_doc_path}")

        # 生成されたファイルをステージング
        subprocess.run(["git", "add", str(new_wo_path)], check=True)
        subprocess.run(["git", "add", str(related_doc_path)], check=True)

        # レポートを生成し、コミット
        typer.echo(f"📝 Generating report for {wo_id}...")
        generate_report_from_work_id(wo_id)
        typer.echo(f"✅ Report generated for {wo_id}.")

        typer.echo(f"🚀 Committing changes for {wo_id}...")
        subprocess.run(["sc", "commit", f"feat({wo_id}): {title}", "--wo-id", wo_id], check=True)
        typer.echo(f"✅ Work-Order {wo_id} processed and committed.")

    except Exception as e:
        typer.echo(f"❌ エラーが発生しました: {e}")
        raise typer.Exit(code=1)


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
def commit(
    msg: str = typer.Argument(..., help="Git commit message"),
    wo_id: str = typer.Option(None, "--wo-id", help="関連するWork-Order ID (WO-YYYYMMDD-XXX)")
):
    """
    1) 指定された Work-Order ID に関連するファイルをステージング
    2) git commit を実行
    """
    if wo_id:
        # WO-IDが指定された場合、関連ファイルをステージング
        wo_json_path = Path(f"projects/solar_circuit/workorders/incoming/{wo_id}.json")
        wo_report_path = Path(f"projects/solar_circuit/workorders/reports/{wo_id}_report.md")
        wo_related_doc_path = Path(f"projects/solar_circuit/collaboration/design_docs/{wo_id}_workorder.md")

        files_to_add = []
        if wo_json_path.exists():
            files_to_add.append(str(wo_json_path))
        if wo_report_path.exists():
            files_to_add.append(str(wo_report_path))
        if wo_related_doc_path.exists():
            files_to_add.append(str(wo_related_doc_path))

        if files_to_add:
            typer.echo(f"📂 Staging files for {wo_id}: {files_to_add}")
            subprocess.run(["git", "add"] + files_to_add, check=True)
        else:
            typer.echo(f"⚠️ No files found to stage for Work-Order {wo_id}. Nothing to commit.")
            raise typer.Exit(code=1)

    subprocess.run(["git", "commit", "-m", msg], check=True)
    typer.echo("✅ Commit completed.")
# ╰──────────────────────────────────────────────────────────────────╯


if __name__ == "__main__":
    app()
