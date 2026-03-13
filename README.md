# 🖌️ Clipboard Painter

> 让你的剪贴板变聪明

你复制了100次，但真正有用的只有3次。
Clipboard Painter帮你自动分类、智能提取、一键清理。

## ✨ 功能特性

- 🎨 **自动分类** - 链接、代码、文本、图片自动识别
- 🔍 **快速搜索** - 历史记录秒级检索，支持正则
- 📝 **智能提取** - 从网页复制时自动提取标题、链接、正文
- 🗑️ **隐私保护** - 一键清理敏感信息（手机号、身份证、密钥）
- 📊 **使用统计** - 查看自己每天复制最多的类型
- 🚀 **快捷键神器** - `Ctrl+Shift+V` 唤起，模糊搜索

## 🚀 快速开始

```bash
# 安装 uv（如果没有安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆仓库
git clone git@github.com:Kailoinf/clipboard-painter.git
cd clipboard-painter

# 验证安装（可选）
python verify.py

# 安装依赖（uv 会自动创建虚拟环境）
uv sync

# 启动剪贴板监听
uv run python src/clipboard_daemon.py

# 或直接运行（如果已激活虚拟环境）
python src/clipboard_daemon.py

# 在另一个终端启动 GUI 搜索界面
uv run python src/gui.py
```

## 🎯 使用示例

### 1. 监听剪贴板
```bash
python src/clipboard_daemon.py
```
- 自动监听剪贴板变化
- 自动分类内容类型
- 自动识别敏感信息
- 每积累10条记录批量写入数据库

### 2. 搜索历史记录
```bash
python src/gui.py
```
- 按关键词搜索
- 按类型过滤
- 按 `Esc` 关闭窗口

### 3. 查看日志
```bash
tail -f logs/$(date +%Y-%m-%d).log
```

## 📁 项目结构

```
clipboard-painter/
├── src/
│   ├── clipboard_daemon.py   # 剪贴板监听守护进程
│   ├── classifier.py         # 内容分类（URL/代码/文本/图片）
│   ├── sanitizer.py          # 敏感信息清理
│   └── gui.py                # 快捷键唤起界面
├── data/
│   └── clipboard.db          # SQLite 数据库
└── config/
    └── rules.yaml            # 自定义分类规则
```

## 💡 使用场景

- **开发** - 快速找回之前复制的代码片段
- **写作** - 自动分类资料，不再乱成一团
- **资料收集** - 从网页复制时自动提取结构化信息
- **日常办公** - 隐私信息自动脱敏，复制更安心

## 🛠️ 技术栈

- Python 3.10+
- uv（现代 Python 包管理器）
- SQLite
- Tkinter（GUI）
- Pyperclip（剪贴板操作）

## 📄 License

MIT

## ⚠️ 已知限制

- 仅支持 Linux/macOS（Windows 需要额外的剪贴板库）
- GUI 基于 Tkinter，界面较为简陋
- 大量复制场景下可能会有轻微延迟（批处理优化后已改善）
- 不支持图片剪贴板（仅文本）

## 🚀 Roadmap

- [ ] 图片剪贴板支持
- [ ] 基于现代 GUI 框架重构界面
- [ ] 云端同步
- [ ] 智能分类规则自定义（通过 GUI）
- [ ] Markdown 导出
- [ ] 定时备份
- [ ] 浏览器扩展（自动提取网页内容）

---

**Made with ❄️ by Kailoinf**
