#!/bin/bash

# ニュース集約ファイルの検証スクリプト

echo "🔍 news_from_project.json の検証"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

FILE="news_from_project.json"

if [ ! -f "$FILE" ]; then
    echo "❌ エラー: $FILE が見つかりません"
    exit 1
fi

# JSON の妥当性チェック
if jq empty "$FILE" 2>/dev/null; then
    echo "✅ JSON 形式は有効です"
else
    echo "❌ JSON 形式が無効です"
    exit 1
fi

# メタデータの確認
echo ""
echo "📊 メタデータ"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
jq '.period, .project_number, .total_count' "$FILE"

# ニュース件数の確認
TOTAL=$(jq '.news | length' "$FILE")
echo ""
echo "📈 ニュース件数"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "全件数: $TOTAL 件"

# 必須フィールドの確認
echo ""
echo "✓ 必須フィールドの確認"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
FIELDS="issue_number title category issue_url created_at date summary"
for field in $FIELDS; do
    COUNT=$(jq ".news[0] | has(\"$field\")" "$FILE")
    if [ "$COUNT" = "true" ]; then
        echo "✅ $field"
    else
        echo "❌ $field (欠落)"
    fi
done

# カテゴリ別統計
echo ""
echo "📋 カテゴリ別統計"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
jq '.statistics' "$FILE" | grep -v '^{' | grep -v '^}' | sed 's/,$//'

echo ""
echo "✅ 検証完了"
