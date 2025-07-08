import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# テスト対象のスクリプトが配置されているディレクトリをシステムパスに追加
# これにより、`from report_generator import ...`のようなインポートが可能になる
SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.append(str(SCRIPT_DIR))

# `report_generator` モジュールから必要な関数や定数をインポート
from report_generator import (
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

# --- テスト用の設定とフィクスチャ ---

@pytest.fixture
def temp_project_dir():
    """一時的なプロジェクトディレクトリ構造を作成するフィクスチャ"""
    # `tempfile.TemporaryDirectory()` を使って一時ディレクトリを作成
    # `yield` でそのパスをテスト関数に渡し、テスト終了後に自動的にクリーンアップされる
    with tempfile.TemporaryDirectory() as tmpdir:
        # `pathlib.Path` を使ってパスをオブジェクトとして扱う
        p = Path(tmpdir)
        # テストに必要なサブディレクトリを作成
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
        "expected_output_formatted": "- [x] 完了条件A"
    }
    # `json.dump` を使って辞書をJSONファイルとして書き込む
    with open(wo_path, "w", encoding="utf-8") as f:
        json.dump(wo_data, f, ensure_ascii=False, indent=2)
    return wo_data

@pytest.fixture
def mock_template(temp_project_dir):
    """モックのテンプレートファイルを作成するフィクスチャ"""
    template_path = temp_project_dir / "templates" / "report_template.md"
    # f-string を避け、Jinja2 構文が正しく解釈されるようにする
    template_content = (
        TEMPLATE_START
        + "\n# {{ workorder.title }}\n\n作業ID: {{ workorder.id }}\n"
        + TEMPLATE_END
        + "\n"
    )
    # `Path.write_text` でテンプレート内容をファイルに書き込む
    template_path.write_text(template_content, encoding="utf-8")
    return template_content


# --- ユニットテスト ---

def test_load_workorder_success(mock_workorder, temp_project_dir):
    """ワークオーダーの読み込みが成功するケース"""
    # `patch` を使って `PROJECT_ROOT` の値を一時的なディレクトリに差し替える
    with patch("report_generator.PROJECT_ROOT", temp_project_dir):
        wo = load_workorder("20250709-001")
        assert wo["title"] == "テスト作業"

def test_load_workorder_not_found(temp_project_dir):
    """ワークオーダーファイルが見つからない場合に `FileNotFoundError` が発生するケース"""
    with patch("report_generator.PROJECT_ROOT", temp_project_dir):
        with pytest.raises(FileNotFoundError):
            load_workorder("non-existent-id")

def test_extract_template_from_file(mock_template, temp_project_dir):
    """テンプレートファイルからマーカー間の抽出が成功するケース"""
    template_path = temp_project_dir / "templates" / "report_template.md"
    extracted = extract_template_from_file(template_path)
    assert "# {{ workorder.title }}" in extracted
    assert TEMPLATE_START in extracted
    assert TEMPLATE_END in extracted

def test_extract_template_missing_markers(temp_project_dir):
    """テンプレートファイルにマーカーがない場合に `ValueError` が発生するケース"""
    template_path = temp_project_dir / "templates" / "report_template.md"
    template_path.write_text("マーカーのないテンプレート", encoding="utf-8")
    with pytest.raises(ValueError):
        extract_template_from_file(template_path)

def test_render_template():
    """Jinja2テンプレートのレンダリングが正しく行われるケース"""
    template_str = "タイトル: {{ workorder.title }}"
    wo_data = {"title": "レンダリングテスト"}
    rendered = render_template(template_str, wo_data)
    assert rendered == "タイトル: レンダリングテスト"

def test_render_template_with_undefined_vars():
    """Jinja2テンプレートに未定義の変数が含まれていてもエラーにならないケース"""
    template_str = "タイトル: {{ workorder.title }}, 未定義: {{ workorder.undefined_key }}"
    wo_data = {"title": "レンダリングテスト"}
    rendered = render_template(template_str, wo_data)
    assert rendered == "タイトル: レンダリングテスト, 未定義: "

# --- モード判定のテスト ---

@pytest.mark.parametrize(
    "file_content, rendered_template, expected_mode",
    [
        # 1. 新規作成ケース
        (None, "<start>Tpl</start>", "NEW"),
        # 2. テンプレートから変更なし -> 上書き
        ("<start>Tpl</start>", "<start>Tpl</start>", "OVERWRITE_TEMPLATE"),
        # 3. テンプレート部分が同じで、追記がある -> 追記
        ("<start>Tpl</start>\nUser Content", "<start>Tpl</start>", "APPEND"),
        # 4. テンプレート部分が更新されている -> 追記（マージ）
        ("<start>Old Tpl</start>\nUser Content", "<start>New Tpl</start>", "APPEND"),
        # 5. マーカーがない -> 回避
        ("No markers here", "<start>Tpl</start>", "RECOVER"),
    ]
)
def test_determine_mode(
    temp_project_dir, file_content, rendered_template, expected_mode
):
    """様々な条件下で `determine_mode` が正しいモードを返すかテスト"""
    report_path = temp_project_dir / "report.md"
    # `parametrize` から受け取った `file_content` に基づいてテストファイルを作成
    if file_content is not None:
        # マーカーのプレースホルダを実際の定数値に置換
        report_path.write_text(file_content.replace("<start>", TEMPLATE_START).replace("</start>", TEMPLATE_END), encoding="utf-8")
    
    # レンダリング済みテンプレートも同様に置換
    rendered = rendered_template.replace("<start>", TEMPLATE_START).replace("</start>", TEMPLATE_END)
    
    mode, _ = determine_mode(report_path, rendered)
    assert mode == expected_mode

# --- ファイル書き込みの統合テスト ---

def run_write_report_test(temp_project_dir, mode: Mode, original_content: str | None, rendered_template: str):
    """`write_report` のテストを実行するためのヘルパー関数"""
    report_path = temp_project_dir / "report.md"
    if original_content:
        report_path.write_text(original_content, encoding="utf-8")

    write_report(report_path, rendered_template, mode, original_content)
    return report_path

def test_write_report_new(temp_project_dir):
    """NEWモードでファイルが正しく作成されるか"""
    rendered = f"{TEMPLATE_START}\nNew Content\n{TEMPLATE_END}"
    report_path = run_write_report_test(temp_project_dir, "NEW", None, rendered)
    assert report_path.read_text(encoding="utf-8") == rendered

def test_write_report_overwrite(temp_project_dir):
    """OVERWRITE_TEMPLATEモードでファイルが正しく上書きされるか"""
    original = f"{TEMPLATE_START}\nOld Content\n{TEMPLATE_END}"
    rendered = f"{TEMPLATE_START}\nNew Content\n{TEMPLATE_END}"
    report_path = run_write_report_test(temp_project_dir, "OVERWRITE_TEMPLATE", original, rendered)
    assert report_path.read_text(encoding="utf-8") == rendered

def test_write_report_append(temp_project_dir):
    """APPENDモードで追記部分を保持したままテンプレートが更新されるか"""
    original = f"{TEMPLATE_START}\nOld Tpl\n{TEMPLATE_END}\n\nUser additions."
    rendered = f"{TEMPLATE_START}\nNew Tpl\n{TEMPLATE_END}"
    report_path = run_write_report_test(temp_project_dir, "APPEND", original, rendered)
    
    final_content = report_path.read_text(encoding="utf-8")
    assert "New Tpl" in final_content
    assert "User additions." in final_content
    # パッチファイルが作成されているかも確認
    assert (temp_project_dir / "report.patch").exists()

def test_write_report_recover(temp_project_dir):
    """RECOVERモードでファイルが退避されるか"""
    original = "No markers here."
    rendered = f"{TEMPLATE_START}\nContent\n{TEMPLATE_END}"
    report_path = run_write_report_test(temp_project_dir, "RECOVER", original, rendered)
    
    # 元のファイルは変更されない（今回は何もしない実装）
    assert report_path.read_text(encoding="utf-8") == original
    # 退避ファイルが作成されているかを確認
    recovered_files = list(temp_project_dir.glob("*_recovered_*.md"))
    assert len(recovered_files) == 1
    assert recovered_files[0].read_text(encoding="utf-8") == original

# --- main関数のE2Eテスト ---

@patch("sys.argv", ["report_generator.py", "--work-id", "20250709-001"])
def test_main_flow_new(mock_workorder, mock_template, temp_project_dir):
    """E2Eテスト: 新規作成フロー"""
    with patch("report_generator.PROJECT_ROOT", temp_project_dir):
        main()
        report_path = temp_project_dir / "workorders" / "reports" / "WO-20250709-001_report.md"
        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "テスト作業" in content

@patch("sys.argv", ["report_generator.py", "--work-id", "20250709-001", "--force"])
def test_main_flow_force_overwrite(mock_workorder, mock_template, temp_project_dir):
    """E2Eテスト: 強制上書きフロー"""
    report_path = temp_project_dir / "workorders" / "reports" / "WO-20250709-001_report.md"
    report_path.write_text("古いコンテンツ", encoding="utf-8")
    
    with patch("report_generator.PROJECT_ROOT", temp_project_dir):
        main()
        content = report_path.read_text(encoding="utf-8")
        assert "テスト作業" in content
        assert "古いコンテンツ" not in content

@patch("report_generator.FORCE_OVERWRITE_ENV", True)
@patch("sys.argv", ["report_generator.py", "--work-id", "20250709-001"])
def test_main_flow_force_overwrite_env(mock_workorder, mock_template, temp_project_dir):
    """E2Eテスト: 環境変数による強制上書きフロー"""
    report_path = temp_project_dir / "workorders" / "reports" / "WO-20250709-001_report.md"
    report_path.write_text("古いコンテンツ", encoding="utf-8")
    
    with patch("report_generator.PROJECT_ROOT", temp_project_dir):
        main()
        content = report_path.read_text(encoding="utf-8")
        assert "テスト作業" in content
        assert "古いコンテンツ" not in content