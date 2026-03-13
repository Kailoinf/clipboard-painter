#!/usr/bin/env python3
"""
剪贴板监听守护进程
"""
import time
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

import pyperclip

from classifier import ClipboardClassifier
from sanitizer import ClipboardSanitizer


class ClipboardDaemon:
    """剪贴板守护进程"""

    def __init__(self, db_path: str = "data/clipboard.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.classifier = ClipboardClassifier()
        self.sanitizer = ClipboardSanitizer()

        self.running = False
        self.last_content = ""
        self.lock = threading.Lock()

        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clipboard_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                content_type TEXT NOT NULL,
                keywords TEXT,
                has_sensitive BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_type ON clipboard_history(content_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created ON clipboard_history(created_at)
        """)

        conn.commit()
        conn.close()

    def _save_clipboard(self, content: str, content_type: str, keywords: str, has_sensitive: bool):
        """保存剪贴板内容到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO clipboard_history (content, content_type, keywords, has_sensitive)
            VALUES (?, ?, ?, ?)
        """, (content, content_type, keywords, int(has_sensitive)))

        conn.commit()
        conn.close()

    def _process_clipboard(self, content: str):
        """处理剪贴板内容"""
        # 分类
        content_type = self.classifier.classify(content)

        # 提取关键词
        keywords = ",".join(self.classifier.extract_keywords(content))

        # 扫描敏感信息
        sensitive_info = self.sanitizer.scan(content)
        has_sensitive = len(sensitive_info) > 0

        # 保存到数据库
        self._save_clipboard(content, content_type, keywords, has_sensitive)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"类型: {content_type:6} | "
              f"敏感: {'是' if has_sensitive else '否':2} | "
              f"关键词: {keywords}")

    def start(self):
        """启动守护进程"""
        self.running = True

        print("🖌️  Clipboard Painter 启动...")
        print("📋 正在监听剪贴板变化...")

        while self.running:
            try:
                with self.lock:
                    content = pyperclip.paste()

                if content and content != self.last_content:
                    self._process_clipboard(content)
                    self.last_content = content

            except Exception as e:
                print(f"❌ 错误: {e}")

            time.sleep(0.5)  # 每0.5秒检查一次

    def stop(self):
        """停止守护进程"""
        self.running = False
        print("🛑 Clipboard Painter 已停止")


if __name__ == "__main__":
    daemon = ClipboardDaemon()
    try:
        daemon.start()
    except KeyboardInterrupt:
        daemon.stop()
