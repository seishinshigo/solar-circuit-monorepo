import json
from pathlib import Path
import pytest
from unittest.mock import patch

# テスト対象の関数をインポート
from solar_circuit.report_generator import (
    load_workorder,
    generate_report_from_work_id,
    determine_mode,
    clean_summary_content
)

# --- テストデータ ---
MOCK_WO_ID = "20250701-001"
MOCK_WO_DATA = {
    "id": MOCK_WO_ID,
    "title": "Test Workorder",
    "file_path": "docs/test.md",
    "metadata": {}
}
MOCK_TEMPLATE_CONTENT = "<!-- TEMPLATE_START -->\n# {{ workorder.title }}\n\n{{ workorder.summary_content }}\n<!-- TEMPLATE_END -->"
MOCK_RELATED_DOC_CONTENT = "This is a related document."

@pytest.fixture
def setup_test_environment(tmp_path):
    """テスト用のディレクトリとファイルを作成するフィクスチャ"""
    project_root = tmp_path
    
    # .env ファイル
    (project_root / ".env").write_text(f"PROJECT_ROOT={project_root}")

    # 必要なディレクトリを作成
    (project_root / "workorders/incoming").mkdir(parents=True)
    (project_root / "workorders/reports").mkdir(parents=True)
    (project_root / "templates").mkdir(parents=True)
    (project_root / "docs").mkdir(parents=True)
    (project_root / "logs").mkdir(parents=True)

    # モックのワークオーダーファイルを作成
    wo_file = project_root / f"workorders/incoming/WO-{MOCK_WO_ID}.json"
    wo_file.write_text(json.dumps(MOCK_WO_DATA))

    # モックのテンプレートファイルを作成
    template_file = project_root / "templates/report_template.md"
    template_file.write_text(MOCK_TEMPLATE_CONTENT)

    # モックの関連ドキュメントを作成
    related_doc_file = project_root / "docs/test.md"
    related_doc_file.write_text(MOCK_RELATED_DOC_CONTENT)

    # report_generatorのPROJECT_ROOTをパッチ
    with patch('solar_circuit.report_generator.PROJECT_ROOT', project_root):
        yield project_root

def test_load_workorder_with_related_docs(setup_test_environment):
    """関連ドキュメントが正しく読み込まれるかテスト"""
    project_root = setup_test_environment
    
    with patch('solar_circuit.report_generator.PROJECT_ROOT', project_root):
        workorder = load_workorder(MOCK_WO_ID)
        assert workorder["summary_content"] == MOCK_RELATED_DOC_CONTENT

def test_load_workorder_with_duplicated_path(setup_test_environment):
    """パスが重複している場合に正しく解決されるかテスト"""
    project_root = setup_test_environment
    
    # WOデータを書き換えて、重複パスのシナリオを作成
    # project_rootが/tmp/pytest-of-user/pytest-0/setup_test_environment0 のような形になるので
    # その親の名前と、自身の名前を結合して重複パスを作る
    duplicated_path = f"{project_root.parent.name}/{project_root.name}/docs/test.md"
    
    wo_data_with_dup_path = MOCK_WO_DATA.copy()
    wo_data_with_dup_path["file_path"] = duplicated_path
    
    wo_file = project_root / f"workorders/incoming/WO-{MOCK_WO_ID}.json"
    wo_file.write_text(json.dumps(wo_data_with_dup_path))

    with patch('solar_circuit.report_generator.PROJECT_ROOT', project_root):
        workorder = load_workorder(MOCK_WO_ID)
        # 関連ドキュメントの内容が正しく読み込まれていることを確認
        assert workorder["summary_content"] == MOCK_RELATED_DOC_CONTENT

def test_load_workorder_with_missing_file(setup_test_environment):
    """関連ファイルが存在しない場合に警告ログが出るかテスト"""
    project_root = setup_test_environment
    
    # 存在しないファイルパスを持つWOデータを作成
    wo_data_missing_file = MOCK_WO_DATA.copy()
    wo_data_missing_file["file_path"] = "docs/non_existent_file.md"
    
    wo_file = project_root / f"workorders/incoming/WO-{MOCK_WO_ID}.json"
    wo_file.write_text(json.dumps(wo_data_missing_file))

    # ロガーをパッチして、警告が呼ばれたか確認
    with patch('solar_circuit.report_generator.logger.warning') as mock_warning:
        with patch('solar_circuit.report_generator.PROJECT_ROOT', project_root):
            workorder = load_workorder(MOCK_WO_ID)
            # summary_contentが空であることを確認
            assert workorder["summary_content"] == ""
            # logger.warningが1回呼ばれたことを確認
            mock_warning.assert_called_once()

def test_generate_report_new(setup_test_environment):
    """新規レポートが正しく生成されるかテスト"""
    project_root = setup_test_environment
    report_path = project_root / f"workorders/reports/WO-{MOCK_WO_ID}_report.md"

    generate_report_from_work_id(MOCK_WO_ID)

    assert report_path.exists()
    content = report_path.read_text()
    assert MOCK_WO_DATA["title"] in content
    assert MOCK_RELATED_DOC_CONTENT in content

def test_determine_mode_append(tmp_path):
    """APPENDモードが正しく判定されるかテスト"""
    report_path = tmp_path / "report.md"
    report_path.write_text("<!-- TEMPLATE_START -->\nOld content\n<!-- TEMPLATE_END -->\n\nUser content.")
    
    rendered_template = "<!-- TEMPLATE_START -->\nNew content\n<!-- TEMPLATE_END -->"
    
    mode, _ = determine_mode(report_path, rendered_template)
    assert mode == "APPEND"

def test_determine_mode_recover(tmp_path):
    """RECOVERモードが正しく判定されるかテスト"""
    report_path = tmp_path / "report.md"
    report_path.write_text("Some content without markers.")
    
    rendered_template = "<!-- TEMPLATE_START -->\nTemplate\n<!-- TEMPLATE_END -->"
    
    mode, _ = determine_mode(report_path, rendered_template)
    assert mode == "RECOVER"

def test_clean_summary_content():
    """Markdown見出しレベルが正しく調整されるかテスト"""
    content = "# Title\n## Subtitle\nSome text."
    expected = "## Title\n### Subtitle\nSome text."
    assert clean_summary_content(content) == expected