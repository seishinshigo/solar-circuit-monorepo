# Week 0 Improvements Plan – Test & Coverage Baseline

version: "0.1"
updated: 2025‑07‑07

---

## 🎯 ゴール

1. **テスト&カバレッジ基盤を整備**し、以降のフェーズで安心してリファクタできる土台を作る。
2. 既存カバレッジ 65 % → **75 % 以上** に引き上げ、CLI 基本コマンドの異常系もテスト対象に含める。

---

## 🗂 スコープ

| 含む                     | 理由                                         |
| ---------------------- | ------------------------------------------ |
| `.coveragerc` 導入       | レポートのノイズを除き、正確な % を把握する                    |
| `pytest.ini` 設定        | 共通オプション・マーカーを集中管理                          |
| **テスト構造再編** (`tests/`) | command 単位にファイル分離し保守性向上                    |
| **coverage badge** 追加  | README から品質メトリクスを視覚化                       |
| CI ワークフロー改訂            | `pytest --cov` ＆ `coverage xml` → badge 更新 |
| **含まない**               | 新機能・API 改修（Week 1 以降で実施）                   |

---

## 🗺 タイムライン & タスク詳細

| Day    | タスク                                                                              | 主要ファイル / コマンド                               |
| ------ | -------------------------------------------------------------------------------- | ------------------------------------------- |
| **D0** | ブランチ作成 `feat/week-0-checks`                                                      | `git switch -c feat/week-0-checks`          |
| **D0** | `.coveragerc` 雛形作成                                                               | exclude `__init__.py`, `tests/*`            |
| **D1** | `pytest.ini` 追加                                                                  | `addopts = -q --cov=projects/solar_circuit` |
| **D1** | 既存 `test_cli.py` を `tests/test_cli_hello.py` へ分割                                 | Typer CliRunner 使用例を追記                      |
| **D2** | 異常系テスト追加<br>– 引数不足時 `sc` エラー検証                                                   | `tests/test_cli_error.py`                   |
| **D2** | `tests/conftest.py` に共通フィクスチャ                                                    | Typer CliRunner インスタンス共有                    |
| **D3** | CI (`ci.yml`) を修正<br>– `pytest -q` → `pytest` (iniで -q含む)<br>– `coverage xml` 出力 | ワークフロー step 更新                              |
| **D3** | shields.io で **coverage badge** URL 追加                                           | README.md                                   |
| **D4** | ローカル実行 → CI 緑確認                                                                  | `pytest ; npx markdownlint-cli2 …`          |
| **D5** | PR 作成 → レビュー → Merge                                                             | `WO-YYYYMMDD-005`                           |

> **目標カバレッジ** : 75 % 超。 達しない場合は D4〜D5 でテストを追加。

---

## 🛠 実装ガイド

### 1. `.coveragerc`

```ini
[run]
branch = True
source = projects/solar_circuit/solar_circuit
omit =
    */__init__.py
    */tests/*
```

### 2. `pytest.ini`

```ini
[pytest]
addopts = -q --cov=projects/solar_circuit --cov-report=term-missing
markers =
    cli: CLI コマンドのテスト
```

### 3. 新規テストファイル例

```python
# tests/test_cli_error.py
import typer
from typer.testing import CliRunner
from solar_circuit.cli import app

runner = CliRunner()

def test_cli_no_args():
    result = runner.invoke(app, [])
    assert result.exit_code != 0
    assert "Usage" in result.output
```

### 4. CI Workflow 追記抜粋

```yaml
- name: 🧪 Run tests & coverage
  run: pytest

- name: 📊 Upload coverage to artifact (badge)
  run: |
    coverage xml
    cp coverage.xml ${{ github.workspace }}
```

### 5. README バッジ

```md
![coverage](https://img.shields.io/badge/coverage-75%25-brightgreen)
```

> 実数はコードカバレッジに合わせて CI で自動更新する GitHub Action を後続タスクで導入予定。

---

## 🎯 完了定義 (Definition of Done)

* [ ] `.coveragerc` & `pytest.ini` が main に存在
* [ ] tests ディレクトリが CLI コマンド単位で整理
* [ ] `pytest --cov` で 75 % 以上
* [ ] README に CI & coverage バッジが並ぶ
* [ ] CI ワークフローが coverage を計測し、緑で通過

---

初版 0.1 — 追加・修正は PR で対応します。

<!-- WO-20250707-005 -->