#!/bin/bash

# 引数のチェック
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <WorkOrder ID> <report file path>"
  exit 1
fi

WORKORDER_ID="$1"
REPORT_FILE_PATH="$2"

# レポート保存先ディレクトリ
REPORT_DIR="projects/solar_circuit/workorders/reports"

# レポートファイル名
REPORT_NAME="${WORKORDER_ID}_report.md"

# 保存先パス
DEST_PATH="${REPORT_DIR}/${REPORT_NAME}"

# ディレクトリが存在しない場合は作成
mkdir -p "${REPORT_DIR}"

# レポートファイルをコピー
cp "${REPORT_FILE_PATH}" "${DEST_PATH}"

echo "Report for WorkOrder ${WORKORDER_ID} saved to ${DEST_PATH}"
