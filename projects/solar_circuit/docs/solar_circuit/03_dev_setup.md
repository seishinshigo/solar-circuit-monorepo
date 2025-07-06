# 開発環境セットアップ

## Work-Order およびレポートの命名規約

Work-Order ファイルとそれに対応するレポートファイルは、以下の命名規約に従ってください。

- **Work-Order ファイル**: `incoming/{ID}.json`
  - 例: `incoming/wo-20240710-001.json`

- **レポートファイル**: `reports/{ID}_report.md`
  - 例: `reports/wo-20240710-001_report.md`

`{ID}` は Work-Order の一意な識別子であり、Work-Order ファイルとレポートファイルで共通して使用されます。

## レポート保存フロー

作業報告書は、コミット前に `workorders/reports/` ディレクトリに自動的に保存されるように設定されています。以下の手順でレポートを保存してください。

```bash
python -m solar_circuit.cli report save <WorkOrder ID> <レポートファイルのパス>
# 例:
# python -m solar_circuit.cli report save wo-20240710-001 path/to/your/report.md
```

このコマンドを実行すると、指定されたレポートファイルが `workorders/reports/{WorkOrder ID}_report.md` として保存されます。コミット時には、このディレクトリにレポートファイルが存在することがチェックされます。

## CI ルール

CI ワークフローでは、以下のルールが適用されます。

- **Work-Order レポートの存在チェック**: `main` ブランチへの `push` または `pull_request` が `closed` された際に、関連する Work-Order ID のレポートファイル (`workorders/reports/{WO_ID}_report.md`) が存在するかどうかをチェックします。レポートが存在しない場合、CI は失敗します。
