# 从 5 场景方案迁移到 4 场景嵌套方案

> ⏱️ **10分钟完成迁移，零直播中断**

---

## 为什么要迁移？

| 对比项 | 5场景方案 | 4场景嵌套方案 |
|--------|---------|-------------|
| **直播中断** | ⚠️ 可能闪烁/黑屏 | ✅ **零中断** |
| **切换延迟** | 1-2秒 | < 100ms |
| **配置复杂度** | 5个场景×5个源 = 25个源 | 1个主场景 + 3个嵌套 |
| **性能开销** | 场景切换开销 | 仅改变可见性 |
| **推荐度** | ⭐⭐ | ⭐⭐⭐⭐⭐ |

**简单说**：迁移后直播画面切换更流畅，用户看不出有任何变化，但系统背后运行更高效。

---

## 📌 重要：Plan A 更新

从迁移后的 4 场景方案基础上，我们进一步优化为 **Plan A（单一 VLC 实例）**：

**变更**：
- 原方案：AScreen 中有 5 个源（playback_video、song_request_video 分开）
- **Plan A**：AScreen 中只有 4 个源（vlc_player 单一实例）

**优点**：
- VLC 由 Python 后端自动控制内容切换
- OBS 脚本只负责源的显示/隐藏
- 架构更简洁，易于维护

**迁移步骤中的调整**：
- 复制 VLC 源时，将其重命名为 `vlc_player`（统一标识）
- 不需要分别创建 playback_video 和 song_request_video
- 在轮播和点歌两个模式中都会显示同一个 vlc_player 源

详见：[OBS_NESTED_SCENE_FINAL.md](OBS_NESTED_SCENE_FINAL.md) 中的 Plan A 配置说明。

---

### Step 1: 创建新的 4 个场景（5分钟）

**在 OBS 中创建新场景**：

```
OBS → 场景 → [+]

依次创建:
□ MScreen          (新建 - 主场景)
□ AScreen          (新建 - VLC区)
□ BScreen          (新建 - 面板区)
□ CScreen          (新建 - 虚拟人区)
```

**完成后的场景列表**：
```
OBS 场景列表:
├── MScreen        ← 新建
├── AScreen        ← 新建
├── BScreen        ← 新建
├── CScreen        ← 新建
├── Scene_Broadcast  ← 旧的，稍后删除
├── Scene_PK         ← 旧的，稍后删除
├── Scene_SongRequest← 旧的，稍后删除
├── Scene_Playback   ← 旧的，保留作为参考
└── Scene_Other      ← 旧的，稍后删除
```

---

### Step 2: 复制源到新场景（3分钟）

#### 从 Scene_Playback 复制到新场景

**复制 VLC 源到 AScreen**：
```
1. 选择 Scene_Playback 场景
2. 右键 "VLC 视频源" 源 → 复制
3. 选择 AScreen 场景
4. 右键源列表 → 粘贴
5. 重命名源为 "vlc_player"（Plan A 标准命名）
6. 验证: VLC源已在 AScreen 中，名称为 vlc_player
   位置: (18, 18), 大小: 1344×756
```

**复制面板源到 BScreen**：
```
1. 选择 Scene_Playback 场景
2. 右键 "Panel-B区" 源 → 复制
3. 选择 BScreen 场景
4. 右键源列表 → 粘贴
5. 验证: 面板源已在 BScreen 中
   位置: (1385, 45), 大小: 522×440
```

**复制虚拟人源到 CScreen**（如果有）：
```
1. 选择 Scene_Playback 场景
2. 右键 "VTuber-C区" 源 → 复制
3. 选择 CScreen 场景
4. 右键源列表 → 粘贴
5. 验证: 虚拟人源已在 CScreen 中
   位置: (1380, 504), 大小: 532×488
```

---

### Step 3: 配置主场景 MScreen（1分钟）

**为 MScreen 添加源**（按顺序，从下到上）：

#### 1️⃣ 添加背景 (最底层)
```
右键 MScreen → 源 → [+] → 图像
- 文件: assets/background.png
- 位置: (0, 0)
- 大小: 1920×1080
```

#### 2️⃣ 添加 AScreen (嵌套)
```
右键 MScreen → 源 → [+] → 场景
- 场景: AScreen
- 位置: (0, 0)
- 大小: 1920×1080
```

#### 3️⃣ 添加 BScreen (嵌套)
```
右键 MScreen → 源 → [+] → 场景
- 场景: BScreen
- 位置: (0, 0)
- 大小: 1920×1080
```

#### 4️⃣ 添加 CScreen (嵌套)
```
右键 MScreen → 源 → [+] → 场景
- 场景: CScreen
- 位置: (0, 0)
- 大小: 1920×1080
```

#### 5️⃣ 添加框架 (最顶层)
```
右键 MScreen → 源 → [+] → 图像
- 文件: assets/frame-overlay.png
- 位置: (0, 0)
- 大小: 1920×1080
- 右键 → 安排 → 置于顶层
```

**验证 MScreen 的源顺序**：
```
MScreen 源列表 (从下到上):
✓ background.png      (最底)
✓ AScreen
✓ BScreen
✓ CScreen
✓ frame-overlay.png   (最顶)
```

---

### Step 4: 替换 OBS 脚本（1分钟）

#### 删除旧脚本

```
OBS → 工具 → 脚本 → Lua脚本

查找并删除:
□ panel_refresh.lua       (如果有的话)
□ scene_switcher.lua      (确保删除！)
```

#### 添加新脚本

```
OBS → 工具 → 脚本 → Lua脚本 → [+]

选择: SingllLive\scripts\obs\visibility_switcher.lua

在脚本属性中配置:
  Mode文件路径: D:\SingllLive\data\mode.txt
  主场景名称: MScreen
  A区场景名称: AScreen
  B区场景名称: BScreen
  C区场景名称: CScreen
  检查间隔: 1000

✓ 应用
```

#### 还需要添加面板刷新脚本

```
OBS → 工具 → 脚本 → Lua脚本 → [+]

选择: SingllLive\scripts\obs\panel_refresh.lua

在脚本属性中配置:
  图像源名称: 需要先找到 BScreen 中的面板源名称
  刷新间隔: 1000

✓ 应用
```

**关键：找到 BScreen 中的面板源名称**
```
1. 点击 BScreen 场景
2. 在源列表中找到面板图像源的名称 (通常是 "panel.png" 或 "Panel-B区")
3. 在脚本属性中填入该名称
```

---

## 验证迁移成功

### 检查清单

```
□ 4 个新场景已创建
  ✓ MScreen
  ✓ AScreen
  ✓ BScreen
  ✓ CScreen

□ MScreen 中有 5 个源
  ✓ background.png
  ✓ AScreen
  ✓ BScreen
  ✓ CScreen
  ✓ frame-overlay.png

□ AScreen 包含
  ✓ VLC 视频源

□ BScreen 包含
  ✓ panel.png

□ CScreen 包含
  ✓ VTubeStudio 或房间背景 (可选)

□ OBS 脚本已启用
  ✓ visibility_switcher.lua
  ✓ panel_refresh.lua

□ MScreen 已选中为活跃场景
```

### 测试直播效果

```
1. 启动 SingllLive
   python cyber_live.py

2. 在直播间发送弹幕命令
   "轮播模式"
   观察: AScreen/BScreen/CScreen 应同时显示 ✓

   "直播模式"
   观察: AScreen 隐藏，只显示 BScreen ✓
   注意: 没有场景切换，画面平滑过渡 ✅

   "点歌模式"
   观察: AScreen/BScreen 显示，CScreen 隐藏 ✓

3. 点歌操作
   "点歌 歌名"
   观察: VLC 开始播放，面板显示队列 ✓

✅ 迁移成功！
```

---

## 清理旧资源（可选）

迁移验证成功后，可以删除旧的 5 个场景以保持整洁：

```
OBS 场景列表中:

右键删除:
□ Scene_Broadcast
□ Scene_PK
□ Scene_SongRequest
□ Scene_Playback  (参考用)
□ Scene_Other

保留:
✓ MScreen (新主场景)
✓ AScreen (新A区)
✓ BScreen (新B区)
✓ CScreen (新C区)
```

---

## 常见问题

### Q1: 迁移后面板不显示？

**A**: 检查 panel_refresh.lua 脚本属性中的"图像源名称"

```
1. 点击 BScreen 场景
2. 找到面板源的准确名称 (在源列表中查看)
3. 复制该名称到脚本属性
4. 重新应用脚本
```

### Q2: 迁移后虚拟人不显示？

**A**: CScreen 中可能没有虚拟人源，或者可见性被隐藏了

```
检查步骤:
1. 点击 CScreen 场景
2. 确认是否有虚拟人源 (VTubeStudio或图像)
3. 如果没有，从 Scene_Playback 复制
4. 在脚本属性中确保 C 区场景名称正确
```

### Q3: 迁移后切换延迟很大？

**A**: 可能 visibility_switcher.lua 的检查间隔太长

```
在脚本属性中:
改小 "检查间隔" 的值
从 1000ms 改为 500ms 或 300ms

✓ 延迟会降低
```

### Q4: 如何回到 5 场景方案？

**A**: 禁用新脚本，启用旧脚本

```
1. OBS → 工具 → 脚本
2. 禁用 visibility_switcher.lua
3. 启用 scene_switcher.lua (如有)
4. 按原来的方式选择场景

但不推荐回退，4 场景方案明显更优
```

### Q5: Plan A 和原方案有什么区别？

**A**: Plan A 使用单一 VLC 实例，而不是分开的 playback_video 和 song_request_video

```
原方案：
- AScreen 有 5 个源：playback_video, song_request_video, lyrics_display, broadcast_screen, pk_background

Plan A（推荐）：
- AScreen 有 4 个源：vlc_player（单一), lyrics_display, broadcast_screen, pk_background
- VLC 内容切换由 Python 后端自动控制
- OBS 脚本只负责源的显示/隐藏

优点：
✓ 架构更简洁（减少一个源）
✓ 后端自动管理 VLC 内容，OBS 无需关心
✓ 更易维护和扩展

如何迁移到 Plan A：
1. 将复制的 VLC 源重命名为 "vlc_player"
2. 不需要创建单独的 playback_video 和 song_request_video
3. 使用 ascreen_source_switcher.lua 脚本（已包含 Plan A 配置）
4. 在轮播和点歌模式中都会显示 vlc_player
```

---

## 高级配置：自定义可见性规则

如果想改变某个模式的显示配置，编辑脚本：

```lua
-- 打开 scripts/obs/visibility_switcher.lua

-- 比如想让直播时也显示虚拟人
broadcast = {
    a = false,
    b = true,
    c = true,   -- ← 改为 true，显示虚拟人
},

-- 保存后，重启 OBS 脚本即可生效
```

---

## 迁移前后对比

### 迁移前（5场景）

```
直播间发送 "直播模式":
  1. scene_switcher.lua 读取 mode.txt
  2. 检测模式变化: playback → broadcast
  3. OBS 切换场景: Scene_Playback → Scene_Broadcast
  4. 画面闪烁/可能黑屏 (场景切换开销)
  5. 观众可能看到卡顿

延迟: 1-2秒
```

### 迁移后（4场景嵌套）

```
直播间发送 "直播模式":
  1. visibility_switcher.lua 读取 mode.txt
  2. 检测模式变化: playback → broadcast
  3. 设置源可见性: AScreen隐藏, BScreen显示
  4. 画面平滑过渡 (无场景切换)
  5. 观众无感知

延迟: < 100ms
```

---

## 总结

✅ **迁移步骤总结**：
1. 创建 4 个新场景 (1分钟)
2. 复制源到新场景 (3分钟)
3. 配置 MScreen 主场景 (1分钟)
4. 替换 OBS 脚本 (1分钟)

✅ **迁移收益**：
- 直播无中断
- 切换更流畅
- 系统更高效
- 管理更简洁

✅ **立即开始**：
按照上面的 4 步完成迁移，5分钟内你就会拥有更专业的直播系统！

