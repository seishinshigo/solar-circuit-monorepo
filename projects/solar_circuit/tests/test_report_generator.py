#!/usr/bin/env python3
"""
report_generator.py
-------------------
CLI スクリプト: ワークオーダー JSON と Markdown テンプレートを読み込み、
既存レポートの状態に応じて
    • 新規生成 (NEW)
    • 追記 (APPEND)
    • テンプレ上書き (OVERWRITE_TEMPLATE)
    • 回避／退避 (RECOVER)
を自動で実行し、Jinja2 によってテンプレートを動的にレンダリングし、
実行結果をログに記録します。
"""

from __future__ import annotations

import os
import json
import logging
import argparse
import difflib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

# --- プロジェクトルート設定 ---
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", SCRIPT_DIR.parent)).resolve()

# --- ログファイル設定 ---
LOG_FILE = PROJECT_ROOT / "logs" / "report_generator.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# --- ロガー設定 ---
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- モード定義とマーカー ---
Mode = Literal["NEW", "APPEND", "OVERWRITE_TEMPLATE", "RECOVER", "FORCED_OVERWRITE"]
TEMPLATE_START = "<!-- TEMPLATE_START -->"
TEMPLATE_END   = "<!-- TEMPLATE_END -->"
RECOVER_SUFFIX = "_recovered"

# --- 環境変数読み込み ---
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
FORCE_OVERWRITE_ENV = os.getenv("FORCE_OVERWRITE", "false").lower() == "true"


def load_workorder(work_id: str) -> dict:
    """指定されたワークオーダーIDのJSONファイルを読み込む"""
    formatted = work_id if work_id.startswith("WO-") else f"WO-{work_id}"
    path = PROJECT_ROOT / f"workorders/incoming/{formatted}.json"
    if not path.exists():
        raise FileNotFoundError(f"ワークオーダーファイルが見つかりません: {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    related = data.get("file_path") or data.get("metadata", {}).get("related_docs")
    if related:
        full = PROJECT_ROOT / related
        if full.exists():
            data["summary_content"] = full.read_text(encoding="utf-8")
        else:
            logger.warning(f"関連ドキュメントが見つかりません: {full}")
            data["summary_content"] = ""
    else:
        data["summary_content"] = ""

    data.setdefault("metadata", {})
    return data


def extract_template_from_file(template_path: Path) -> str:
    """テンプレートファイルからマーカー間の部分を抽出する"""
    content = template_path.read_text(encoding="utf-8")
    start = content.find(TEMPLATE_START)
    end   = content.find(TEMPLATE_END)
    if start != -1 and end != -1:
        return content[start: end + len(TEMPLATE_END)]
    raise ValueError(f"テンプレートにマーカーが不足しています: {template_path}")


def extract_part_from_content(content: str, start_marker: str, end_marker: str) -> str | None:
    """文字列からマーカー間の部分を抽出する"""
    s = content.find(start_marker)
    e = content.find(end_marker)
    if s != -1 and e != -1:
        return content[s: e + len(end_marker)]
    return None


def determine_mode(report_path: Path, rendered: str) -> tuple[Mode, str | None]:
    """レポートの状態に基づいて実行モードを決定"""
    if not report_path.exists():
        return "NEW", None
    original = report_path.read_text(encoding="utf-8")
    existing = extract_part_from_content(original, TEMPLATE_START, TEMPLATE_END)
    if existing is None:
        return "RECOVER", original
    norm_new = "\n".join(line.strip() for line in rendered.strip().splitlines())
    norm_exist = "\n".join(line.strip() for line in existing.strip().splitlines())
    norm_orig = "\n".join(line.strip() for line in original.strip().splitlines())
    if norm_new == norm_exist:
        if norm_orig == norm_exist:
            return "OVERWRITE_TEMPLATE", original
        return "APPEND", original
    return "APPEND", original


def render_template(template_str: str, workorder: dict) -> str:
    """Jinja2テンプレートをレンダリング"""
    env = Environment(loader=FileSystemLoader(PROJECT_ROOT / "templates"), autoescape=False)
    tmpl = env.from_string(template_str)
    return tmpl.render(workorder=workorder)


def write_report(report_path: Path, rendered: str, mode: Mode, original: str | None) -> None:
    """モードに従ってレポートを書き込む"""
    if mode == "RECOVER":
        if original is None:
            return
        ts = datetime.now().strftime("%Y%m%dT%H%M%S")
        recover = report_path.with_name(f"{report_path.stem}{RECOVER_SUFFIX}_{ts}.md")
        recover.write_text(original, encoding="utf-8")
        logger.warning(f"不整合検出: 元ファイルを {recover} に退避しました")
        return
    if mode == "APPEND":
        original = original or ""
        part = extract_part_from_content(original, TEMPLATE_START, TEMPLATE_END)
        if part:
            final = original.replace(part, rendered)
            diff = difflib.unified_diff(
                original.splitlines(keepends=True),
                final.splitlines(keepends=True),
                fromfile=f"a/{report_path.name}", tofile=f"b/{report_path.name}"
            )
            (report_path.with_suffix('.patch')).write_text(''.join(diff), encoding="utf-8")
        else:
            final = rendered
    else:
        final = rendered
    report_path.write_text(final, encoding="utf-8")
    logger.info(f"{mode} モードでレポートを保存しました: {report_path}")


def clean_summary_content(md: str) -> str:
    cleaned = __import__('re').sub(r'^(#{1,6})\s', r'#\1 ', md, flags=__import__('re').MULTILINE)
    return cleaned.strip()


def generate_report_from_work_id(work_id: str, force: bool = False):
    try:
        wo = load_workorder(work_id)
        rpt = PROJECT_ROOT / f"workorders/reports/{work_id}_report.md"
        tpl = PROJECT_ROOT / "templates/report_template.md"
        if wo.get("summary_content"):
            wo["summary_content"] = clean_summary_content(wo["summary_content"])
        tpl_str = extract_template_from_file(tpl)
        rendered = render_template(tpl_str, wo)
        mode, original = determine_mode(rpt, rendered)
        final_mode = "FORCED_OVERWRITE" if (force or FORCE_OVERWRITE_ENV) else mode
        if final_mode == "FORCED_OVERWRITE":
            logger.info(f"強制上書きモードを検出: {mode} -> {final_mode} に切替")
        write_report(rpt, rendered, final_mode, original)
        logger.info(f"実行モード: {final_mode}")
    except Exception as e:
        logger.error(f"エラー: {e}", exc_info=True)
        raise


def main():
    parser = argparse.ArgumentParser(description="作業報告書を自動生成・更新します。")
    parser.add_argument("--work-id", required=True, help="ワークオーダーID (例: 20250709-001)")
    parser.add_argument("--force", action="store_true", help="強制上書きモード")
    args = parser.parse_args()
    generate_report_from_work_id(args.work_id, args.force)

if __name__ == "__main__":
    main()
