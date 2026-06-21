# Findings JSON Schema

`findings.json` 是 Claude（你）分析後產出、由腳本消費的中介結構。它的 schema 必須嚴格遵守，因為 highlight 與 report 腳本依賴這個格式。

## 完整結構

```json
{
  "contract_name": "軟體委任設計合約書.docx",
  "review_date": "2026-06-21",
  "party_a_name": "○○股份有限公司",
  "party_b_name": "△△科技有限公司",
  "reviewer_stance": "乙方",
  "summary": {
    "total_risks": 7,
    "high_count": 3,
    "medium_count": 3,
    "low_count": 1,
    "missing_count": 4
  },
  "risks": [
    {
      "id": "R001",
      "clause_id": "第五條 第二項",
      "para_index": 23,
      "match_text": "乙方應於甲方通知後三日內無條件接受所有變更需求",
      "category": "unreasonable_liability",
      "risk_level": "高",
      "reason": "未限制變更範圍且工期費用不予調整，造成乙方無法控制工作量與成本。",
      "suggestion": "建議改為：『甲方提出變更需求時，雙方應於 5 個工作日內就工期及費用達成書面協議；未達成協議前，原合約條件繼續適用。』"
    }
  ],
  "missing_clauses": [
    {
      "id": "M-LIMIT",
      "name": "賠償責任上限",
      "reason": "本合約缺乏對乙方總賠償責任的限制，乙方可能因單一事件承擔遠超合約金額的損害。",
      "suggestion": "建議補充：『乙方就本合約所負之全部損害賠償責任（包含但不限於違約金、補償金），總額不得超過甲方已實際支付乙方之合約價金。』"
    }
  ]
}
```

## 欄位定義

### Top Level

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `contract_name` | string | 是 | 原始合約檔名（含 .docx） |
| `review_date` | string (ISO 8601) | 是 | 審查日期，如 `2026-06-21` |
| `party_a_name` | string | 是 | 甲方名稱（從合約抽取） |
| `party_b_name` | string | 是 | 乙方名稱（從合約抽取） |
| `reviewer_stance` | string | 是 | 固定為 `"乙方"` |
| `summary` | object | 是 | 風險統計，由 Claude 計算或腳本自動計算 |
| `risks` | array | 是 | 風險條款清單，可為空陣列 |
| `missing_clauses` | array | 是 | 缺失條款清單，可為空陣列 |

### `risks[]`

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `id` | string | 是 | 唯一識別碼，建議格式 `R001`、`R002` |
| `clause_id` | string | 是 | 條款編號或位置描述（如「第五條 第二項」） |
| `para_index` | integer | 是 | 對應 extracted.json 的段落索引（從 0 開始） |
| `match_text` | string | 是 | **必須在原文中精確存在**的字串，highlight 依據 |
| `category` | string | 是 | 七大類別之一：`unreasonable_liability` / `unilateral_termination` / `payment_risk` / `acceptance_risk` / `ip_risk` / `confidentiality_risk` / `penalty_risk` |
| `risk_level` | string | 是 | `高` / `中` / `低` |
| `reason` | string | 是 | 為何對乙方不利（建議 50-150 字） |
| `suggestion` | string | 是 | 具體修改建議，含替代用語 |

### `missing_clauses[]`

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `id` | string | 是 | review_principles.md 定義的代碼（M-LIMIT、M-FORCE 等）或自訂 `M-CUSTOM-001` |
| `name` | string | 是 | 條款名稱 |
| `reason` | string | 是 | 缺少此條款對乙方的影響 |
| `suggestion` | string | 是 | 建議補充的條款文字 |

## 重要規則

1. **`match_text` 必須是 extracted.json 中該段落的子字串。** 若無法精確比對，highlight 會失敗並記錄警告。
2. **`match_text` 長度建議 10-80 字。** 太短會誤標，太長易跨 run 失敗。
3. 同一段落可有多筆 risk，使用不同 `id`。
4. `summary` 數字應與實際 array 長度一致；若不一致，highlight script 會輸出警告但仍會處理。
5. 所有人類可讀文字（reason、suggestion）使用繁體中文。
