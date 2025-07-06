# Solar Circuit
Bootstrap project.

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