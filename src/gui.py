#!/usr/bin/env python3
"""
GUI 界面 - 快捷键唤起搜索界面
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sqlite3
from pathlib import Path
from datetime import datetime
import yaml

from logger import logger


class ClipboardGUI:
    """剪贴板历史搜索界面"""

    def __init__(self, db_path: str = "data/clipboard.db", config_path: str = "config/rules.yaml"):
        self.db_path = Path(db_path)
        self.config_path = config_path

        # 加载配置
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.window = None
        self.search_var = tk.StringVar()
        self.type_filter = tk.StringVar(value="all")
        self.result_text = None

    def create_window(self):
        """创建搜索窗口"""
        self.window = tk.Tk()
        self.window.title("🖌️ Clipboard Painter - 搜索")
        self.window.geometry("800x600")

        # 搜索框
        search_frame = ttk.Frame(self.window, padding="10")
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="🔍 搜索:").pack(side=tk.LEFT)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=50)
        search_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        search_entry.focus()

        # 搜索按钮
        ttk.Button(search_frame, text="搜索", command=self.search).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="清空", command=self.clear).pack(side=tk.LEFT, padx=5)

        # 类型过滤
        filter_frame = ttk.Frame(self.window, padding="10")
        filter_frame.pack(fill=tk.X)

        ttk.Label(filter_frame, text="类型:").pack(side=tk.LEFT)

        type_options = ["all", "url", "code", "text", "email", "phone"]
        for opt in type_options:
            ttk.Radiobutton(filter_frame, text=opt.upper(), value=opt,
                           variable=self.type_filter, command=self.search).pack(side=tk.LEFT, padx=5)

        # 结果显示区
        self.result_text = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, font=("Consolas", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 绑定快捷键
        self.window.bind("<Escape>", lambda e: self.window.destroy())
        self.window.bind("<Return>", lambda e: self.search())

        logger.info("GUI 窗口已创建")

    def search(self, event=None):
        """搜索历史记录"""
        query = self.search_var.get().strip()
        content_type = self.type_filter.get()

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            sql = "SELECT * FROM clipboard_history WHERE 1=1"
            params = []

            if content_type != "all":
                sql += " AND content_type = ?"
                params.append(content_type)

            if query:
                sql += " AND (content LIKE ? OR keywords LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%"])

            sql += " ORDER BY created_at DESC LIMIT 100"

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()

            # 显示结果
            self.result_text.delete(1.0, tk.END)

            if not rows:
                self.result_text.insert(tk.END, "没有找到匹配的记录\n")
                return

            self.result_text.insert(tk.END, f"找到 {len(rows)} 条记录:\n\n")

            for row in rows:
                self.result_text.insert(tk.END, f"ID: {row['id']}\n")
                self.result_text.insert(tk.END, f"时间: {row['created_at']}\n")
                self.result_text.insert(tk.END, f"类型: {row['content_type']}\n")
                if row['has_sensitive']:
                    self.result_text.insert(tk.END, "⚠️  包含敏感信息\n")
                self.result_text.insert(tk.END, f"内容:\n{row['content'][:500]}\n")
                if len(row['content']) > 500:
                    self.result_text.insert(tk.END, "... (内容过长)\n")
                self.result_text.insert(tk.END, "-" * 80 + "\n\n")

            logger.info(f"搜索完成，找到 {len(rows)} 条记录")

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            messagebox.showerror("错误", f"搜索失败: {e}")

    def clear(self):
        """清空搜索和结果"""
        self.search_var.set("")
        self.type_filter.set("all")
        self.result_text.delete(1.0, tk.END)

    def run(self):
        """运行 GUI"""
        self.create_window()
        self.search()  # 初始加载所有记录
        self.window.mainloop()


def main():
    """GUI 主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Clipboard Painter GUI")
    parser.add_argument("--db", default="data/clipboard.db", help="数据库路径")
    parser.add_argument("--config", default="config/rules.yaml", help="配置文件路径")
    args = parser.parse_args()

    gui = ClipboardGUI(db_path=args.db, config_path=args.config)
    gui.run()


if __name__ == "__main__":
    main()
