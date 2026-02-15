# blivedm 安装问题诊断指南

## 问题描述

当安装依赖时，可能遇到以下错误：

```
ERROR: Could not find a version that satisfies the requirement blivedm>=0.6.0
(from versions: 0.1.0, 0.1.1)
ERROR: No matching distribution found for blivedm>=0.6.0
```

## 根本原因

**PyPI 上的 `blivedm` 包是完全不同的项目** (版本仅有 0.1.0, 0.1.1)。

我们实际需要的 `blivedm` 库是 B站弹幕解析库，由 Nayuki 维护，托管在 GitHub 上，而不是 PyPI。

| 来源 | 版本 | 说明 |
|------|------|------|
| **PyPI** (错误) | 0.1.0, 0.1.1 | 完全不同的包，无关项目 |
| **GitHub** (正确) | 0.6.x+ | B站弹幕客户端库 |

## 解决方案

### 方案 1: 自动方案 (推荐)

确保 `requirements.txt` 包含 GitHub 安装地址：

```txt
git+https://github.com/xfgryujk/blivedm.git@master
```

然后运行：

```bash
pip install --prefer-binary -r requirements.txt
```

**前置条件:**
- Python 3.8+ 已安装
- Git 已安装
- 能访问 GitHub.com

### 方案 2: 手动克隆安装

如果网络慢或不稳定，可先克隆再离线安装：

```bash
# 1. 克隆仓库
git clone https://github.com/xfgryujk/blivedm.git

# 2. 安装本地仓库
pip install ./blivedm

# 3. 安装其他依赖
pip install --prefer-binary bilibili-api-python aiohttp Pillow
```

### 方案 3: Windows 特定问题处理

如果在 Windows 上安装失败，常见原因：

#### 3a. Git 未安装

```bash
# 检查 Git 是否已安装
git --version

# 如果未安装，下载并安装 Git for Windows
# https://git-scm.com/download/win
```

#### 3b. C++ 编译工具缺失 (可能需要)

某些包可能需要编译，如果遇到 "error: Microsoft Visual C++ 14.0 is required"：

```bash
# 方案 1: 安装 Visual C++ Build Tools
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# 方案 2: 使用 pre-built wheels (如果可用)
pip install --prefer-binary -r requirements.txt
```

#### 3c. 网络或防火墙问题

如果无法访问 GitHub：

```bash
# 测试网络连接
ping github.com

# 或尝试使用国内镜像 (可选)
pip install -i https://pypi.tsinghua.edu.cn/simple -r requirements.txt
```

## 验证安装

安装完成后，验证 blivedm 是否正确安装：

```bash
python -c "import blivedm; print(f'blivedm 已安装: {blivedm.__version__}')"
```

或检查能否导入关键模块：

```bash
python -c "from blivedm import BLiveClient; print('BLiveClient 导入成功')"
```

## requirements.txt 说明

当前 `requirements.txt` 文件格式：

```txt
# B站弹幕相关
# blivedm 不在 PyPI 上维护，从 GitHub 安装
git+https://github.com/nayuki/blivedm.git@master
bilibili-api-python>=0.15.0

# 其他依赖...
```

**注意:**
- `git+https://...` 形式会自动从 GitHub 克隆并安装
- `@master` 指定分支 (可改为具体版本号)
- 如果 GitHub URL 变更，需更新此文件

## 常见问题

### Q: 安装很慢，我应该怎么做？

**A:** blivedm 需要从源码构建，速度会比 pre-built wheels 慢：
- 这是正常的，通常需要 1-5 分钟
- 确保网络稳定
- 可使用手动克隆方案 (方案 2)

### Q: 我在国内，GitHub 访问很慢怎么办？

**A:** 可选方案：
1. 使用代理加速服务
2. 手动克隆到本地后离线安装
3. 等网络好的时候安装

### Q: 我已经安装了 PyPI 上的错误的 blivedm，应该怎么办？

**A:** 卸载并重新安装：

```bash
pip uninstall blivedm -y
pip install git+https://github.com/xfgryujk/blivedm.git@master
```

### Q: 我可以改用其他 blivedm Fork 吗？

**A:** 可以，但需确保 API 兼容。常见替代方案：

```txt
# 官方维护版本 (推荐)
git+https://github.com/xfgryujk/blivedm.git@master

# 其他 Fork (需验证 API 兼容性)
git+https://github.com/Akegarasu/blivedm-go.git
```

修改后务必测试 `cyber_live.py` 是否正常运行。

## 如果以上都不行

如果所有方案都失败，请：

1. **收集诊断信息:**

```bash
python --version
git --version
pip --version
pip install -v git+https://github.com/nayuki/blivedm.git@master 2>&1 | tee install.log
```

2. **检查错误日志** (install.log)

3. **提交 Issue** 并附带：
   - `install.log` 内容
   - Python/Git/pip 版本
   - 操作系统信息 (Windows 10/11 etc.)
   - 网络环境说明 (是否使用代理/VPN)

## 参考链接

- [官方 blivedm 仓库](https://github.com/xfgryujk/blivedm)
- [Git 下载](https://git-scm.com/)
- [pip 文档 - 从 VCS 安装](https://pip.pypa.io/en/stable/topics/vcs-support/)
