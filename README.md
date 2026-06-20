# Fund NAV Workbench

計算基金淨值（NAV, Net Asset Value）的桌面應用程式。本專案作為企業內部展示 Claude Code 能力使用。

## 功能

- 輸入基金的持倉明細、現金、負債與流通在外單位數
- 一鍵計算總資產、淨資產價值（NAV）與每單位淨值
- 以 JSON 格式儲存／載入基金資料
- CustomTkinter Dark Mode 介面

## 淨值公式

```
總資產     = 持倉市值總額 + 現金
NAV        = 總資產 - 負債
每單位淨值 = NAV / 流通在外單位數
```

金額計算全程使用 `Decimal`，避免浮點數誤差。

## 環境需求

- Python 3.14
- [uv](https://docs.astral.sh/uv/)

## 安裝與執行

```bash
uv sync              # 安裝相依套件
uv run main.py       # 啟動桌面應用程式
# 或
uv run python -m fund_nav
```

## 測試

```bash
uv run pytest                              # 執行測試並檢查覆蓋率（門檻 90%）
uv run pytest tests/test_calculator.py     # 執行單一測試檔
uv run pytest -k nav_per_unit              # 依名稱篩選測試
```

## 專案結構

```
fund_nav/
├── app.py              # 進入點：設定 logging 並啟動 UI
├── logging_config.py   # 集中化 logging 設定
├── domain/             # 領域層：Holding、Fund、NavResult、例外
├── services/           # 服務層：NavCalculator（計算）、FundRepository（持久化）
└── ui/                 # UI 層：CustomTkinter 介面
tests/                  # 對應 domain 與 services 的單元測試
```

UI 層因需顯示器而不納入覆蓋率統計，核心計算與持久化邏輯覆蓋率達 100%。
