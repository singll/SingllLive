# Plan A 实现总结

**状态**：✅ Plan A 已完全实现

> 本文档总结了 SingllLive 直播系统从原始设计到 Plan A（单一 VLC 实例）的优化过程。

---

## 什么是 Plan A？

**Plan A** 是 OBS 4 场景嵌套架构的最优实现方案，核心特点：

### 架构对比

| 维度 | 原始设计 | Plan A |
|------|-------|--------|
| **AScreen 源数** | 5 个 | 4 个 |
| **VLC 实例** | 2 个（分开） | 1 个（共享） |
| **VLC 控制** | OBS 脚本管理 | Python 后端管理 |
| **源配置** | playback_video, song_request_video 分开 | vlc_player 单一 |
| **轮播模式** | 显示 playback_video | 显示 vlc_player |
| **点歌模式** | 显示 song_request_video | 显示 vlc_player |

### Plan A 优势

✅ **架构简洁**
- 减少一个源，逻辑更清晰
- AScreen 只有 4 个源：vlc_player, lyrics_display, broadcast_screen, pk_background

✅ **职责分明**
- Python 后端：完全控制 VLC 内容切换（轮播库 → 点歌 → 暂停）
- OBS 脚本：只负责源的显示/隐藏

✅ **易于维护**
- 添加新模式时只需修改 OBS 脚本配置
- VLC 内容切换逻辑集中在后端，不分散

✅ **性能更优**
- 减少 OBS 资源占用
- 后端对 VLC 的控制更精准

---

## 已完成的修改

### 1. 脚本修改 ✅

**文件**: `/home/ubuntu/SingllLive/scripts/obs/ascreen_source_switcher.lua`

**更改内容**：
```lua
-- 原始：5 个源
local ascreen_sources = {
    playback_video = "轮播视频源",
    lyrics_display = "歌词/播放器显示",
    song_request_video = "点歌视频/MV源",
    broadcast_screen = "直播画面源",
    pk_background = "PK背景源",
}

-- Plan A：4 个源（vlc_player 单一实例）
local ascreen_sources = {
    vlc_player = "VLC播放器（唯一实例）",
    lyrics_display = "歌词/播放器显示",
    broadcast_screen = "直播画面源",
    pk_background = "PK背景源",
}
```

**模式配置**：
```lua
-- 轮播模式
playback = {
    vlc_player = true,        -- 显示（播放歌曲库）
    lyrics_display = true,
    broadcast_screen = false,
    pk_background = false,
},

-- 点歌模式
song_request = {
    vlc_player = true,        -- 显示（播放点的歌曲）
    lyrics_display = true,
    broadcast_screen = false,
    pk_background = false,
},

-- 直播模式
broadcast = {
    vlc_player = false,       -- 隐藏（VLC暂停）
    lyrics_display = false,
    broadcast_screen = true,
    pk_background = false,
},

-- PK 模式
pk = {
    vlc_player = false,       -- 隐藏（VLC暂停）
    lyrics_display = false,
    broadcast_screen = false,
    pk_background = true,
},
```

### 2. 文档更新 ✅

#### OBS_NESTED_SCENE_FINAL.md
- ✅ 脚本工作流程更新为 Plan A 说明
- ✅ AScreen 源配置更新为 Plan A（4 个源）
- ✅ 脚本源配置说明更新
- ✅ 配置清单更新
- ✅ 测试步骤更新为 Plan A 流程

#### MIGRATION_TO_NESTED_SCENES.md
- ✅ 添加 Plan A 更新说明
- ✅ 步骤 2 中的 VLC 源重命名为 vlc_player
- ✅ 添加 Q5：Plan A 和原方案的区别

#### OBS_NESTED_SCENE_PLAN.md
- ✅ 添加 Plan A 推荐提示
- ✅ 链接到 OBS_NESTED_SCENE_FINAL.md

---

## 实现步骤（针对新用户）

### 1️⃣ OBS 场景配置

**MScreen（主场景）**:
- background.png (最底)
- AScreen (嵌套)
- BScreen (嵌套)
- CScreen (嵌套)
- frame-overlay.png (最顶)

**AScreen（A区视频 - Plan A）**:
```
1. vlc_player (VLC 唯一实例)
   位置: (18, 18), 大小: 1344×756
   配置: ☑循环 ☑随机

2. lyrics_display (歌词显示)
   位置: (18, 18), 大小: 1344×756

3. broadcast_screen (直播画面)
   位置: (18, 18), 大小: 1344×756

4. pk_background (PK背景)
   位置: (18, 18), 大小: 1344×756

初始状态: 全部隐藏
```

**BScreen（B区面板）**:
- panel.png 图像源

**CScreen（C区虚拟人）**:
- VTubeStudio 窗口或房间背景

### 2️⃣ OBS 脚本配置

**安装脚本**:
```
OBS → 工具 → 脚本 → Lua脚本 → [+]
选择: SingllLive\scripts\obs\ascreen_source_switcher.lua

属性配置:
  Mode文件路径: data/mode.txt
  AScreen场景名称: AScreen
  检查间隔: 1000
```

### 3️⃣ 测试验证

```bash
# 启动系统
python cyber_live.py

# 测试模式切换
弹幕: "轮播模式"
观察: vlc_player 显示 ✓, lyrics_display 显示 ✓

弹幕: "直播模式"
观察: vlc_player 隐藏 ✗, broadcast_screen 显示 ✓

弹幕: "点歌 歌名"
观察: vlc_player 显示 ✓（播放点的歌曲 - 后端控制）
```

---

## VLC 内容控制（后端工作流）

Plan A 中，VLC 内容切换完全由 Python 后端控制：

```
模式切换 (mode.txt 更新)
    ↓
cyberlive.py 检测模式变化
    ↓
调用 VLC 对应操作：
  - playback: 播放歌曲库（循环、随机）
  - song_request: 自动切换到点的歌曲
  - broadcast/pk: 暂停（保持播放列表）
    ↓
OBS 脚本检测 mode.txt
    ↓
设置 vlc_player 显示/隐藏
    ↓
画面无缝切换 ✓
```

### 关键文件

- **modules/modes.py**: 模式管理和优先级
- **modules/vlc_control.py**: VLC 播放控制
- **cyber_live.py**: 模式自动切换和 VLC 管理
- **scripts/obs/ascreen_source_switcher.lua**: OBS 脚本（Plan A）

---

## 源名称规范（重要）

OBS 中必须使用这些源名称（区分大小写）：

| 源名称 | 用途 | 模式 |
|--------|------|------|
| `vlc_player` | VLC 播放器（唯一实例） | playback, song_request |
| `lyrics_display` | 歌词/播放器显示 | playback, song_request |
| `broadcast_screen` | 直播画面 | broadcast |
| `pk_background` | PK 背景 | pk |

**检查方法**:
1. OBS → AScreen → 源列表
2. 查看每个源的准确名称
3. 确保与上表完全一致（大小写敏感）

---

## 常见问题

### Q: 为什么要用单一 VLC？

A: 因为我们的直播系统在切换模式时，VLC 的内容也需要跟着变化（轮播库 vs 点的歌），而不是用两个不同的视频源。单一 VLC 由后端自动管理播放内容，OBS 脚本只需控制显示/隐藏。

### Q: vlc_player 在轮播和点歌时都显示，怎么区分内容？

A: 内容切换由 Python 后端完全控制。当切换到点歌模式时，后端会：
1. 更新 mode.txt 为 "song_request"
2. 控制 VLC 自动切换到用户点的歌曲
3. OBS 脚本显示 vlc_player（内容已由 VLC 自动切换好）

### Q: 如果要添加新的模式怎么办？

A: 在 ascreen_source_switcher.lua 中添加新的模式配置：

```lua
local mode_source_config = {
    -- ... 现有模式 ...

    -- 新模式示例
    new_mode = {
        vlc_player = true,      -- 或 false
        lyrics_display = false, -- 或 true
        broadcast_screen = false,
        pk_background = false,
    },
}
```

然后在 Python 后端对应的模式处理中调用即可。

---

## 验证清单

实施 Plan A 时，请检查以下项目：

```
场景结构:
☐ MScreen 是主场景
☐ MScreen 包含 AScreen/BScreen/CScreen 嵌套
☐ AScreen/BScreen/CScreen 始终可见（都在 MScreen 中）

源配置:
☐ AScreen 有 4 个源（不是 5 个）
☐ VLC 源名称为 "vlc_player"
☐ 不存在 "playback_video" 或 "song_request_video"
☐ 其他源名称正确

脚本:
☐ ascreen_source_switcher.lua 已加载
☐ 脚本中 mode_source_config 使用 vlc_player
☐ panel_refresh.lua 已加载

数据文件:
☐ data/mode.txt 存在且可写
☐ 初始内容为 "playback" 或其他模式

功能验证:
☐ 轮播模式：vlc_player 显示
☐ 点歌模式：vlc_player 显示（内容由后端切换）
☐ 直播模式：vlc_player 隐藏，broadcast_screen 显示
☐ PK 模式：pk_background 显示
☐ 画面切换无黑屏或闪烁
```

---

## 文件修改记录

| 文件 | 修改项 | 状态 |
|------|--------|------|
| ascreen_source_switcher.lua | 源配置更新为 Plan A | ✅ |
| OBS_NESTED_SCENE_FINAL.md | 全面更新为 Plan A | ✅ |
| MIGRATION_TO_NESTED_SCENES.md | 添加 Plan A 说明 | ✅ |
| OBS_NESTED_SCENE_PLAN.md | 添加 Plan A 推荐 | ✅ |
| visibility_switcher.lua | 不涉及（场景级别） | - |
| panel_refresh.lua | 不涉及（面板刷新） | - |

---

## 后续扩展

### 如果要显示多个源同时

Plan A 也支持同时显示多个源。例如，轮播时同时显示 VLC + 虚拟人跳舞：

```lua
playback = {
    vlc_player = true,        -- VLC 播放歌曲
    lyrics_display = true,    -- 显示歌词
    broadcast_screen = false,
    pk_background = false,
    -- CScreen 的虚拟人也可以通过独立逻辑显示
},
```

### 如果要添加新的源类型

1. 在 AScreen 中添加新源（在 OBS 中）
2. 在脚本的 `ascreen_sources` 表中声明
3. 在对应模式的 `mode_source_config` 中配置显示/隐藏

```lua
local ascreen_sources = {
    vlc_player = "VLC播放器（唯一实例）",
    lyrics_display = "歌词/播放器显示",
    broadcast_screen = "直播画面源",
    pk_background = "PK背景源",
    comments_display = "评论显示",  -- 新增
}

-- 在模式中配置
song_request = {
    vlc_player = true,
    lyrics_display = true,
    broadcast_screen = false,
    pk_background = false,
    comments_display = true,  -- 点歌时显示评论
},
```

---

## 总结

Plan A 是 SingllLive 直播系统的最优配置方案：

✅ **更简洁** - 4 个源代替 5 个
✅ **职责分明** - 后端控制内容，OBS 控制显示
✅ **易维护** - 配置集中，逻辑清晰
✅ **高效能** - 减少资源占用和系统开销
✅ **可扩展** - 易于添加新模式和源

**立即开始**：按照本文档的实现步骤，您可以在 10 分钟内完成 Plan A 的配置！

---

**文档版本**: 1.0
**最后更新**: 2026-02-15
**维护者**: SingllLive Team
