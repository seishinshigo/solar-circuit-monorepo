import pytest
import tempfile
import shutil
import sys
from pathlib import Path

# scripts ディレクトリをモジュールパスに追加
sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

from report_generator import (
    determine_mode,
    render_template,
    TEMPLATE_START,
    TEMPLATE_END
)


@pytest.fixture
def tmp_report_file():
    temp_dir = tempfile.mkdtemp()
    report_path = Path(temp_dir) / "test_report.md"
    yield report_path
    shutil.rmtree(temp_dir)


def test_determine_mode_new(tmp_report_file):
    template = f"{TEMPLATE_START}\nSample Content\n{TEMPLATE_END}"
    mode = determine_mode(tmp_report_file, template)
    assert mode == "NEW"


def test_determine_mode_overwrite(tmp_report_file):
    template = f"{TEMPLATE_START}\nSame\n{TEMPLATE_END}"
    tmp_report_file.write_text(template, encoding="utf-8")
    mode = determine_mode(tmp_report_file, template)
    assert mode == "OVERWRITE_TEMPLATE"


def test_determine_mode_append(tmp_report_file):
    template = f"{TEMPLATE_START}\nStuff\n{TEMPLATE_END}"
    mixed = f"{template}\n\n追加内容"
    tmp_report_file.write_text(mixed, encoding="utf-8")
    mode = determine_mode(tmp_report_file, template)
    assert mode == "APPEND"


def test_determine_mode_recover(tmp_report_file):
    tmp_report_file.write_text("不明な内容", encoding="utf-8")
    template = f"{TEMPLATE_START}\nX\n{TEMPLATE_END}"
    mode = determine_mode(tmp_report_file, template)
    assert mode == "RECOVER"


def test_render_template_basic():
    template = "{{ workorder.title }}"
    result = render_template(template, {"title": "Hello World"})
    assert result.strip() == "Hello World"
