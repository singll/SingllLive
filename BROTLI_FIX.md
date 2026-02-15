# brotli 兼容性问题修复指南

## 问题描述

Python 3.14 运行时出现错误：
```
TypeError: process() takes exactly 1 argument (2 given)
aiohttp.client_exceptions.ClientPayloadError: 400, Can not decode content-encoding: br
```

## 根本原因

1. **brotli 库 API 变化**: Python 3.14+ 中 brotli 的 `process()` 方法签名改变
2. **aiohttp 兼容性**: aiohttp 3.9.x 调用了不兼容的 API
3. **blivedm 影响**: blivedm 的内部 aiohttp 会话请求 brotli 压缩

## 解决方案

### Step 1: 卸载 brotli（如果已安装）
```bash
pip uninstall brotli -y
```

### Step 2: 重新安装依赖
```bash
# 使用 --prefer-binary 避免编译问题
pip install --prefer-binary -r requirements.txt
```

### Step 3: 验证安装

确认以下依赖版本：
```bash
pip show aiohttp blivedm
# aiohttp 应该是 3.8.x 或 3.9.x
# blivedm 应该是 0.6.x 或 0.7.x
# brotli 应该 NOT 被安装
```

### Step 4: 运行程序
```bash
python cyber_live.py
```

## 技术实现

### 1. 移除 brotli 依赖
- `requirements.txt` 不再列出 brotli
- aiohttp 在没有 brotli 的情况下运行，不会在 Accept-Encoding 中请求 'br'
- B站 API 服务器就不会返回 brotli 压缩的响应

### 2. 全局补丁（防御性）
- `modules/brotli_patch.py` 提供额外保护
- 即使 brotli 被意外安装为其他包的依赖，也能禁用其使用
- 强制 Accept-Encoding 为 'gzip, deflate'

### 3. 早期导入
- `cyber_live.py` 在最开始导入 brotli_patch
- 确保补丁在 blivedm 创建会话之前就被应用

## 如果问题仍然存在

如果卸载 brotli 后仍然看到 brotli 相关错误：

### 方案 A: 强制重建环境
```bash
# 完全移除虚拟环境
deactivate
rmvenv venv  # 或 rm -rf venv

# 创建新虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 重新安装依赖
pip install --prefer-binary -r requirements.txt
```

### 方案 B: 检查是否有其他包依赖 brotli
```bash
pip show brotli  # 如果显示 Required-by: 其他包，说明被依赖

# 查看完整依赖树
pip install pipdeptree
pipdeptree | grep -A 5 brotli
```

### 方案 C: 强制安装兼容版本
```bash
# 如果 brotli 必须被安装，使用旧版本
pip install "brotli<1.1"
```

## 预期结果

修复后应该看到：
```
[时间] danmaku  支持命令: 点歌/切歌/当前/歌单/PK
[时间] blivedm  room=<直播间号> 已连接
[时间] vlc      VLC 已启动
[时间] panel    面板渲染服务启动
```

**不再出现** brotli 解压错误！

## 兼容性信息

| 组件 | 版本 | 备注 |
|------|------|------|
| Python | 3.8 - 3.14+ | ✅ 完全支持 |
| aiohttp | 3.8.0 - 3.9.x | ✅ gzip/deflate 压缩 |
| brotli | ❌ 不需要 | 禁用 br 压缩 |
| blivedm | 0.6.0+ | ✅ 兼容 |
| bilibili-api-python | 0.15.0+ | ✅ 兼容 |
| Pillow | 9.0.0+ | ✅ 兼容 |

