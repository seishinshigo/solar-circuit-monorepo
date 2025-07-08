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

import argparse
import difflib
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from jinja2 import Template

# --- 設定 ---
TEMPLATE_START = "<!-- TEMPLATE_START -->"
TEMPLATE_END = "<!-- TEMPLATE_END -->"
RECOVER_SUFFIX = "_recovered"
LOG_FILE = "projects/solar_circuit/logs/report_generator.log"

# ログディレクトリが存在しない場合は作成
Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

# --- ロガー設定 ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- モード定義 ---
Mode = Literal["NEW", "APPEND", "OVERWRITE_TEMPLATE", "RECOVER"]

# --- 環境変数読み込み ---
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")
FORCE_OVERWRITE = os.getenv("FORCE_OVERWRITE", "false").lower() == "true"


def load_workorder(work_id: str) -> dict:
    path = Path(f"projects/solar_circuit/workorders/incoming/WO-{work_id}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def extract_template(template_path: Path) -> str:
    with open(template_path, encoding="utf-8") as f:
        lines = f.readlines()
    start, end = None, None
    for i, line in enumerate(lines):
        if TEMPLATE_START in line:
            start = i
        elif TEMPLATE_END in line:
            end = i
    if start is not None and end is not None:
        return "".join(lines[start:end+1])
    raise ValueError("テンプレートにマーカーが不足しています")


def determine_mode(report_path: Path, rendered_str: str) -> Mode:
    if not report_path.exists():
        return "NEW"

    with open(report_path, encoding="utf-8") as f:
        content = f.read()

    if rendered_str.strip() == content.strip():
        return "OVERWRITE_TEMPLATE"
    elif TEMPLATE_START in content and TEMPLATE_END in content:
        return "APPEND"
    else:
        return "RECOVER"


def render_template(template_str: str, workorder: dict) -> str:
    template = Template(template_str)
    return template.render(workorder=workorder)


def write_report(report_path: Path, content: str, mode: Mode) -> None:
    if mode == "RECOVER":
        recover_path = report_path.with_name(report_path.stem + RECOVER_SUFFIX + ".md")
        shutil.copy(report_path, recover_path)
        logger.warning(f"不整合検出: 元ファイルを {recover_path} に退避しました")
        return

    if mode == "APPEND":
        with open(report_path, "a", encoding="utf-8") as f:
            f.write("\n\n")
            f.write(content)
    else:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)

    logger.info(f"{mode} モードでレポートを保存しました: {report_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-id", required=True, help="ワークオーダーID (例: 20250709-001)")
    parser.add_argument("--force", action="store_true", help="強制上書きモード")
    args = parser.parse_args()

    workorder = load_workorder(args.work_id)
    report_path = Path(f"projects/solar_circuit/workorders/reports/WO-{args.work_id}_report.md")
    template_path = Path("projects/solar_circuit/templates/report_template.md")
    template_str = extract_template(template_path)
    rendered = render_template(template_str, workorder)

    mode: Mode = determine_mode(report_path, rendered)

    if args.force or FORCE_OVERWRITE:
        logger.info("強制上書きモードを検出: OVERWRITE_TEMPLATE に切替")
        mode = "OVERWRITE_TEMPLATE"

    write_report(report_path, rendered, mode)
    logger.info(f"実行モード: {mode}")


if __name__ == "__main__":
    main()
