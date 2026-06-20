"""Fund NAV Workbench 的 CustomTkinter 桌面介面（Dark Mode）。"""

import logging
from dataclasses import dataclass
from decimal import DecimalException
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from fund_nav.domain.exceptions import FundNavError
from fund_nav.domain.models import Fund, Holding
from fund_nav.services.calculator import NavCalculator
from fund_nav.services.repository import FundRepository

logger = logging.getLogger(__name__)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

WINDOW_TITLE = "Fund NAV Workbench"
WINDOW_SIZE = "1024x680"


@dataclass
class HoldingRow:
    """持倉輸入列的一組 widget。"""

    frame: ctk.CTkFrame
    symbol: ctk.CTkEntry
    name: ctk.CTkEntry
    quantity: ctk.CTkEntry
    price: ctk.CTkEntry


class NavWorkbenchApp(ctk.CTk):
    """基金淨值計算主視窗。"""

    def __init__(self) -> None:
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(900, 600)

        self._calculator = NavCalculator()
        self._repository = FundRepository()
        self._holding_rows: list[HoldingRow] = []

        self._build_layout()
        self._seed_example()
        logger.info("UI 初始化完成")

    # ------------------------------------------------------------------
    # 介面建構
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self._build_input_panel()
        self._build_result_panel()

    def _build_input_panel(self) -> None:
        panel = ctk.CTkFrame(self)
        panel.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        title = ctk.CTkLabel(
            panel, text="基金資料", font=ctk.CTkFont(size=20, weight="bold")
        )
        title.grid(row=0, column=0, padx=12, pady=(12, 4), sticky="w")

        form = ctk.CTkFrame(panel, fg_color="transparent")
        form.grid(row=1, column=0, padx=12, pady=4, sticky="ew")
        for col in (1, 3):
            form.grid_columnconfigure(col, weight=1)

        self._name_entry = self._labeled_entry(form, "基金名稱", 0, 0, colspan=3)
        self._cash_entry = self._labeled_entry(form, "現金", 1, 0)
        self._liabilities_entry = self._labeled_entry(form, "負債", 1, 2)
        self._units_entry = self._labeled_entry(form, "流通在外單位數", 2, 0)

        holdings_box = ctk.CTkScrollableFrame(panel, label_text="持倉明細")
        holdings_box.grid(row=2, column=0, padx=12, pady=8, sticky="nsew")
        holdings_box.grid_columnconfigure(tuple(range(5)), weight=1)
        self._holdings_box = holdings_box
        self._render_holdings_header()

        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=3, column=0, padx=12, pady=(4, 12), sticky="ew")
        ctk.CTkButton(actions, text="新增持倉", command=self.add_holding_row).pack(
            side="left", padx=4
        )
        ctk.CTkButton(actions, text="載入", command=self._on_load).pack(
            side="left", padx=4
        )
        ctk.CTkButton(actions, text="儲存", command=self._on_save).pack(
            side="left", padx=4
        )
        ctk.CTkButton(
            actions, text="計算淨值", command=self._on_calculate
        ).pack(side="right", padx=4)

    def _build_result_panel(self) -> None:
        panel = ctk.CTkFrame(self)
        panel.grid(row=0, column=1, padx=(0, 16), pady=16, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel, text="計算結果", font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, padx=12, pady=(12, 4), sticky="w")

        self._nav_label = ctk.CTkLabel(
            panel, text="—", font=ctk.CTkFont(size=40, weight="bold")
        )
        self._nav_label.grid(row=1, column=0, padx=12, pady=(8, 0))
        ctk.CTkLabel(panel, text="每單位淨值").grid(row=2, column=0, pady=(0, 12))

        self._detail_box = ctk.CTkTextbox(panel, height=320)
        self._detail_box.grid(row=3, column=0, padx=12, pady=8, sticky="nsew")
        panel.grid_rowconfigure(3, weight=1)

        self._status_label = ctk.CTkLabel(panel, text="", text_color="#ff6b6b")
        self._status_label.grid(row=4, column=0, padx=12, pady=(0, 12), sticky="w")

    def _labeled_entry(
        self,
        parent: ctk.CTkBaseClass,
        label: str,
        row: int,
        col: int,
        *,
        colspan: int = 1,
    ) -> ctk.CTkEntry:
        ctk.CTkLabel(parent, text=label).grid(
            row=row * 2, column=col, columnspan=colspan, padx=6, pady=(6, 0), sticky="w"
        )
        entry = ctk.CTkEntry(parent)
        entry.grid(
            row=row * 2 + 1,
            column=col,
            columnspan=colspan,
            padx=6,
            pady=(0, 6),
            sticky="ew",
        )
        return entry

    def _render_holdings_header(self) -> None:
        header = ctk.CTkFrame(self._holdings_box, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=5, sticky="ew")
        for idx, text in enumerate(("代號", "名稱", "數量", "市價", "")):
            header.grid_columnconfigure(idx, weight=1)
            ctk.CTkLabel(header, text=text).grid(row=0, column=idx, padx=4, sticky="w")

    # ------------------------------------------------------------------
    # 持倉列操作
    # ------------------------------------------------------------------
    def add_holding_row(
        self,
        symbol: str = "",
        name: str = "",
        quantity: str = "",
        price: str = "",
    ) -> HoldingRow:
        """新增一列持倉輸入欄位。"""
        row_index = len(self._holding_rows) + 1
        frame = ctk.CTkFrame(self._holdings_box, fg_color="transparent")
        frame.grid(row=row_index, column=0, columnspan=5, pady=2, sticky="ew")
        for idx in range(5):
            frame.grid_columnconfigure(idx, weight=1)

        entries: list[ctk.CTkEntry] = []
        for idx, value in enumerate((symbol, name, quantity, price)):
            entry = ctk.CTkEntry(frame)
            entry.insert(0, value)
            entry.grid(row=0, column=idx, padx=4, sticky="ew")
            entries.append(entry)

        holding_row = HoldingRow(frame, entries[0], entries[1], entries[2], entries[3])
        ctk.CTkButton(
            frame,
            text="移除",
            width=60,
            command=lambda: self._remove_holding_row(holding_row),
        ).grid(row=0, column=4, padx=4)

        self._holding_rows.append(holding_row)
        return holding_row

    def _remove_holding_row(self, row: HoldingRow) -> None:
        row.frame.destroy()
        self._holding_rows.remove(row)

    # ------------------------------------------------------------------
    # 事件處理
    # ------------------------------------------------------------------
    def _on_calculate(self) -> None:
        self._status_label.configure(text="")
        try:
            fund = self._build_fund()
            result = self._calculator.calculate(fund)
        except (FundNavError, DecimalException, ValueError) as exc:
            logger.warning("計算失敗：%s", exc)
            self._status_label.configure(text=f"計算失敗：{exc}")
            return

        self._nav_label.configure(text=f"{result.nav_per_unit}")
        details = (
            f"基金名稱：{result.fund_name}\n"
            f"持倉市值：{result.total_market_value}\n"
            f"現金：{result.cash}\n"
            f"總資產：{result.total_assets}\n"
            f"總負債：{result.total_liabilities}\n"
            f"淨資產價值：{result.net_asset_value}\n"
            f"流通單位數：{result.units_outstanding}\n"
            f"每單位淨值：{result.nav_per_unit}\n"
            f"計算時間：{result.as_of:%Y-%m-%d %H:%M:%S}\n"
        )
        self._detail_box.delete("1.0", "end")
        self._detail_box.insert("1.0", details)

    def _on_save(self) -> None:
        path_str = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON", "*.json")]
        )
        if not path_str:
            return
        try:
            self._repository.save(self._build_fund(), Path(path_str))
            self._status_label.configure(
                text_color="#51cf66", text=f"已儲存至 {path_str}"
            )
        except (FundNavError, DecimalException, OSError) as exc:
            logger.warning("儲存失敗：%s", exc)
            self._status_label.configure(text_color="#ff6b6b", text=f"儲存失敗：{exc}")

    def _on_load(self) -> None:
        path_str = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path_str:
            return
        try:
            fund = self._repository.load(Path(path_str))
        except (FundNavError, OSError, ValueError) as exc:
            logger.warning("載入失敗：%s", exc)
            self._status_label.configure(text_color="#ff6b6b", text=f"載入失敗：{exc}")
            return
        self._populate_from_fund(fund)
        self._status_label.configure(text_color="#51cf66", text="已載入基金資料")

    # ------------------------------------------------------------------
    # 資料轉換
    # ------------------------------------------------------------------
    def _build_fund(self) -> Fund:
        holdings = [
            Holding(
                symbol=row.symbol.get().strip(),
                name=row.name.get().strip(),
                quantity=row.quantity.get().strip() or "0",
                price=row.price.get().strip() or "0",
            )
            for row in self._holding_rows
            if row.symbol.get().strip()
        ]
        return Fund(
            name=self._name_entry.get().strip(),
            holdings=holdings,
            cash=self._cash_entry.get().strip() or "0",
            liabilities=self._liabilities_entry.get().strip() or "0",
            units_outstanding=self._units_entry.get().strip() or "0",
        )

    def _populate_from_fund(self, fund: Fund) -> None:
        self._set_entry(self._name_entry, fund.name)
        self._set_entry(self._cash_entry, str(fund.cash))
        self._set_entry(self._liabilities_entry, str(fund.liabilities))
        self._set_entry(self._units_entry, str(fund.units_outstanding))

        for row in list(self._holding_rows):
            self._remove_holding_row(row)
        for holding in fund.holdings:
            self.add_holding_row(
                holding.symbol,
                holding.name,
                str(holding.quantity),
                str(holding.price),
            )

    @staticmethod
    def _set_entry(entry: ctk.CTkEntry, value: str) -> None:
        entry.delete(0, "end")
        entry.insert(0, value)

    def _seed_example(self) -> None:
        """填入展示用範例資料。"""
        self._set_entry(self._name_entry, "示範基金")
        self._set_entry(self._cash_entry, "1000000")
        self._set_entry(self._liabilities_entry, "50000")
        self._set_entry(self._units_entry, "100000")
        self.add_holding_row("2330", "台積電", "1000", "950.5")
        self.add_holding_row("2317", "鴻海", "2000", "165.0")

    def run(self) -> None:
        """啟動主事件迴圈。"""
        logger.info("進入主事件迴圈")
        self.mainloop()
