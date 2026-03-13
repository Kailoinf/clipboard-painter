#!/usr/bin/env python3
"""
敏感信息清理器 - 脱敏处理
"""
import re


class ClipboardSanitizer:
    """剪贴板敏感信息清理"""

    def __init__(self):
        # 脱敏规则
        self.rules = [
            # 身份证: 保留前3后4
            {
                'pattern': r'(\d{3})\d*(\d{4})',
                'replacement': r'\1********\2',
                'name': '身份证号'
            },
            # 手机号: 保留前3后4
            {
                'pattern': r'(1[3-9]\d{2})\d*(\d{4})',
                'replacement': r'\1****\2',
                'name': '手机号'
            },
            # 邮箱: 保留首字符和域名
            {
                'pattern': r'(\b[a-zA-Z0-9])[a-zA-Z0-9._%+-]*(@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                'replacement': r'\1***\2',
                'name': '邮箱'
            },
            # AWS Access Key: 完全隐藏
            {
                'pattern': r'AKIA[a-zA-Z0-9]{16}',
                'replacement': 'AKIA************************',
                'name': 'AWS Access Key'
            },
            # OpenAI API Key: 完全隐藏
            {
                'pattern': r'sk-[a-zA-Z0-9]{48}',
                'replacement': 'sk-****************************************',
                'name': 'OpenAI API Key'
            },
            # Base64 密钥: 隐藏大部分
            {
                'pattern': r'([A-Za-z0-9+/]{8})[A-Za-z0-9+/]{20,}={0,2}',
                'replacement': r'\1************************************',
                'name': 'Base64密钥'
            },
            # IP 地址: 保留前两段
            {
                'pattern': r'(\d{1,3}\.\d{1,3})\.\d{1,3}\.\d{1,3}',
                'replacement': r'\1.*.*',
                'name': 'IP地址'
            },
        ]

    def sanitize(self, content: str) -> tuple[str, list[str]]:
        """
        脱敏处理

        Args:
            content: 原始内容

        Returns:
            (脱敏后内容, 检测到的敏感类型列表)
        """
        result = content
        detected = []

        for rule in self.rules:
            # 先扫描，避免不必要的替换
            if re.search(rule['pattern'], content):
                result = re.sub(rule['pattern'], rule['replacement'], result)
                detected.append(rule['name'])

        return result, detected

    def scan(self, content: str) -> list[dict]:
        """
        扫描敏感信息（不修改）

        Returns:
            敏感信息列表 [{"type": "...", "count": 1}]
        """
        found = []

        for rule in self.rules:
            matches = re.findall(rule['pattern'], content)
            if matches:
                found.append({
                    "type": rule['name'],
                    "count": len(matches)
                })

        return found
