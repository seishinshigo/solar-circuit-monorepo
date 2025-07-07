---
title: Context Engineering Integration Guide
version: "0.1"
updated: 2025-07-07
-------------------

# Context Engineering Integration Guide

## 🛰️ 背景 / Background

[Context‑Engineering Intro](https://github.com/coleam00/context-engineering-intro) で示されたワークフローは、LLM に **明示的な文脈（Context）ファイル**を渡すことで出力品質と再現性を高める手法です。Solar Circuit も *Work‑Order* ベースで類似の仕組みを持つため、要素を移植すれば **少ない労力で大幅な精度向上** が見込めます。

## 🔍 取り込む要素

| # | 要素                             | 目的               | 優先度 |
| - | ------------------------------ | ---------------- | --- |
| 1 | **RULES.md**                   | AI 出力の統一ルール      | ★★★ |
| 2 | **INITIAL.md → PRP** フロー       | 機能要件を AI が誤読なく把握 | ★★★ |
| 3 | **examples/** ディレクトリ           | 例を通じて意図を共有       | ★★☆ |
| 4 | **Multi‑Agent PRP**            | 赤・青・緑 AI 連携      | ★★☆ |
| 5 | **Validation Gate** (`pytest`) | 自動品質保証           | ★★☆ |

## 🚀 実装ステップ

1. **RULES.md を追加**
   `projects/solar_circuit/docs/solar_circuit/RULES.md`

   * フォーマットは Markdown。
   * Work‑Order JSON に `"rules": ["docs/solar_circuit/RULES.md"]` を必須フィールドとして追加。
2. **INITIAL → PRP コマンド**
   `sc prp gen <INITIAL.md>` / `sc prp exec <PRP.md>` を Typer サブコマンドで実装し、Orchestrator に Work‑Order を POST。
3. **examples/** 追加
   monorepo 直下に `examples/` ディレクトリを作成。
   第一弾として既存 `sc hello` コマンドのコード & テストをコピー。
4. **Multi‑Agent フィールド拡張**
   Work‑Order Schema に `agents[]` と `phase_timeout` を入れる（Poetic AI 三体に展開）。
5. **Validation Gate 強化**
   Work‑Order に `success_cmd: "pytest"` をデフォルト設定。
   Worker は成功するまでリトライし、fail 時は `status: failure` とエラーログをレポート。

## 🏆 Quick Win

* **RULES.md** & `rules` フィールドだけ先に入れる（30 分）
* **examples/** に 1 サンプル追加（15 分）
* `sc prp gen` の雛形だけ CLI に追加（1 時間）

## ⏳ ロードマップ提案（計画書との対応）

| Week | Plan (01\_plan\_solo\_edition) | Context Eng. タスク      |
| ---- | ------------------------------ | --------------------- |
| 1‑2  | M1' Mini‑Orchestrator          | RULES.md / PRP Draft  |
| 3‑4  | Plugin SDK & Schema v1.1       | examples/ → Worker 拡張 |
| 5‑6  | Compose & Metrics              | Validation Gate 導入    |

> **リンク追加** : 01\_plan\_solo\_edition.md の末尾「関連ドキュメント」に `[Context Engineering ガイド](02_context_engineering.md)` を追記すると行き来がラクになります。

---

*初版* v0.1 (2025‑07‑07)  — 追加/修正歓迎 ✨
