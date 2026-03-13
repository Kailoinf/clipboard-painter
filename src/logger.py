#!/usr/bin/env python3
"""
日志配置模块
"""
import logging
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "clipboard-painter", log_dir: str = "logs") -> logging.Logger:
    """
    配置日志系统

    Args:
        name: 日志器名称
        log_dir: 日志目录

    Returns:
        配置好的日志器
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 文件 handler
    log_file = log_path / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 控制台 handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# 导出单例
logger = setup_logger()
