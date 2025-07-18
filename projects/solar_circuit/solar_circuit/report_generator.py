from __future__ import annotations

from pathlib import Path
import os
import json
import logging
import argparse
import difflib
import shutil
from datetime import datetime
from typing import Literal

from dotenv import load_dotenv
from jinja2 import Template


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

def find_project_root(marker: str = "pyproject.toml") -> Path:
    """マーカーファイルを探索してプロジェクトルートを見つける"""
    current_dir = Path(__file__).parent.resolve()
    while current_dir != current_dir.parent:
        if (current_dir / marker).exists():
            return current_dir
        current_dir = current_dir.parent
    raise FileNotFoundError(f"Project root with marker '{marker}' not found.")

PROJECT_ROOT = find_project_root()


# --- 設定 ---
TEMPLATE_START = "<!-- TEMPLATE_START -->"
TEMPLATE_END = "<!-- TEMPLATE_END -->"
RECOVER_SUFFIX = "_recovered"

# スクリプトの場所を基準に絶対パスを構築
# report_generator.py -> scripts -> solar_circuit (PROJECT_ROOT)
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
LOG_FILE = PROJECT_ROOT / "logs/report_generator.log"

# デバッグ用にPROJECT_ROOTを出力


# ログディレクトリが存在しない場合は作成
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# --- ロガー設定 ---
# 既存のハンドラをクリアしてから再設定
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

# --- モード定義 ---
Mode = Literal["NEW", "APPEND", "OVERWRITE_TEMPLATE", "RECOVER", "FORCED_OVERWRITE"]

# --- 環境変数読み込み ---
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
FORCE_OVERWRITE_ENV = os.getenv("FORCE_OVERWRITE", "false").lower() == "true"


def resolve_path(base_path: Path, relative_path_str: str | None) -> Path | None:
    """
    ベースパスと相対パスを賢く結合する。
    相対パスがベースパスの末尾部分と重複している場合、重複を避ける。
    例:
    base: /a/b/c
    rel:  b/c/d/e.txt
    -> /a/b/c/d/e.txt
    """
    if not relative_path_str:
        return None

    relative_path = Path(relative_path_str)
    if relative_path.is_absolute():
        return relative_path

    base_parts = base_path.parts
    rel_parts = relative_path.parts

    overlap_len = 0
    # base_partsの末尾とrel_partsの先頭がどれだけ重複しているか探す
    for i in range(min(len(base_parts), len(rel_parts)), 0, -1):
        if base_parts[-i:] == rel_parts[:i]:
            overlap_len = i
            break
    
    if overlap_len > 0:
        # 重複部分を除いたパスを結合
        new_rel_parts = rel_parts[overlap_len:]
        return base_path.joinpath(*new_rel_parts)

    # 重複がない場合はそのまま結合
    return base_path / relative_path


def load_workorder(work_id: str) -> dict:
    """指定されたワークオーダーIDのJSONファイルを読み込む"""
    # work_id が 'WO-' で始まっていない場合、プレフィックスを追加
    formatted_work_id = work_id if work_id.startswith("WO-") else f"WO-{work_id}"
    path = PROJECT_ROOT / f"workorders/incoming/{formatted_work_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"ワークオーダーファイルが見つかりません: {path}")
    with open(path, encoding="utf-8") as f:
        workorder_data = json.load(f)

    # 関連ドキュメントの内容を読み込み、workorder_dataに追加
    # detail_report_path を優先的に読み込む
    detail_report_path = resolve_path(PROJECT_ROOT, workorder_data.get("detail_report_path"))
    if detail_report_path:
        if detail_report_path.exists():
            with open(detail_report_path, encoding="utf-8") as f:
                workorder_data["summary_content"] = f.read()
        else:
            logger.warning(f"詳細レポートファイルが見つかりません: {detail_report_path}")
            workorder_data["summary_content"] = ""
    else:
        # 既存の関連ドキュメントの読み込みロジック
        related_docs_path_str = workorder_data.get("file_path") or workorder_data.get("metadata", {}).get("related_docs")
        related_docs_path = resolve_path(PROJECT_ROOT, related_docs_path_str)
        if related_docs_path:
            if related_docs_path.exists():
                with open(related_docs_path, encoding="utf-8") as f:
                    workorder_data["summary_content"] = f.read()
            else:
                logger.warning(f"関連ドキュメントが見つかりません: {related_docs_path}")
                workorder_data["summary_content"] = ""
        else:
            workorder_data["summary_content"] = ""

    workorder_data.setdefault("metadata", {})

    # 常に正規化されたIDを返すようにする
    workorder_data["id"] = formatted_work_id

    return workorder_data


def extract_template_from_file(template_path: Path) -> str:
    """テンプレートファイルからマーカー間の部分を抽出する"""
    with open(template_path, encoding="utf-8") as f:
        content = f.read()
    
    start_idx = content.find(TEMPLATE_START)
    end_idx = content.find(TEMPLATE_END)

    if start_idx != -1 and end_idx != -1:
        return content[start_idx : end_idx + len(TEMPLATE_END)]
    raise ValueError(f"テンプレートにマーカーが不足しています: {template_path}")


def extract_part_from_content(content: str, start_marker: str, end_marker: str) -> str | None:
    """文字列からマーカー間の部分を抽出する"""
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx != -1 and end_idx != -1:
        return content[start_idx : end_idx + len(end_marker)]
    return None


def determine_mode(report_path: Path, rendered_template: str) -> tuple[Mode, str | None]:
    """レポートの状態に基づいて実行モードを決定する"""
    if not report_path.exists():
        return "NEW", None

    with open(report_path, encoding="utf-8") as f:
        original_content = f.read()

    existing_template_part = extract_part_from_content(original_content, TEMPLATE_START, TEMPLATE_END)

    if existing_template_part is None:
        return "RECOVER", original_content

    # 空白と改行を正規化して比較
    rendered_norm = "\n".join(line.strip() for line in rendered_template.strip().splitlines())
    existing_norm = "\n".join(line.strip() for line in existing_template_part.strip().splitlines())
    original_norm = "\n".join(line.strip() for line in original_content.strip().splitlines())

    if rendered_norm == existing_norm:
        if original_norm == existing_norm:
            return "OVERWRITE_TEMPLATE", original_content
        else:
            return "APPEND", original_content
    else:
        # テンプレートが更新されているが、ユーザーの追記もある可能性がある
        return "APPEND", original_content


from jinja2 import Environment, FileSystemLoader

def render_template(template_str: str, workorder: dict) -> str:
    """Jinja2テンプレートをレンダリングする"""
    # テンプレート文字列から直接ロードするのではなく、Environmentを使用
    env = Environment(loader=FileSystemLoader(PROJECT_ROOT / "templates"), autoescape=False)
    template = env.from_string(template_str)
    return template.render(workorder=workorder)


def write_report(report_path: Path, rendered_template: str, mode: Mode, original_content: str | None) -> None:
    """決定されたモードに従ってレポートファイルを書き込む"""
    if mode == "RECOVER":
        if original_content is None: return
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        recover_path = report_path.with_name(f"{report_path.stem}{RECOVER_SUFFIX}_{timestamp}.md")
        # shutil.copyだとパーミッションエラーになることがあるので、読み書きで対応
        with open(recover_path, "w", encoding="utf-8") as f:
            f.write(original_content)
        logger.warning(f"不整合検出: 元ファイルを {recover_path} に退避しました")
        return

    final_content = ""
    if mode == "APPEND":
        if original_content is None:
            logger.error("APPENDモードエラー: オリジナルコンテンツがありません。")
            return
        
        existing_template_part = extract_part_from_content(original_content, TEMPLATE_START, TEMPLATE_END)
        if existing_template_part is None:
            logger.error("APPENDモードエラー: 既存のテンプレートマーカーが見つかりません。")
            # この場合、RECOVERモードで退避済みのはずだが念のため
            final_content = rendered_template
        else:
            # 既存のテンプレート部分を新しいレンダリング結果で置き換える
            final_content = original_content.replace(existing_template_part, rendered_template)

        # 差分パッチを作成
        diff = difflib.unified_diff(
            original_content.splitlines(keepends=True),
            final_content.splitlines(keepends=True),
            fromfile=f"a/{report_path.name}",
            tofile=f"b/{report_path.name}",
        )
        patch_path = report_path.with_suffix(".patch")
        with open(patch_path, "w", encoding="utf-8") as f:
            f.writelines(diff)
        logger.info(f"差分パッチを保存しました: {patch_path}")

    else:  # NEW, OVERWRITE_TEMPLATE, FORCED_OVERWRITE
        final_content = rendered_template

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(final_content)

    logger.info(f"{mode} モードでレポートを保存しました: {report_path}")


import re

def clean_summary_content(md_content: str) -> str:
    # 全てのMarkdown見出しレベルを1つ下げる (例: #→##, ##→###)
    cleaned_content = re.sub(r'^(#{1,6})\s', r'#\1 ', md_content, flags=re.MULTILINE)
    return cleaned_content.strip()

def generate_report_from_work_id(work_id: str, force: bool = False):
    """指定されたワークオーダーIDに基づいてレポートを生成・更新する"""
    try:
        workorder = load_workorder(work_id)
        report_path = PROJECT_ROOT / f"workorders/reports/{workorder['id']}_report.md"
        template_path = PROJECT_ROOT / "templates/report_template.md"

        # summary_content の見出しレベルを調整
        if "summary_content" in workorder and workorder["summary_content"]:
            workorder["summary_content"] = clean_summary_content(workorder["summary_content"])

        template_str = extract_template_from_file(template_path)
        rendered_template = render_template(template_str, workorder)

        mode, original_content = determine_mode(report_path, rendered_template)
        final_mode: Mode = mode

        is_forced = force or FORCE_OVERWRITE_ENV
        if is_forced:
            final_mode = "FORCED_OVERWRITE"
            logger.info(f"強制上書きモードを検出: {mode} -> {final_mode} に切替")
        
        write_report(report_path, rendered_template, final_mode, original_content)
        logger.info(f"実行モード: {final_mode}")

    except FileNotFoundError as e:
        logger.error(f"ファイルが見つかりません: {e}")
        raise
    except ValueError as e:
        logger.error(f"値エラー: {e}")
        raise
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}", exc_info=True)
        raise


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="ワークオーダーに基づいて作業報告書を自動生成・更新します。")
    parser.add_argument("--work-id", required=True, help="ワークオーダーID (例: 20250709-001)")
    parser.add_argument("--force", action="store_true", help="強制上書きモード。FORCE_OVERWRITE環境変数でも設定可。")
    args = parser.parse_args()
    generate_report_from_work_id(args.work_id, args.force)


if __name__ == "__main__":
    main()
