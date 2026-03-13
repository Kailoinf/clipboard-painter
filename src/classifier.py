#!/usr/bin/env python3
"""
内容分类器 - 识别剪贴板内容类型
"""
import re
from typing import Literal

ContentType = Literal["url", "code", "text", "image", "email", "phone", "unknown"]


class ClipboardClassifier:
    """剪贴板内容分类"""

    def __init__(self):
        # URL 模式
        self.url_pattern = re.compile(
            r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w .-]*/?'
        )

        # 代码模式
        self.code_patterns = [
            re.compile(r'\bdef\s+\w+\s*\(.*\):'),  # Python 函数
            re.compile(r'\bfunction\s+\w+\s*\(.*\)'),  # JS 函数
            re.compile(r'\bclass\s+\w+.*:'),  # Python/JS 类
            re.compile(r'<[a-zA-Z][^>]*>.*<\/[a-zA-Z][^>]*>'),  # HTML 标签
            re.compile(r'\{[\s\S]*\}'),  # JSON 对象
            re.compile(r'\w+\s*=\s*[\'"].*[\'"]'),  # 赋值语句
            re.compile(r'import\s+\w+'),  # Python import
            re.compile(r'const\s+\w+'),  # JS const
            re.compile(r'git\s+'),  # Git 命令
        ]

        # 邮箱模式
        self.email_pattern = re.compile(
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        )

        # 手机号模式（中国大陆）
        self.phone_pattern = re.compile(r'1[3-9]\d{9}')

        # 敏感信息模式（身份证、密钥等）
        self.sensitive_patterns = [
            re.compile(r'\d{15}|\d{17}[\dXx]'),  # 身份证
            re.compile(r'[A-Za-z0-9+/]{32,}={0,2}'),  # Base64 密钥
            re.compile(r'AKIA[a-zA-Z0-9]{16}'),  # AWS Access Key
            re.compile(r'sk-[a-zA-Z0-9]{48}'),  # OpenAI API Key
        ]

    def classify(self, content: str) -> ContentType:
        """
        分类剪贴板内容

        Args:
            content: 剪贴板文本内容

        Returns:
            内容类型
        """
        if content is None:
            return "unknown"

        if not content.strip():
            return "unknown"

        content = content.strip()

        # 优先检测敏感信息
        if self._has_sensitive(content):
            return "text"  # 标记为text，但在sanitizer中会特殊处理

        # URL
        if self.url_pattern.match(content):
            return "url"

        # 邮箱
        if self.email_pattern.fullmatch(content):
            return "email"

        # 手机号
        if self.phone_pattern.fullmatch(content):
            return "phone"

        # 代码
        if self._is_code(content):
            return "code"

        return "text"

    def _is_code(self, content: str) -> bool:
        """判断是否为代码"""
        for pattern in self.code_patterns:
            if pattern.search(content):
                return True

        # 多行缩进通常是代码
        lines = content.split('\n')
        if len(lines) > 2:
            indented_count = sum(1 for line in lines if line.startswith((' ', '\t')))
            if indented_count > len(lines) * 0.5:
                return True

        return False

    def _has_sensitive(self, content: str) -> bool:
        """是否包含敏感信息"""
        for pattern in self.sensitive_patterns:
            if pattern.search(content):
                return True
        return False

    def extract_keywords(self, content: str) -> list[str]:
        """提取关键词用于搜索"""
        words = re.findall(r'\b\w{3,}\b', content.lower())
        # 去重并排序（按词频）
        word_count = {}
        for word in words:
            word_count[word] = word_count.get(word, 0) + 1

        # 返回出现最多的前5个词
        return sorted(word_count.keys(), key=lambda x: -word_count[x])[:5]
