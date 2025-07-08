<!-- TEMPLATE_START -->
# 作業報告書テンプレート

## 1. 概要

このセクションでは、ワークオーダーの目的と、本報告書で扱う作業の概要を簡潔に記述します。

- **ワークオーダーID**: {{ workorder.id }}
- **タイトル**: {{ workorder.title }}
- **関連ドキュメント**: {{ workorder.metadata.related_docs | default('なし') }}

## 2. 作業内容

実施した作業の詳細を記述します。具体的な手順、変更点、実装上の工夫などを分かりやすく説明します。

{{ workorder.summary_content }}

### 2.1. ワークオーダーのステップ

{{ workorder.steps_formatted }}

## 3. 成果物

本作業で作成または更新された主要な成果物をリストアップします。ファイルパスはプロジェクトルートからの相対パスで記述してください。

- `[ファイルパス]`: [簡単な説明]
  - 例: `projects/solar_circuit/solar_circuit/cli.py`: CLIコマンドの追加と修正

## 4. 結果

作業の結果と、それがワークオーダーの目標に対してどのように貢献したかを記述します。テスト結果、カバレッジ、静的解析の結果など、具体的な数値や証拠を含めます。

- **テスト結果**: [成功/失敗]
- **コードカバレッジ**: [XX%]
- **静的解析**: [問題なし/問題あり（詳細を記述）]

## 5. 完了定義 (Definition of Done)

ワークオーダーに定義された完了条件に対する達成状況をチェックリスト形式で示します。

{{ workorder.expected_output_formatted }}

## 6. 補足

特記事項や、今後の課題、CI/CDバッジなどの追加情報があれば記述します。

- ![CI Status](https://example.com/ci-badge.svg)
- ![Coverage](https://example.com/coverage-badge.svg)

---

## メタ情報 (機械処理用)

```json
{
  "id": "{{ workorder.id }}",
  "title": "{{ workorder.title }}",
  "success_cmd": "[成功確認コマンド]"
}
````

<!-- TEMPLATE_END -->