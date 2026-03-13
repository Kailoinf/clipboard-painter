#!/usr/bin/env python3
"""
剪贴板监听守护进程
"""
import time
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
import yaml

import pyperclip

from src.classifier import ClipboardClassifier
from src.sanitizer import ClipboardSanitizer
from src.logger import logger


class ClipboardDaemon:
    """剪贴板守护进程"""

    def __init__(self, db_path: str = "data/clipboard.db", config_path: str = "config/rules.yaml"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.max_history = self.config.get('database', {}).get('max_history', 10000)
        self.auto_clean_days = self.config.get('database', {}).get('auto_clean_days', 30)

        self.classifier = ClipboardClassifier()
        self.sanitizer = ClipboardSanitizer()

        self.running = False
        self.last_content = ""
        self.lock = threading.Lock()
        self.db_lock = threading.Lock()

        # 批处理优化：积累多条记录后批量写入
        self._batch_buffer = []
        self._batch_size = 10  # 每10条记录批量写入一次
        self._batch_timer = 5  # 或最多5秒后强制写入

        self._init_db()

    @contextmanager
    def _get_db_connection(self):
        """数据库连接上下文管理器（防止锁冲突）"""
        conn = None
        try:
            with self.db_lock:
                conn = sqlite3.connect(self.db_path, timeout=30)
                conn.row_factory = sqlite3.Row
                yield conn
        except Exception as e:
            logger.error(f"数据库连接错误: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def _init_db(self):
        """初始化数据库（优化索引）"""
        with self._get_db_connection() as conn:
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

            # 添加复合索引，优化查询性能
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_type_created
                ON clipboard_history(content_type, created_at DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_keywords
                ON clipboard_history(keywords)
            """)

            conn.commit()
            logger.info("数据库初始化完成")

    def _auto_clean_old_records(self, conn, cursor):
        """自动清理过期记录"""
        if self.auto_clean_days <= 0:
            return

        cursor.execute("""
            DELETE FROM clipboard_history
            WHERE created_at < datetime('now', '-' || ? || ' days')
        """, (self.auto_clean_days,))

        deleted = cursor.rowcount
        if deleted > 0:
            conn.commit()
            logger.info(f"清理了 {deleted} 条过期记录")

    def _limit_history_size(self, conn, cursor):
        """限制历史记录数量"""
        cursor.execute("""
            SELECT COUNT(*) as total FROM clipboard_history
        """)
        total = cursor.fetchone()['total']

        if total > self.max_history:
            # 删除最旧的记录
            cursor.execute("""
                DELETE FROM clipboard_history
                WHERE id IN (
                    SELECT id FROM clipboard_history
                    ORDER BY created_at ASC
                    LIMIT ?
                )
            """, (total - self.max_history,))
            deleted = cursor.rowcount
            conn.commit()
            logger.info(f"删除了 {deleted} 条记录以保持在限制范围内")

    def _flush_batch(self):
        """刷新批处理缓冲区，批量写入数据库"""
        if not self._batch_buffer:
            return

        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            # 批量插入
            cursor.executemany("""
                INSERT INTO clipboard_history (content, content_type, keywords, has_sensitive)
                VALUES (?, ?, ?, ?)
            """, self._batch_buffer)

            conn.commit()
            logger.info(f"批量写入 {len(self._batch_buffer)} 条记录")

            # 执行清理任务
            self._auto_clean_old_records(conn, cursor)
            self._limit_history_size(conn, cursor)

        self._batch_buffer.clear()

    def _save_clipboard(self, content: str, content_type: str, keywords: str, has_sensitive: bool):
        """保存剪贴板内容到批处理缓冲区"""
        self._batch_buffer.append((content, content_type, keywords, int(has_sensitive)))

        # 达到批量大小立即写入
        if len(self._batch_buffer) >= self._batch_size:
            self._flush_batch()

    def _process_clipboard(self, content: str):
        """处理剪贴板内容"""
        try:
            # 分类
            content_type = self.classifier.classify(content)

            # 提取关键词
            keywords = ",".join(self.classifier.extract_keywords(content))

            # 扫描敏感信息
            sensitive_info = self.sanitizer.scan(content)
            has_sensitive = len(sensitive_info) > 0

            # 保存到数据库
            self._save_clipboard(content, content_type, keywords, has_sensitive)

            logger.info(f"类型: {content_type:6} | 敏感: {'是' if has_sensitive else '否':2} | "
                       f"关键词: {keywords[:30]}...")

        except Exception as e:
            logger.error(f"处理剪贴板内容失败: {e}")

    def start(self):
        """启动守护进程"""
        self.running = True

        logger.info("🖌️  Clipboard Painter 启动...")
        logger.info("📋 正在监听剪贴板变化...")
        logger.info(f"⚙️  最大历史记录: {self.max_history}")
        logger.info(f"🧹 自动清理天数: {self.auto_clean_days}")

        while self.running:
            try:
                with self.lock:
                    content = pyperclip.paste()

                if content and content != self.last_content:
                    self._process_clipboard(content)
                    self.last_content = content

            except Exception as e:
                logger.error(f"主循环错误: {e}")

            time.sleep(0.5)  # 每0.5秒检查一次

    def stop(self):
        """停止守护进程"""
        self.running = False
        self._flush_batch()  # 确保缓冲区中的数据写入
        logger.info("🛑 Clipboard Painter 已停止")


def main():
    """主函数入口"""
    import argparse

    parser = argparse.ArgumentParser(description="Clipboard Painter - 让剪贴板变聪明")
    parser.add_argument("--db", default="data/clipboard.db", help="数据库路径")
    parser.add_argument("--config", default="config/rules.yaml", help="配置文件路径")
    args = parser.parse_args()

    daemon = ClipboardDaemon(db_path=args.db, config_path=args.config)
    try:
        daemon.start()
    except KeyboardInterrupt:
        daemon.stop()
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        raise


if __name__ == "__main__":
    main()
