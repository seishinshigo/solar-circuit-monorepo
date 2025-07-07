# Solar Circuit

[![solar-circuit-ci](https://github.com/seishinshigo/solar-circuit-monorepo/actions/workflows/ci.yml/badge.svg)](https://github.com/seishinshigo/solar-circuit-monorepo/actions/workflows/ci.yml)

Bootstrap project.

## 関連ドキュメント
- [ソロ開発エディション開発計画書](01_plan_solo_edition.md)


## ローカル起動方法

FastAPI アプリケーションをローカルで起動するには、以下のコマンドを使用します。

```bash
uvicorn solar_circuit.orchestrator.main:app --reload
```

これにより、開発サーバーが起動し、コードの変更が自動的に反映されます。

## レポートの保存

作業報告書を `workorders/reports/` ディレクトリに保存するには、以下のコマンドを使用します。

```bash
python -m solar_circuit.cli report save <WorkOrder ID> <レポートファイルのパス>
# 例:
# python -m solar_circuit.cli report save wo-20240710-001 path/to/your/report.md
```

## Git フックの有効化

コミット前にレポートの保存を強制する `pre-commit` フックを有効にするには、以下のコマンドを実行してください。

```bash
git config core.hooksPath .githooks
```

## CI ルール

CI ワークフローでは、以下のルールが適用されます。

- **Work-Order レポートの存在チェック**: `main` ブランチへの `push` または `pull_request` が `closed` された際に、関連する Work-Order ID のレポートファイル (`workorders/reports/{WO_ID}_report.md`) が存在するかどうかをチェックします。レポートが存在しない場合、CI は失敗します。

### CI ログ例

#### 成功例

```
Work-Order report for wo-20240710-001 found.
```

#### 失敗例

```
Error: Missing Work-Order report for wo-20240710-001. Expected at projects/solar_circuit/workorders/reports/wo-20240710-001_report.md
```