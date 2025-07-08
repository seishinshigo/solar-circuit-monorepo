import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# テスト対象のスクリプトが配置されているディレクトリをシステムパスに追加
# これにより、`from solar_circuit.report_generator import ...` が可能になる
SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.append(str(SCRIPT_DIR))

from solar_circuit.report_generator import (
    determine_mode,
    extract_template_from_file,
    load_workorder,
    main,
    render_template,
    write_report,
    Mode,
    TEMPLATE_START,
    TEMPLATE_END,
)

# --- テスト用のフィクスチャ ---------------------------------------------------

@pytest.fixture
def temp_project_dir():
    """一時的なプロジェクトディレクトリ構造を作成するフィクスチャ"""
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        (p / "workorders" / "incoming").mkdir(parents=True)
        (p / "workorders" / "reports").mkdir(parents=True)
        (p / "templates").mkdir(parents=True)
        (p / "logs").mkdir(parents=True)
        yield p

@pytest.fixture
def mock_workorder(temp_project_dir):
    """モックのワークオーダーファイルを作成するフィクスチャ"""
    wo_path = temp_project_dir / "workorders" / "incoming" / "WO-20250709-001.json"
    wo_data = {
        "id": "20250709-001",
        "title": "テスト作業",
        "metadata": {"related_docs": "docs/test.md"},
        "steps_formatted": "- ステップ1\n- ステップ2",
        "expected_output_formatted": "- [x] 完了条件A",
        "file_path": "collaboration/design_docs/test_summary.md"
    }
    with open(wo_path, "w", encoding="utf-8") as f:
        json.dump(wo_data, f, ensure_ascii=False, indent=2)

    related_doc_path = temp_project_dir / "collaboration" / "design_docs" / "test_summary.md"
    related_doc_path.parent.mkdir(parents=True, exist_ok=True)
    related_doc_path.write_text("# テストサマリー\nこれはテスト用のサマリーコンテンツです。", encoding="utf-8")

    return wo_data

@pytest.fixture
def mock_template(temp_project_dir):
    """ユニットテスト用テンプレートフィクスチャ"""
    template_path = temp_project_dir / "templates" / "report_template.md"
    template_content = (
        TEMPLATE_START
        + "\n# {{ workorder.title }}\n\n作業ID: {{ workorder.id }}\n"
        + TEMPLATE_END
        + "\n"
    )
    template_path.write_text(template_content, encoding="utf-8")
    return template_content

# --- 単体テスト --------------------------------------------------------------

def test_load_workorder_success(mock_workorder, temp_project_dir):
    with patch("solar_circuit.report_generator.PROJECT_ROOT", temp_project_dir):
        wo = load_workorder("20250709-001")
        assert wo["title"] == "テスト作業"

def test_load_workorder_not_found(temp_project_dir):
    with patch("solar_circuit.report_generator.PROJECT_ROOT", temp_project_dir):
        with pytest.raises(FileNotFoundError):
            load_workorder("non-existent-id")

def test_extract_template_from_file(mock_template, temp_project_dir):
    template_path = temp_project_dir / "templates" / "report_template.md"
    extracted = extract_template_from_file(template_path)
    assert "# {{ workorder.title }}" in extracted
    assert TEMPLATE_START in extracted
    assert TEMPLATE_END in extracted

def test_extract_template_missing_markers(temp_project_dir):
    template_path = temp_project_dir / "templates" / "report_template.md"
    template_path.write_text("マーカーのないテンプレート", encoding="utf-8")
    with pytest.raises(ValueError):
        extract_template_from_file(template_path)

def test_render_template():
    template_str = "タイトル: {{ workorder.title }}"
    wo_data = {"title": "レンダリングテスト"}
    rendered = render_template(template_str, wo_data)
    assert rendered == "タイトル: レンダリングテスト"

def test_render_template_with_undefined_vars():
    template_str = "タイトル: {{ workorder.title }}, 未定義: {{ workorder.undefined_key }}"
    wo_data = {"title": "レンダリングテスト"}
    rendered = render_template(template_str, wo_data)
    assert rendered == "タイトル: レンダリングテスト, 未定義: "

def test_render_template_with_summary_content():
    template_str = "概要: {{ workorder.summary_content }}"
    wo_data = {"summary_content": "これはサマリーです。"}
    rendered = render_template(template_str, wo_data)
    assert rendered == "概要: これはサマリーです。"

# --- モード判定テスト ---------------------------------------------------------

@pytest.mark.parametrize(
    "file_content, rendered_template, expected_mode",
    [
        (None, "<start>Tpl</start>", "NEW"),
        ("<start>Tpl</start>", "<start>Tpl</start>", "OVERWRITE_TEMPLATE"),
        ("<start>Tpl</start>\nUser Content", "<start>Tpl</start>", "APPEND"),
        ("<start>Old Tpl</start>\nUser Content", "<start>New Tpl</start>", "APPEND"),
        ("No markers here", "<start>Tpl</start>", "RECOVER"),
    ]
)
def test_determine_mode(temp_project_dir, file_content, rendered_template, expected_mode):
    report_path = temp_project_dir / "report.md"
    if file_content is not None:
        report_path.write_text(
            file_content.replace("<start>", TEMPLATE_START).replace("</start>", TEMPLATE_END),
            encoding="utf-8"
        )
    rendered = rendered_template.replace("<start>", TEMPLATE_START).replace("</start>", TEMPLATE_END)
    mode, _ = determine_mode(report_path, rendered)
    assert mode == expected_mode

# --- write_report 統合テスト ------------------------------------------------

def run_write_report_test(temp_project_dir, mode: Mode, original_content: str | None, rendered_template: str):
    report_path = temp_project_dir / "report.md"
    if original_content:
        report_path.write_text(original_content, encoding="utf-8")
    write_report(report_path, rendered_template, mode, original_content)
    return report_path

def test_write_report_new(temp_project_dir):
    rendered = f"{TEMPLATE_START}\nNew Content\n{TEMPLATE_END}"
    report_path = run_write_report_test(temp_project_dir, "NEW", None, rendered)
    assert report_path.read_text(encoding="utf-8") == rendered

def test_write_report_overwrite(temp_project_dir):
    original = f"{TEMPLATE_START}\nOld Content\n{TEMPLATE_END}"
    rendered = f"{TEMPLATE_START}\nNew Content\n{TEMPLATE_END}"
    report_path = run_write_report_test(temp_project_dir, "OVERWRITE_TEMPLATE", original, rendered)
    assert report_path.read_text(encoding="utf-8") == rendered

def test_write_report_append(temp_project_dir):
    original = f"{TEMPLATE_START}\nOld Tpl\n{TEMPLATE_END}\n\nUser additions."
    rendered = f"{TEMPLATE_START}\nNew Tpl\n{TEMPLATE_END}"
    report_path = run_write_report_test(temp_project_dir, "APPEND", original, rendered)
    final_content = report_path.read_text(encoding="utf-8")
    assert "New Tpl" in final_content
    assert "User additions." in final_content
    assert (temp_project_dir / "report.patch").exists()

def test_write_report_recover(temp_project_dir):
    original = "No markers here."
    rendered = f"{TEMPLATE_START}\nContent\n{TEMPLATE_END}"
    report_path = run_write_report_test(temp_project_dir, "RECOVER", original, rendered)
    assert report_path.read_text(encoding="utf-8") == original
    recovered_files = list(temp_project_dir.glob("*_recovered_*.md"))
    assert len(recovered_files) == 1
    assert recovered_files[0].read_text(encoding="utf-8") == original

# --- main() E2E テスト -------------------------------------------------------

@patch("sys.argv", ["report_generator.py", "--work-id", "20250709-001"])
def test_main_flow_new(mock_workorder, temp_project_dir):
    with patch("solar_circuit.report_generator.PROJECT_ROOT", temp_project_dir):
        # テンプレートを patch 後に確実に生成
        tpl = temp_project_dir / "templates" / "report_template.md"
        tpl.parent.mkdir(parents=True, exist_ok=True)
        tpl.write_text(
            "<!-- TEMPLATE_START -->\n# タイトル: {{ workorder.title }}\n<!-- TEMPLATE_END -->",
            encoding="utf-8"
        )

        main()

        rpt = temp_project_dir / "workorders" / "reports" / "WO-20250709-001_report.md"
        assert rpt.exists()
        content = rpt.read_text(encoding="utf-8")
        assert "タイトル" in content
        assert "テスト作業" in content

@patch("sys.argv", ["report_generator.py", "--work-id", "20250709-001", "--force"])
def test_main_flow_force_overwrite(mock_workorder, temp_project_dir):
    with patch("solar_circuit.report_generator.PROJECT_ROOT", temp_project_dir):
        tpl = temp_project_dir / "templates" / "report_template.md"
        tpl.parent.mkdir(parents=True, exist_ok=True)
        tpl.write_text(
            "<!-- TEMPLATE_START -->\n# タイトル: {{ workorder.title }}\n<!-- TEMPLATE_END -->",
            encoding="utf-8"
        )

        rpt = temp_project_dir / "workorders" / "reports" / "WO-20250709-001_report.md"
        rpt.write_text("古いコンテンツ", encoding="utf-8")

        main()

        content = rpt.read_text(encoding="utf-8")
        assert "タイトル" in content
        assert "テスト作業" in content
        assert "古いコンテンツ" not in content

@patch("solar_circuit.report_generator.FORCE_OVERWRITE_ENV", True)
@patch("sys.argv", ["report_generator.py", "--work-id", "20250709-001"])
def test_main_flow_force_overwrite_env(mock_workorder, temp_project_dir):
    with patch("solar_circuit.report_generator.PROJECT_ROOT", temp_project_dir):
        tpl = temp_project_dir / "templates" / "report_template.md"
        tpl.parent.mkdir(parents=True, exist_ok=True)
        tpl.write_text(
            "<!-- TEMPLATE_START -->\n# タイトル: {{ workorder.title }}\n<!-- TEMPLATE_END -->",
            encoding="utf-8"
        )

        rpt = temp_project_dir / "workorders" / "reports" / "WO-20250709-001_report.md"
        rpt.write_text("古いコンテンツ", encoding="utf-8")

        main()

        content = rpt.read_text(encoding="utf-8")
        assert "タイトル" in content
        assert "テスト作業" in content
        assert "古いコンテンツ" not in content
