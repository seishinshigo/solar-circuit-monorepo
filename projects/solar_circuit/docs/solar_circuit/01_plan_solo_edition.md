---
title: ソロ開発エディション開発計画書
version: "1.0"
updated: 2025-07-07
---
# ソーラーサーキット “ソロ開発エディション” 開発計画書 v1.0 (2025‑07‑07)

---

## 1️⃣ 目的と背景

Blue Print で示された M0–M6 の段階的構築モデルを、**個人開発でも無理なく完走できる 8 週間ロードマップ**に落とし込む。クラウド常駐を前提とした K8s/Linkerd/NATS などの重装備は後回しにし、まずは *ローカル + Docker Compose* で完結する最小構成を確立する。fileciteturn3file0

## 2️⃣ スコープ

| 含む                                   | 理由                                             |
| ------------------------------------ | ---------------------------------------------- |
| CLI (sc) 現行機能維持                      | 既存ワークフローを壊さずに着手可                               |
| Mini‑Orchestrator (FastAPI)          | Round 状態遷移と REST API を早期に確立                    |
| Worker Plugin SDK (echo 雛形)          | 後続拡張の接点を先に固める fileciteturn3file4            |
| Work‑Order / Report JSON Schema v1.1 | すべての I/O をこれに合わせる fileciteturn3file3        |
| 基本メトリクス (Prometheus)                 | 後付けが難しいので最初から導入                                |
| Docker Compose 一式                    | 単一マシンで完結・再現性◎                                  |
| **含まない**                             | K8s, Linkerd, OPA, SOC2 監査, Terraform 自動 apply |

## 3️⃣ SMART 目標

| No | 目標                           | 指標                                            | 期日         |
| -- | ---------------------------- | --------------------------------------------- | ---------- |
| G1 | CLI M0 が lint/pytest グリーンで動作 | CI success ≥ 95 %                             | 2025‑07‑13 |
| G2 | Mini‑Orchestrator PoC 起動     | `POST /workorders` で 200, DB insert 1 行       | 2025‑07‑20 |
| G3 | Worker echo Plugin 動作        | `/reports/{id}` が `status: success` を返却       | 2025‑08‑03 |
| G4 | Docker Compose 1 コマンド起動      | `docker compose up` で Orchestrator/Worker が疎通 | 2025‑08‑17 |

## 4️⃣ マイルストーン & タイムライン

| 週                    | コードネーム                           | 主な成果物                                                                |
| -------------------- | -------------------------------- | -------------------------------------------------------------------- |
| Week 0 (7/7‑7/13)    | **M0 確認**                        | CLI が単独で Round を走らせる (b326140 基準)                                    |
| Week 1‑2 (7/14‑7/27) | **M1′ Mini‑Orchestrator**        | FastAPI `main.py`, SQLModel `Round` table, SQLite DB                 |
| Week 3‑4 (7/28‑8/10) | **M2′ Plugin SDK + Schema v1.1** | `workers/default/handler.py`, JSON Schema v1.1, `sc commit` → REST 化 |
| Week 5‑6 (8/11‑8/24) | **M3′ Compose & Metrics**        | `docker-compose.yml`, `/metrics` endpoint, Prometheus scrape         |
| Week 7‑8 (8/25‑9/07) | **M4′ オプション**                    | Postgres 移行 + GitHub PR Bot (任意)                                     |

> **命名規則**: “M1′” のように *プライム* を付け、Blue Print M1 の縮小版であることを示す。

## 5️⃣ タスク詳細 (抜粋)

### 5.1 Week 1‑2: Mini‑Orchestrator

* `orchestrator/main.py` に FastAPI 雛形 20 行
* `models.py` に `Round(id,status,created_at)`
* `uvicorn` 起動 & curl で手動テスト
* pytest: `/workorders` 正常系 + 異常系 1 件

### 5.2 Week 3‑4: Plugin SDK & Schema v1.1

* `shared_libs/schemas/gemini.workorder@1.json` 更新 (phase\_timeout / agents 追加) fileciteturn3file3
* `workers/default/handler.py` に echo 実装 (`@hook handle(order)`) fileciteturn3file4
* `sc commit` を httpx 経由で Orchestrator POST に置換

### 5.3 Week 5‑6: Compose & Metrics

* `docker-compose.yml`: orchestrator, worker, prometheus, minio
* Orchestrator に `round_total` & `token_usage_total` Counter 追加 (Prom client)
* README に `docker compose up` 手順追記

## 6️⃣ 技術スタック

| レイヤ           | 技術                                         | バージョン/備考    |
| ------------- | ------------------------------------------ | ----------- |
| Orchestrator  | FastAPI + SQLModel                         | Python 3.12 |
| DB            | SQLite → Postgres (移行予定)                   |             |
| Storage       | ローカル FS → MinIO (S3互換)                     |             |
| Worker SDK    | entry\_points plugin fileciteturn3file4 |             |
| CLI           | Typer + httpx                              |             |
| Observability | Prometheus (metrics) / JSON Lines (logs)   |             |

## 7️⃣ 開発ワークフロー & CI

1. `git switch -c feat/wo-<date>-<slug>`
2. `sc commit "feat: …"` → Git hook で WO\_ID 挿入
3. Push → GitHub Actions `ci.yml` + `report-autosave.yml` 実行
4. PR レビュー後 merge

CI テンプレは資料 01 に従う fileciteturn3file17。

## 8️⃣ スキーマ指針

* `phase_timeout` (default: coding 30 m / testing 45 m)
* `agents[]` で Multi‑Agent 指定 (将来拡張) fileciteturn3file3
* バージョンはファイル末尾 `@1` を採用

## 9️⃣ ログ & メトリクス

* **ログ**: `logs/{date}.jsonl` に workorder\_id 含む行を書き出し (jq で grep 可)
* **メトリクス**: `/metrics` → Prometheus → Grafana (任意)

## 🔟 リスク & 対応策

| リスク                    | 対応                                                      |
| ---------------------- | ------------------------------------------------------- |
| SQLite → Postgres 移行ミス | Alembic autogenerate + ステージ環境先行適用 fileciteturn3file9 |
| モデル API レート制限          | Backoff + Queue 長監視 (Prom alert)                        |
| ワンオフプラグインの破壊的変更        | SDK シグネチャ固定 & SemVer 適用                                 |

## 11️⃣ 次のステップ

1. **本計画書をユーザーが確認・承認**
2. Week 0 作業 (CLI M0 テスト) 着手
3. `orchestrator/main.py` 雛形 PR を作成

---

> **更新履歴**
> 2025‑07‑07 v1.0 初版作成
