# Work-Order: WO-20250707-006

## 📄 報告書品質改善タスク – 作業指示書

version: "0.1"
date: 2025-07-07

---

## 🎯 目的

作業報告書（例：`WO-20250707-005_report.md`）の品質を向上させ、以後の開発サイクルにおいて **再利用性・可読性・自動処理耐性のある報告書テンプレート** を確立する。報告内容の粒度・ファイルパス明示・成果物リストの精緻化を行い、読み手・レビューア・自動CIにとって最適な構成とする。

---

## 📌 スコープ

| 含む                    | 理由                          |
| --------------------- | --------------------------- |
| Markdown形式の作業報告書構成改善  | 人間とAIの両方が扱いやすくするため          |
| ファイルパス・成果物リストの形式統一    | レビューや自動リンク化に有効              |
| CIやコードに対する成果物のマッピング記述 | 再検証・トレーサビリティ向上              |
| **含まない**              | CLIやCI自体の機能追加・処理ロジック変更（別WO） |

---

## ✅ 作業目標

| No | 項目                                                          | 内容                                                           |
| -- | ----------------------------------------------------------- | ------------------------------------------------------------ |
| 1  | テンプレート雛形作成                                                  | `templates/report_template.md` を新設し、各章構成を標準化（概要・作業内容・結果・DoD） |
| 2  | ファイルパスの明示                                                   | すべての作成・変更ファイルに絶対パス or プロジェクト相対パスを明記                          |
| 3  | 成果物リスト導入                                                    | 「この報告書で作成／更新された成果物一覧」セクションを導入                                |
| 4  | 脚注または補足形式によるバッジリンク補完                                        | README記載のCI/coverageバッジなど、実際のURLを明示                          |
| 5  | テンプレートに識別メタ (`WO-ID`, `related_docs`, `success_cmd`) を埋め込み可 | 将来的なCI or Gemini CLIとの自動連携のため                                |

---

## 🛠 実施ステップ

1. `WO-20250707-005_report.md` を対象に改善点を抽出し、差分案を作成
2. `templates/report_template.md` を新規作成し、構成・書式を標準化
3. 改善済み `WO-20250707-005_report.md` を `v1.1` として保存し、両方の比較ができるようにする
4. `README.md` にテンプレート導入方針を簡易記述
5. markdownlint ルールとの整合性（MD025, MD032 等）を維持した状態で最終確認

---

## 🏁 完了定義 (Definition of Done)

* [ ] `templates/report_template.md` が追加され、章構成・表記ルールが含まれている
* [ ] `WO-20250707-005_report.md` に対して改善バージョンが保存されている（例: `..._report_v1.1.md`）
* [ ] すべてのファイルパスがプロジェクト内参照形式で明記されている
* [ ] DoD に準拠したチェックリストが明記されている
* [ ] CI・badge・カバレッジに関連する成果物が脚注付きで記録されている

---

## 🔖 メタ情報（機械処理用）

```json
{
  "id": "WO-20250707-006",
  "title": "作業報告書テンプレートと品質基準整備",
  "kind": "design",
  "phase": "documentation",
  "related_docs": [
    "workorders/reports/WO-20250707-005_report.md",
    "docs/solar_circuit/01_plan_solo_edition.md"
  ],
  "success_cmd": "npx markdownlint-cli2 'projects/**/*.md'",
  "deadline": "2025-07-10"
}
```

---

初版 v0.1 — 提案ベースのため、修正・追加指示を受け入れ可能。
