---

### 🇯🇵 日本語対応追記版 `README.md`

````markdown
# Solar Circuit System（ソーラー・サーキット・システム）

このリポジトリには、**Solar Circuit** プロジェクトの中核コンポーネントが含まれています。

- 🎛️ `solar_circuit/cli.py`: 軽量CLI（Typer使用）
- 🧠 `orchestrator/`: タスク自動化とエージェント協調の実行ロジック
- 🧪 `tests/`: `pytest` によるテストスイート（カバレッジ対応）

---

## 🧪 テスト方法

```bash
pytest --cov=projects/solar_circuit
````

---

## 📦 開発用インストール（編集可能モード）

```bash
pip install -e projects/solar_circuit
```

---

## 🧾 開発依存パッケージのインストール

```bash
pip install -r projects/solar_circuit/requirements-dev.txt
```

---

## 📁 ワークフロー（GitHub Actions）

このプロジェクトでは、以下の GitHub Actions が設定されています：

* **CI (`ci.yml`)：**
  `main` ブランチへの push および pull request に対して、`projects/solar_circuit/` 以下のコードに対して `pytest` テスト（カバレッジ付き）を実行します。

* **レポート自動生成 (`report-autosave.yml`)：**
  新しい作業依頼ファイル（例：`WO-20250708-001.json`）が `projects/solar_circuit/workorders/incoming/` ディレクトリに追加された際、自動的に対応する作業報告書テンプレート（例：`WO-20250708-001_report.md`）を `reports/` ディレクトリに生成します。
　なお、新たに `detail_report_path` フィールドを導入し、より詳細な報告書Markdownを `collaboration/detailed_reports/` 配下から挿入できるよう拡張済みです。

---

## 📝 作業報告書（レポート）の作成と提出フロー

作業終了後、レポートを記述して `main` ブランチに push すると、`report-autosave.yml` により自動的に処理されます。
※ レポート生成時に `clean_summary_content` 関数でMarkdown見出しを１レベル下げる処理を行い、テンプレートの階層構造と競合しないよう自動調整します。

### 作業報告書の作成

以下のコマンドで、指定した作業依頼IDに対応するレポートのスケルトンを生成します：

```bash
sc report create WO-YYYYMMDD-XXX
```

例：`WO-20250708-001`

このコマンドは、`projects/solar_circuit/workorders/reports/` に `WO-YYYYMMDD-XXX_report.md` を作成します。

### レポートテンプレートの位置

レポートは以下のテンプレートをもとに作成されます：

```
projects/solar_circuit/templates/report_template.md
```

### レポートの提出方法

作業終了後、レポートを記述して `main` ブランチに push すると、`report-autosave.yml` により自動的に処理されます。

**提出の順序ルール：**

1. 作業が完了したら、必ずレポートを記述してください。
2. レポートファイルが `reports/` にある状態で `git commit`・`git push` を実行します。
3. レポートが確認され、自動保存アクションがトリガーされます。

---

## 📚 ドキュメント

詳細な開発フローは [`docs/solar_circuit/04_workflow.md`](solar_circuit/04_workflow.md) に記載されています。

```

---
