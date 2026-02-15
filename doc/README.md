# 📚 SingllLive 文档指南

欢迎来到 SingllLive 直播系统！本目录包含 4 个核心文档。根据你的需求选择：

---

## 🚀 快速开始？→ [QUICK_START.md](QUICK_START.md)

**适合：** 想快速配置和启动的用户

**包含内容：**
- ⚡ 5分钟快速上手
- 🔧 基本配置步骤
- ✅ 功能验证清单

**推荐阅读：** 首先读这个！

---

## 🎬 OBS 场景配置？→ [OBS_NESTED_SCENE_FINAL.md](OBS_NESTED_SCENE_FINAL.md)

**适合：** 需要配置 OBS 场景和脚本的用户

**包含内容：**
- 🎨 4 场景嵌套架构
- 📍 源配置和位置设置
- 🔧 Lua 脚本配置
- ✓ Plan A 源名称规范

**推荐阅读：** OBS 配置必看！

---

## 🔌 Plan A 技术实现？→ [PLAN_A_FILE_SYSTEM_IMPLEMENTATION.md](PLAN_A_FILE_SYSTEM_IMPLEMENTATION.md)

**适合：** 想深入了解 Plan A（文件系统模式）的技术细节

**包含内容：**
- 🎯 Plan A 工作原理
- 📂 目录结构和配置
- 🔄 模式切换流程
- 🧪 故障排除指南
- 💾 .m3u 文件格式说明

**推荐阅读：** 技术细节和调试用！

---

## 📖 系统完整指南？→ [singll-live-guide.md](singll-live-guide.md)

**适合：** 想全面了解整个系统的用户

**包含内容：**
- 📋 系统概述和核心功能
- 🎨 屏幕布局和 ABC 区域
- ⚙️ 完整配置详解
- 🔄 工作流程说明
- 🐛 故障排查指南
- 📊 API 参考

**推荐阅读：** 深入学习整个系统！

---

## 📋 文档导航表

| 文档 | 大小 | 适合场景 | 阅读时间 |
|------|------|---------|---------|
| [QUICK_START.md](QUICK_START.md) | 10KB | 🟢 快速上手 | 5 分钟 |
| [OBS_NESTED_SCENE_FINAL.md](OBS_NESTED_SCENE_FINAL.md) | 17KB | 🔵 OBS 配置 | 15 分钟 |
| [PLAN_A_FILE_SYSTEM_IMPLEMENTATION.md](PLAN_A_FILE_SYSTEM_IMPLEMENTATION.md) | 12KB | 🟠 技术细节 | 20 分钟 |
| [singll-live-guide.md](singll-live-guide.md) | 21KB | 🟣 完整指南 | 30 分钟 |

---

## 🎯 按角色选择

### 👨‍💻 我是开发者，想快速上手
1. 读 [QUICK_START.md](QUICK_START.md) - 5 分钟了解流程
2. 配置 OBS - 按 [OBS_NESTED_SCENE_FINAL.md](OBS_NESTED_SCENE_FINAL.md) 操作
3. 启动并测试

### 🎬 我需要配置 OBS
1. 读 [OBS_NESTED_SCENE_FINAL.md](OBS_NESTED_SCENE_FINAL.md) 的"场景配置步骤"
2. 复制脚本文件到 OBS
3. 配置源和属性
4. 启用脚本和配置

### 🔧 我需要调试系统
1. 读 [PLAN_A_FILE_SYSTEM_IMPLEMENTATION.md](PLAN_A_FILE_SYSTEM_IMPLEMENTATION.md) 的"故障排除"
2. 检查日志输出
3. 验证文件和目录
4. 查看 [singll-live-guide.md](singll-live-guide.md) 的故障排查章节

### 📚 我想深入理解架构
1. 从 [singll-live-guide.md](singll-live-guide.md) 开始了解整个系统
2. 读 [PLAN_A_FILE_SYSTEM_IMPLEMENTATION.md](PLAN_A_FILE_SYSTEM_IMPLEMENTATION.md) 理解技术实现
3. 读 [OBS_NESTED_SCENE_FINAL.md](OBS_NESTED_SCENE_FINAL.md) 理解 OBS 集成

---

## 💡 关键概念速查

### Plan A 是什么？
➜ 读 [PLAN_A_FILE_SYSTEM_IMPLEMENTATION.md](PLAN_A_FILE_SYSTEM_IMPLEMENTATION.md) 的"Overview"

### 模式系统如何工作？
➜ 读 [singll-live-guide.md](singll-live-guide.md) 的"工作流程"

### OBS 场景如何配置？
➜ 读 [OBS_NESTED_SCENE_FINAL.md](OBS_NESTED_SCENE_FINAL.md) 的"场景结构"

### .m3u 播放列表是什么？
➜ 读 [PLAN_A_FILE_SYSTEM_IMPLEMENTATION.md](PLAN_A_FILE_SYSTEM_IMPLEMENTATION.md) 的".m3u 播放列表格式"

### 如何快速启动？
➜ 读 [QUICK_START.md](QUICK_START.md)

---

## ✅ 推荐阅读顺序

### 第一次使用？
```
1. QUICK_START.md              (了解基本流程)
   ↓
2. OBS_NESTED_SCENE_FINAL.md   (配置 OBS)
   ↓
3. 启动系统并测试
```

### 需要深入了解？
```
1. singll-live-guide.md        (系统全景)
   ↓
2. PLAN_A_FILE_SYSTEM_IMPLEMENTATION.md  (技术细节)
   ↓
3. OBS_NESTED_SCENE_FINAL.md   (OBS 配置)
   ↓
4. 阅读源代码进一步学习
```

### 遇到问题？
```
1. 检查日志输出
   ↓
2. 查看相关文档的"故障排除"章节
   ↓
3. 在 singll-live-guide.md 查找完整的故障排查指南
```

---

## 📞 快速链接

- **快速开始:** [QUICK_START.md](QUICK_START.md)
- **OBS 配置:** [OBS_NESTED_SCENE_FINAL.md](OBS_NESTED_SCENE_FINAL.md)
- **技术实现:** [PLAN_A_FILE_SYSTEM_IMPLEMENTATION.md](PLAN_A_FILE_SYSTEM_IMPLEMENTATION.md)
- **完整指南:** [singll-live-guide.md](singll-live-guide.md)

---

## 🎉 开始吧！

👉 **新手推荐:** 从 [QUICK_START.md](QUICK_START.md) 开始，5 分钟快速上手！

📖 **版本**: 2026-02-15 | SingllLive Plan A (文件系统模式)
