---
name: contract-reviewer
description: "Use this skill whenever the user wants to review, audit, or risk-assess contracts (.docx, .doc) from Party B (乙方) perspective. Triggers include: '審查合約', '合約風險', 'contract review', '幫我看一下合約', '乙方角度', '風險條款', '標記不利條款', or any request to scan a folder of contracts and produce highlighted reviewed copies plus risk reports. The skill scans the contract folder, identifies unfavorable, high-risk, or missing clauses, applies yellow highlighting to a copy of the contract, and generates a Word risk analysis report. Always use this skill when the user mentions reviewing contracts even if they don't explicitly ask for highlighting or a report."
license: Proprietary
---

# Contract Reviewer Skill

## 用途

掃描 `contract/` 資料夾中的所有 `.docx` 或 `.doc` 合約，以**乙方**立場進行條款風險審查，並輸出：

1. `{filename}_reviewed.docx`：原合約的副本，對乙方不利或高風險條款以黃色螢光筆標示
2. `{filename}_risk_report.docx`：完整風險分析報告

**重要原則：絕對不得修改原始合約檔案。** 所有輸出皆為副本。

## 工作流程

整個審查流程分為四個明確階段，請依序執行，不要跳過。

### 階段 1：掃描合約

使用 `scripts/extract_contract.py` 掃描目標資料夾，列出所有 `.docx` 與 `.doc` 檔案。對於 `.doc` 檔，必須先轉成 `.docx`（見下方注意事項）。

```bash
python scripts/extract_contract.py --scan <contract_dir>
```

對每一份合約執行：

```bash
python scripts/extract_contract.py --input <contract.docx> --output <work_dir>/extracted.json
```

`extracted.json` 包含：
- `paragraphs`：每段文字內容與索引（`para_index`）
- `metadata`：檔名、段落總數
- 表格內容（若有）

### 階段 2：識別風險條款（核心智力工作）

**這是這個 skill 最關鍵的部分，由你（Claude）親自進行分析。**

請先讀 `references/review_principles.md`，徹底理解乙方審查的七大風險面向與保護性條款檢核清單。

接著對 `extracted.json` 中的每一段條款，逐條檢視並判斷：

- 是否對乙方造成不合理責任？
- 是否存在單方終止權對乙方不利？
- 付款條件、發票流程、保留款比例是否過於嚴苛？
- 驗收條件是否模糊、主觀、缺少時限？
- 智慧財產權歸屬是否使乙方喪失應有權利？
- 保密義務範圍與期間是否過廣、過長？
- 違約金、賠償上限是否與合約金額不成比例？

同時檢視是否缺少對乙方有保護性的條款（例如：金額上限、不可抗力、利息條款、變更管理、爭議解決方式等）。

判斷完成後，產生 `findings.json`，schema 見 `references/findings_schema.md`。重要欄位：

- `risks[].match_text`：必須是原文中**精確**可比對的字串（用於 highlight），通常為條款中的具體一句話，不要超過 80 字
- `risks[].para_index`：對應 extracted.json 的段落索引
- `risks[].risk_level`：`高` / `中` / `低`
- `risks[].category`：見 review_principles.md 定義
- `missing_clauses[]`：缺少的保護性條款

**寫 findings.json 之前，務必再次確認 match_text 確實出現在 extracted.json 對應段落中。** 若無法精確比對，highlight 會失敗。

### 階段 3：產生帶有 highlight 的副本

```bash
python scripts/highlight_contract.py \
    --input <原始合約.docx> \
    --findings <findings.json> \
    --output <contract_dir>/<filename>_reviewed.docx
```

腳本會：
- 複製原始檔（不會修改原檔）
- 對每一筆 risk 的 `match_text` 套用黃色 highlight
- 若某筆 risk 無法在原文找到，會記錄警告但不中斷

### 階段 4：產生風險分析報告

```bash
python scripts/generate_risk_report.py \
    --findings <findings.json> \
    --contract-name <原始檔名> \
    --output <contract_dir>/<filename>_risk_report.docx
```

報告結構包含：
- 合約資訊與審查日期
- 風險統計摘要（依等級、依類別）
- 風險條款明細表（條款 / 原文 / 風險等級 / 不利原因 / 修改建議）
- 缺失條款清單與建議補充內容
- 整體建議與優先處理事項

### 階段 5：驗證輸出

確認兩個檔案皆已產生於 contract 資料夾，並向使用者回報：

- 已審查的合約數量
- 高 / 中 / 低風險條款各幾筆
- 缺失條款數量
- 輸出檔案路徑

## 為何要這樣設計

把「智力分析」和「文件操作」分開有幾個重要理由：

- **可追溯性**：findings.json 是中間產物，後續可被稽核、版本比對、或回放
- **可重現性**：腳本是純粹的 deterministic 轉換，給定相同 findings 必產生相同輸出
- **單一職責**：你（Claude）專心做法律判斷，腳本專心做 Word 操作
- **可測試性**：腳本可獨立單元測試，無需呼叫 LLM

## 注意事項

### .doc 檔案處理

`.doc`（Word 97-2003）格式不能直接用 python-docx 讀取。若遇到 `.doc`：

```bash
# 透過 LibreOffice 轉成 .docx（不會覆寫原始檔）
soffice --headless --convert-to docx --outdir <work_dir> <input.doc>
```

若環境沒有 LibreOffice，請告知使用者並停止審查該檔，不要嘗試強行處理。

### 原始檔保護

絕對不得對 contract 資料夾中的原始檔執行任何 write / edit 操作。所有處理皆透過 `extract_contract.py` 讀取後，把副本寫到工作目錄。輸出檔名必須帶 `_reviewed` 或 `_risk_report` 後綴，與原檔區隔。

### Match Text 撰寫策略

`match_text` 是 highlight 成敗的關鍵：
- 太短（如「乙方」）會誤標太多地方
- 太長（超過一行）容易跨 run 而比對失敗
- 建議取「最能表達該風險的關鍵句」，例如「乙方應於甲方通知後三日內無條件接受所有變更需求」這樣的完整句

若同一風險點需標多處，可在 findings 中列多筆 risk，共用相同的 `id` prefix（如 R001-a、R001-b）。

### 隱私與安全

合約內容可能含有商業機密、個資、定價資訊。處理過程：
- 不要把合約內容傳到外部服務
- 中間檔案（extracted.json、findings.json）建議放於 `contract/.work/` 子資料夾或暫時目錄
- 完成後可選擇是否保留中間檔（預設保留，供稽核）

## 範例對話

**使用者**：「幫我看一下 contract 資料夾裡的合約」

**你的回應**：
1. 執行 `python scripts/extract_contract.py --scan contract/` 列出檔案
2. 告知使用者找到幾份合約並開始審查
3. 對每份合約依序執行階段 1-4
4. 最後彙整摘要回報

## 檔案結構

```
contract-reviewer/
├── SKILL.md                          # 本檔
├── scripts/
│   ├── extract_contract.py           # 階段 1：抽取條款
│   ├── highlight_contract.py         # 階段 3：套用黃色 highlight
│   └── generate_risk_report.py       # 階段 4：產生風險報告
└── references/
    ├── review_principles.md          # 乙方審查七大原則 + 缺失條款檢核清單
    └── findings_schema.md            # findings.json 結構說明
```
