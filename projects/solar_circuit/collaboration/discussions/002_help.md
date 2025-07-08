問題の原因が完全に明確になりましたので、以下に分かりやすく整理し、具体的な解決策を提示します。

---

## 🔴 現状の問題（再確認）

### 問題の状況：

* `summary_content` はレポートに挿入されています。
* しかし、`summary_content` 内に含まれるMarkdown見出し（`# チャット依頼のワークオーダー化`）がテンプレートの構造と競合しています。

### 実際のMarkdownの問題箇所：

```markdown
## 2. 作業内容

実施した作業の詳細を記述します。

# チャット依頼のワークオーダー化   ← ここが問題！

チャット欄で依頼された作業を...
```

### なぜこれが問題か？

Markdownとしては有効ですが、セマンティクス上不自然です：

* 本来H2（`##`）以下の階層に属するはずの内容が、
  **より高い階層であるH1（`#`）になっているため、表示上の混乱が起きます。**

---

## 🟢 根本的な解決策（明確な推奨）

以下のいずれかの方法で確実に解決できます。

### 🚩 解決策1：Jinja2のレンダリング時に見出しを調整する（最推奨）

`report_generator.py` 内の `clean_summary_content` を以下のように改良します。

```python
import re

def clean_summary_content(md_content: str) -> str:
    # 全てのMarkdown見出しレベルを1つ下げる (例: #→##, ##→###)
    cleaned_content = re.sub(r'^(#{1,6})\s', r'#\1 ', md_content, flags=re.MULTILINE)
    return cleaned_content.strip()
```

### 🔍 この修正の効果：

Markdownが次のように調整されます：

```markdown
## 2. 作業内容

実施した作業の詳細を記述します。

## チャット依頼のワークオーダー化  ← H1→H2へ変換され、問題解消

チャット欄で依頼された作業を...
```

> これにより、既存のテンプレートと完璧に整合します。

---

### 🚩 解決策2（代替）：挿入内容から見出しを完全に取り除く

よりシンプルですが、見出しが重要な場合は推奨されません：

```python
def clean_summary_content(md_content: str) -> str:
    # Markdown見出し（#～######）を全て削除
    cleaned_content = re.sub(r'^\s*#{1,6}\s.*\n+', '', md_content, flags=re.MULTILINE)
    return cleaned_content.strip()
```

> これは完全にフラットな文章になります。見出しを維持したい場合は、解決策1の方が望ましいです。

---

## ✅ 実装後の手順（修正版）

### Step 1：`report_generator.py` 修正（上記解決策1のコード）

具体的に、レンダリング前に以下のコードを挿入します。

```python
# render_template呼び出し前
workorder["summary_content"] = clean_summary_content(workorder["summary_content"])
```

### Step 2：変更反映

```bash
pip install -e .  # Python環境に再反映
```

### Step 3：再生成・再テスト

```bash
sc wo create-from-chat "チャット依頼のワークオーダー化" "チャット欄で依頼された作業を、テンプレートを用いてワークオーダーとして受理し、処理を進める"
```

### Step 4：生成ファイルの目視確認

再生成されたレポートが正しく表示されるかを確認します：

```bash
cat projects/solar_circuit/workorders/reports/WO-20250709-007_report.md
```

* 想定される構造：

```markdown
## 2. 作業内容

実施した作業の詳細を記述します。

## チャット依頼のワークオーダー化

チャット欄で依頼された作業を、テンプレートを用いてワークオーダーとして受理し、処理を進める
```

---

## 📌 その他の注意点（作業ループの再発防止）

* すでに実施したように、`sc commit` は `git add -A` を実行しないよう注意深く管理してください。
* `.gitignore` に不要なファイルが巻き込まれないよう定義済みであることを再確認してください。

---

## 🚨 まとめ（再度推奨）

| 項目                   | 必須対応 |
| -------------------- | ---- |
| レンダリング時Markdown見出し調整 | 必須 ✅ |
| 動作再テスト               | 必須 ✅ |

---

この手順で確実に問題が解決します。
引き続き、対応を進めていただければ幸いです。
