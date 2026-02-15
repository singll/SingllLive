#!/usr/bin/env python3
"""
SingllLive 依赖安装工具

处理 Windows 上的 brotli 编译问题
"""

import subprocess
import sys
import os

PACKAGES = [
    "blivedm",
    "bilibili-api-python",
    "aiohttp>=3.8.0",
    "Pillow>=9.0.0",
]

def run_command(cmd, description=""):
    """运行命令并返回是否成功"""
    if description:
        print(f"\n{description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"错误: {e}")
        return False

def main():
    print("="*50)
    print("  SingllLive - Python 依赖安装工具")
    print("="*50)
    print()

    # 升级 pip
    print("升级 pip 和 setuptools...")
    run_command(
        f"{sys.executable} -m pip install --upgrade pip setuptools wheel -q",
        ""
    )

    # 尝试方案 1: --only-binary
    print("\n【方案 1】尝试仅使用预编译 wheels...")
    cmd1 = f"{sys.executable} -m pip install --only-binary :all: " + " ".join(PACKAGES)
    if run_command(cmd1):
        print("\n✓ 安装成功！")
        verify_installation()
        return 0

    # 尝试方案 2: --prefer-binary
    print("\n【方案 2】尝试优先使用预编译 wheels（允许回退编译）...")
    cmd2 = f"{sys.executable} -m pip install --prefer-binary " + " ".join(PACKAGES)
    if run_command(cmd2):
        print("\n✓ 安装成功！")
        verify_installation()
        return 0

    # 尝试方案 3: 跳过 brotli
    print("\n【方案 3】跳过 brotli，安装其他依赖...")
    cmd3 = f"{sys.executable} -m pip install --prefer-binary --no-binary brotli " + " ".join(PACKAGES)
    if run_command(cmd3):
        print("\n✓ 安装成功（已跳过 brotli）！")
        verify_installation()
        return 0

    # 全部失败
    print("\n" + "="*50)
    print("  所有安装方案都失败了")
    print("="*50)
    print()
    print("可能的原因:")
    print("  1. Python 版本不符合（需要 3.8+，当前: {})".format(sys.version))
    print("  2. 网络连接问题")
    print("  3. 没有可用的预编译 wheel")
    print()
    print("解决方案:")
    print()
    print("【方案 A】安装 Visual C++ Build Tools")
    print("  访问: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
    print("  安装后重新运行此脚本")
    print()
    print("【方案 B】手动下载 brotli wheel")
    print("  1. 从以下链接下载与你的 Python 版本匹配的 brotli wheel:")
    print("     https://www.lfd.uci.edu/~gohlke/pythonlibs/#brotli")
    print("  2. 运行: pip install 下载的_wheel_文件.whl")
    print("  3. 然后再运行此脚本")
    print()
    print("【方案 C】修改 requirements.txt")
    print("  删除或注释掉导致编译问题的包，使用最小依赖集")
    print()

    return 1

def verify_installation():
    """验证所有包是否安装成功"""
    print("\n验证安装...")
    try:
        import PIL
        import aiohttp
        import blivedm
        print("✓ 所有核心依赖已安装！")
        return True
    except ImportError as e:
        print(f"⚠ 警告: 某个依赖未能正确安装: {e}")
        return False

if __name__ == "__main__":
    sys.exit(main())
