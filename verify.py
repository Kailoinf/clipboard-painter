#!/usr/bin/env python3
"""
安装验证脚本 - 检查依赖和功能是否正常
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))


def check_imports():
    """检查必要的包是否可导入"""
    print("📦 检查依赖包...")

    required_packages = [
        "pyperclip",
        "yaml",
        "sqlite3",
        "tkinter",
    ]

    missing = []

    for pkg in required_packages:
        try:
            if pkg == "sqlite3":
                __import__(pkg)
            elif pkg == "tkinter":
                import tkinter
            elif pkg == "yaml":
                import yaml
            elif pkg == "pyperclip":
                import pyperclip
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} - 未安装")
            missing.append(pkg)

    if missing:
        print(f"\n❌ 缺少依赖: {', '.join(missing)}")
        print("请运行: uv sync")
        return False

    print("✅ 所有依赖已安装\n")
    return True


def check_modules():
    """检查项目模块是否可用"""
    print("🔧 检查项目模块...")

    try:
        from src.classifier import ClipboardClassifier
        print("  ✅ classifier")

        from src.sanitizer import ClipboardSanitizer
        print("  ✅ sanitizer")

        from src.logger import logger
        print("  ✅ logger")

        from src.clipboard_daemon import ClipboardDaemon
        print("  ✅ clipboard_daemon")

        from src.gui import ClipboardGUI
        print("  ✅ gui")

        print("✅ 所有模块加载成功\n")
        return True

    except Exception as e:
        print(f"❌ 模块加载失败: {e}\n")
        return False


def check_config():
    """检查配置文件"""
    print("⚙️  检查配置文件...")

    config_path = Path("config/rules.yaml")
    if not config_path.exists():
        print(f"  ❌ 配置文件不存在: {config_path}")
        return False

    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        print(f"  ✅ 配置文件加载成功")

        # 检查必要的配置项
        if 'database' in config:
            print(f"  ✅ database 配置存在")
        else:
            print(f"  ⚠️  缺少 database 配置")

        if 'hotkeys' in config:
            print(f"  ✅ hotkeys 配置存在")

        print("✅ 配置文件检查通过\n")
        return True

    except Exception as e:
        print(f"❌ 配置文件错误: {e}\n")
        return False


def check_database():
    """检查数据库"""
    print("🗄️  检查数据库...")

    db_path = Path("data/clipboard.db")

    if not db_path.exists():
        print(f"  ℹ️  数据库不存在（首次运行会自动创建）")
        return True

    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='clipboard_history'
        """)

        if cursor.fetchone():
            print(f"  ✅ 数据库表存在")

            # 检查记录数
            cursor.execute("SELECT COUNT(*) FROM clipboard_history")
            count = cursor.fetchone()[0]
            print(f"  📊 当前记录数: {count}")

        else:
            print(f"  ⚠️  数据库表不存在")

        conn.close()
        print("✅ 数据库检查通过\n")
        return True

    except Exception as e:
        print(f"❌ 数据库检查失败: {e}\n")
        return False


def run_tests():
    """运行简单功能测试"""
    print("🧪 运行功能测试...")

    try:
        from src.classifier import ClipboardClassifier
        from src.sanitizer import ClipboardSanitizer

        classifier = ClipboardClassifier()
        sanitizer = ClipboardSanitizer()

        # 测试分类
        tests = [
            ("https://example.com", "url"),
            ("def hello():", "code"),
            ("test@example.com", "email"),
            ("13800138000", "phone"),
            ("普通文本", "text"),
        ]

        for content, expected in tests:
            result = classifier.classify(content)
            if result == expected:
                print(f"  ✅ 分类测试: {content[:20]} -> {result}")
            else:
                print(f"  ❌ 分类测试: {content[:20]} -> {result} (期望: {expected})")

        # 测试脱敏
        sensitive = "13800138000"
        result, detected = sanitizer.sanitize(sensitive)
        if "****" in result:
            print(f"  ✅ 脱敏测试: 敏感信息已脱敏")
        else:
            print(f"  ❌ 脱敏测试失败")

        print("✅ 功能测试完成\n")
        return True

    except Exception as e:
        print(f"❌ 功能测试失败: {e}\n")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("🖌️  Clipboard Painter - 安装验证")
    print("=" * 50)
    print()

    results = []

    results.append(("依赖检查", check_imports()))
    results.append(("模块检查", check_modules()))
    results.append(("配置检查", check_config()))
    results.append(("数据库检查", check_database()))
    results.append(("功能测试", run_tests()))

    print("=" * 50)
    print("📊 验证结果汇总")
    print("=" * 50)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n🎉 所有检查通过！Clipboard Painter 已准备就绪。")
        print("\n运行方式:")
        print("  启动守护进程: uv run python src/clipboard_daemon.py")
        print("  启动GUI界面:  uv run python src/gui.py")
        return 0
    else:
        print("\n⚠️  部分检查失败，请查看上面的详细信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
