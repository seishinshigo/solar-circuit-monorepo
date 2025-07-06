#!/usr/bin/env bash
set -e

base="projects/solar_circuit"
mkdir -p \
  "$base"/workorders/{incoming,reports} \
  "$base"/rounds \
  "$base"/logs/{test,orchestrator} \
  "$base"/collaboration/{design_docs,discussions}

# 空ディレクトリを Git 管理に載せるため .gitkeep を配置
find "$base"/workorders "$base"/rounds "$base"/logs "$base"/collaboration \
     -type d -exec touch {}/.gitkeep \;

echo "✅ Directory skeleton created."
