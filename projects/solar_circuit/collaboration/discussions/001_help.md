現在の問題を再整理し、確実な解決策を具体的に示します。

---

## 🔴 問題の本質（再確認）

Gemini CLI によるレポート生成で、以下の2つの問題が発生しています。

### 問題1：Markdown構造の競合

* `summary_content` に挿入されたMarkdownに見出し（`#`）が含まれるため、
* テンプレート内の既存の見出しと階層構造が崩れてしまい、最終的なMarkdownファイルで意図した内容が表示されない。

### 具体的な例：

```markdown
## 2. 作業内容

実施した作業の詳細を記述します。

# チャット依頼のワークオーダー化（競合するH1見出し）

チャット欄で依頼された作業を...
```

### 問題2：作業ループの再発

* CLIコマンドの自動コミット処理（`sc commit`）で `git add -A` を実行することで、過去に生成された未ステージングのファイルが巻き込まれる問題が再発している。

---

## 🟢 問題の解決方法（具体的対処）

### 🚩 解決策1：Markdownの構造的競合の回避

#### 方法A（推奨）：レポート生成時に見出しを削除する処理を追加

`report_generator.py` の中で、`summary_content` の先頭にある見出しを削除してから挿入します。

```python
import re

def clean_summary_content(md_content: str) -> str:
    # 先頭のMarkdown見出しを削除（H1〜H6対応）
    cleaned_content = re.sub(r'^\s*#{1,6}\s.*\n+', '', md_content, count=1, flags=re.MULTILINE)
    return cleaned_content.strip()
```

**使い方（render\_template内）**：

```python
# レンダリング前にsummary_contentをクリーンアップ
workorder["summary_content"] = clean_summary_content(workorder["summary_content"])
```

これにより、生成されるMarkdownは次のように競合を回避します：

```markdown
## 2. 作業内容

実施した作業の詳細を記述します。

チャット欄で依頼された作業を、テンプレートを用いてワークオーダーとして受理し...
```

---

#### 方法B（代替案）：テンプレート側を変更する

`report_template.md` で見出しを許容する構造に変更：

```markdown
## 2. 作業内容

{{ workorder.summary_content }}

### 2.1. ワークオーダーのステップ
```

上記方法Aと併用するとより安定します。

---

### 🚩 解決策2：「作業ループ」問題の根本修正

CLIのコミットコマンドを厳密に再確認します。
具体的には `cli.py` の `sc commit` コマンドを、以下のコードで完全に書き換えてください。

```python
# cli.py 内の commit コマンドの修正例（Python・Typerベースの場合）

@app.command()
def commit(wo_id: str = typer.Option(None, help="ワークオーダーID")):
    if not wo_id:
        typer.echo("WO-IDを指定してください")
        raise typer.Exit(code=1)

    wo_json = f"projects/solar_circuit/workorders/incoming/{wo_id}.json"
    wo_report = f"projects/solar_circuit/workorders/reports/{wo_id}_report.md"
    wo_design_doc = f"projects/solar_circuit/collaboration/design_docs/{wo_id}_workorder.md"

    # 特定のファイルだけをステージング
    run(f"git add {wo_json} {wo_report} {wo_design_doc}", shell=True)

    # コミット処理（変更対象を明示）
    run(f"git commit -m 'feat: {wo_id} の作業をコミットしました'", shell=True)
```

* `git add -A` を**絶対に実行しない**ようにします。

---

## 📋 対応のまとめ（必須作業リスト）

以下を順次実行することで、問題を完全に解決できます：

| 項目 | 内容                                       | 対応 |
| -- | ---------------------------------------- | -- |
| 1  | 不要ファイルの除去（再度）                            | ✅  |
| 2  | `report_generator.py` にMarkdown見出し削除処理追加 | ✅  |
| 3  | CLIの`sc commit` を厳密に再修正                  | ✅  |
| 4  | コミット後に再テスト                               | ✅  |

---

## 💡 再テスト手順

修正後に必ず以下のテストを実施：

```bash
sc wo create-from-chat
# 生成後、コミットの範囲を確認
git status
```

**期待される挙動**：

* 新しく生成したワークオーダーとレポートだけがステージングされる
* 競合したMarkdown見出しが挿入されず、内容が明確に表示される

---

以上で確実に問題を解消できます。
実装のサポートやレビューも可能ですので、引き続きサポートが必要ならお知らせください。
