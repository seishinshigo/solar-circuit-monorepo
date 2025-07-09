---

## 📄 `docs/solar_circuit/04_workflow.md`（完全更新版 v1.1）

````markdown
# 作業ワークフロー規定

## ✅ 基本ルール

すべての作業は「作業依頼書（`WO-xxx.json`）」から始まり、「作業報告書（`WO-xxx_report.md`）」で終了します。

以下の順序を原則としてください：

1. 作業依頼書を受け取る（`projects/solar_circuit/workorders/incoming/` に配置）
2. `sc report create WO-XXX` にてレポートファイルを生成（`projects/solar_circuit/workorders/reports/` 内）
3. 実装計画を練る
 3.1. 【パス解決強化】各種パスはプロジェクトルートからの相対結合を行い、二重パス発生を防止
4. 作業を行う
5. Markdown レポートファイルを上書き
6. `git add` + `git commit` にて作業依頼書と報告書を含めて記録
7. `git push` して完了

## 🧰 自動生成されるレポートファイルについて

- コマンド：`sc report create WO-20250708-005`
- 保存場所：`projects/solar_circuit/workorders/reports/WO-20250708-005_report.md`
- 生成内容：共通テンプレート（`templates/report_template.md` に基づく）

## 🧠 作業報告ファイルの分類と処理

以下のようなケースに対応します：

| 状態 | 処理 |
|------|------|
| **報告書が存在しない** | テンプレートから自動生成（`sc report create`） |
| **報告書がテンプレート状態（未編集）** | 作業完了後、内容を上書きして記入 |
| **報告書がすでに記述されている** | 内容を追記／更新し、再コミット |
| **報告書の内容が作業と不整合** | ⚠️ 警告ログを残し、自動的に `_conflicted.md` を出力予定（今後対応） |
| **関連ドキュメントが見つからない場合**   | ⚠️ ログに警告を残しつつ、`related_docs` フィールドが指すパスを再試行（ルート結合） |

> ✨ 今後のアップデートで `sc report autosave` による差分検出・自動チェック処理が導入される予定です。

## 📌 補足：CLI での一貫作業（導入予定）

将来的には以下のようなワンライナーでも対応可能になります：

```bash
sc report autosave WO-20250708-005
````

これにより、テンプレート生成・差分チェック・報告書整形・Git ステージングまでが自動化されます。

---

```

---
