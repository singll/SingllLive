# OBS 4场景嵌套方案（修正版）

## 核心概念修正

AScreen/BScreen/CScreen **始终可见**，只改变它们**内部源的可见性**：

```
MScreen (主场景 - 始终显示)
├── background.png
├── AScreen (始终显示 ⭐)
│   ├── 轮播视频源      (轮播模式: 显示)
│   ├── 播放器歌词源    (轮播/点歌: 显示)
│   ├── 点歌视频/MV源   (点歌模式: 显示)
│   ├── 直播画面源      (直播模式: 显示)
│   └── PK背景源        (PK模式: 显示)
│
├── BScreen (始终显示 ⭐)
│   └── panel.png       (每秒重新渲染，显示对应模式的面板)
│
├── CScreen (始终显示 ⭐)
│   ├── VTubeStudio虚拟人 (可选切换动作)
│   └── 房间背景 (可选)
│
└── frame-overlay.png

模式切换逻辑:
PLAYBACK (轮播):      显示 [轮播视频] + [歌词], 隐藏其他
BROADCAST (直播):     显示 [直播画面], 隐藏其他
SONG_REQUEST (点歌):  显示 [点歌MV] + [歌词], 隐藏其他
PK:                   显示 [PK背景], 隐藏其他
OTHER:                全隐藏
```

---

## 实现步骤

### Step 1: 创建 4 个场景

```
OBS → 场景 → [+]

创建:
□ MScreen
□ AScreen
□ BScreen
□ CScreen
```

---

### Step 2: 配置 AScreen（关键 - Plan A：单一VLC实例）

**添加所有必需的源**（Plan A 方案）：

```
AScreen 中的源列表（共4个源）:

1️⃣ VLC 播放器（唯一实例）
   类型: VLC视频源
   配置: ☑循环播放 ☑随机
   位置: (18, 18)
   大小: 1344×756
   名称: "vlc_player"
   说明: 单一 VLC 实例，由后端自动控制内容切换
        - 轮播模式：播放歌曲库（循环、随机）
        - 点歌模式：自动切换到用户点的歌曲
        - 直播/PK：暂停（保持状态）

2️⃣ 歌词/播放器显示
   类型: 浏览器源 或 图像
   位置: (18, 18)
   大小: 1344×756
   名称: "lyrics_display"
   说明: 显示歌词或播放器信息（轮播/点歌模式显示）

3️⃣ 直播画面源
   类型: 窗口捕获 或 显示器捕获
   位置: (18, 18)
   大小: 1344×756
   名称: "broadcast_screen"
   说明: 显示直播画面（直播模式显示）

4️⃣ PK背景源
   类型: VLC视频源 或 图像/视频
   位置: (18, 18)
   大小: 1344×756
   名称: "pk_background"
   说明: 显示PK背景（PK模式显示）

初始状态: 全部隐藏 ✗
(脚本启动后会根据模式显示对应源)
```

**关键说明**：
- Plan A 只需 4 个源（相比原来的 5 个）
- `vlc_player` 是唯一的 VLC 实例，后端自动控制其内容切换
- 不再需要分别的 `playback_video` 和 `song_request_video` 源
- 源位置和大小都相同，因为同一时刻只显示一个

---

### Step 3: 配置 BScreen

**只需添加一个源**：

```
BScreen 中的源:
1️⃣ 面板图像源
   类型: 图像
   文件: data/panel.png
   位置: (1385, 45)
   大小: 522×440
   名称: "panel_image"

说明:
- panel.png 由 cyber_live.py 每秒重新生成
- 根据当前模式生成不同的内容（面板脚本已实现）
- BScreen 只需显示最新的 panel.png 即可
```

---

### Step 4: 配置 CScreen

**虚拟人/房间场景**：

```
CScreen 中的源:
1️⃣ VTubeStudio窗口 或 房间背景
   类型: 窗口捕获 或 图像
   位置: (1380, 504)
   大小: 532×488
   名称: "vtuber_model" 或 "room_bg"

说明:
- 虚拟人可以切换动作（可选）
- 或保持固定画面
- 本方案不涉及此部分的自动切换
```

---

### Step 5: 配置 MScreen

**组合所有场景**：

```
MScreen 中的源 (从下到上):
1️⃣ background.png
   位置: (0, 0), 大小: 1920×1080

2️⃣ AScreen (嵌套场景)
   位置: (0, 0), 大小: 1920×1080

3️⃣ BScreen (嵌套场景)
   位置: (0, 0), 大小: 1920×1080

4️⃣ CScreen (嵌套场景)
   位置: (0, 0), 大小: 1920×1080

5️⃣ frame-overlay.png
   位置: (0, 0), 大小: 1920×1080
   (置于顶层)
```

---

## Step 6: 创建关键脚本

创建新脚本来控制 **AScreen 内部源的可见性**：

**文件**: `scripts/obs/ascreen_source_switcher.lua`

此脚本的功能：
- 监听 mode.txt 文件变化
- 根据模式配置切换 AScreen 内部源的可见性
- 每个模式下只显示对应的源，其他源隐藏

---

## Step 7: 启用脚本管理 AScreen 源

### 安装脚本

```
OBS → 工具 → 脚本 → Lua脚本 → [+]

选择: SingllLive\scripts\obs\ascreen_source_switcher.lua

在脚本属性中配置:
  Mode文件路径: D:\SingllLive\data\mode.txt
  AScreen场景名称: AScreen
  检查间隔: 1000
  调试模式: ☐ (可选，开启输出详细日志)

✓ 应用
```

### 脚本源配置说明（Plan A）

脚本会自动管理 AScreen 中这些源（共4个）：

```lua
-- 脚本管理的源名称（需要与 OBS 中的源名称完全一致）
vlc_player       -- VLC 播放器（唯一实例，由后端控制）
lyrics_display   -- 歌词/播放器显示
broadcast_screen -- 直播画面源
pk_background    -- PK背景源
```

**重要**：
- OBS 中的源名称必须与脚本中的名称完全一致！
- Plan A 使用单一 `vlc_player` 代替原来的 `playback_video` 和 `song_request_video`
- VLC 内容切换完全由 Python 后端自动控制
- OBS 脚本只负责根据模式显示/隐藏对应的源

---

## Step 8: 添加面板自动刷新脚本

BScreen 中的 panel.png 需要自动刷新：

```
OBS → 工具 → 脚本 → Lua脚本 → [+]

选择: SingllLive\scripts\obs\panel_refresh.lua

在脚本属性中配置:
  图像源名称: panel_image    (BScreen中的面板源名称)
  刷新间隔: 1000

✓ 应用
```

---

## 最终架构图

```
OBS 画面层级:

┌─────────────────────────────────────────────┐
│  frame-overlay.png (框架，最顶层)           │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ MScreen (主场景，始终显示)          │   │
│  │                                     │   │
│  │ ┌─────────────────────────────────┐ │   │
│  │ │ CScreen (虚拟人，始终显示)       │ │   │
│  │ │ ├─ VTubeStudio 窗口              │ │   │
│  │ │ └─ 房间背景 (可选)               │ │   │
│  │ │ (右下角 532×488)                │ │   │
│  │ └─────────────────────────────────┘ │   │
│  │                                     │   │
│  │ ┌─────────────────────────────────┐ │   │
│  │ │ BScreen (面板，始终显示)         │ │   │
│  │ │ ├─ panel.png (动态渲染)          │ │   │
│  │ │ │  显示对应模式的信息            │ │   │
│  │ │ └─ (右侧 522×440)               │ │   │
│  │ │ 脚本: panel_refresh.lua          │ │   │
│  │ └─────────────────────────────────┘ │   │
│  │                                     │   │
│  │ ┌─────────────────────────────────┐ │   │
│  │ │ AScreen (视频，始终显示)         │ │   │
│  │ │ │                               │ │   │
│  │ │ ├─ playback_video   (轮播模式)  │ │   │
│  │ │ ├─ lyrics_display   (歌词显示)  │ │   │
│  │ │ ├─ song_request_video (点歌MV) │ │   │
│  │ │ ├─ broadcast_screen (直播画面)  │ │   │
│  │ │ └─ pk_background    (PK背景)    │ │   │
│  │ │ │                               │ │   │
│  │ │ 脚本: ascreen_source_switcher.lua│ │   │
│  │ │ 只显示当前模式对应的源          │ │   │
│  │ │ (左侧 1344×756)                 │ │   │
│  │ └─────────────────────────────────┘ │   │
│  │                                     │   │
│  │ background.png (背景，最底层)      │   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 脚本工作流程（Plan A：单一VLC实例）

```
流程图:

cyberlive.py                           OBS
    │                                   │
    │ 检测模式变化                      │
    ├─▶ 更新 mode.txt                  │
    │   内容: "song_request"            │
    │                                   ├─▶ ascreen_source_switcher.lua
    │                                   │   定时检查 mode.txt
    │                                   │
    │   VLC 后端控制                    ├─▶ 读取: "song_request"
    │   ↓                               │
    ├─▶ VLC 切换到点的歌曲             ├─▶ 对比旧值: "playback" ≠ "song_request"
    │   (自动播放用户点的歌)            │
    │                                   ├─▶ 隐藏源（playback时的源）:
    │                                   │   broadcast_screen ✗
    │                                   │   pk_background ✗
    │                                   │
    │                                   ├─▶ 显示源（song_request需要的源）:
    │                                   │   vlc_player ✓
    │                                   │   lyrics_display ✓
    │                                   │
    │ 同时重新渲染 panel.png            │
    ├─▶ panel.py 生成                   │   ├─▶ panel_refresh.lua
    │   点歌队列信息                     │   │   自动刷新 panel.png
    │                                   │   │
    │                                   │   └─▶ BScreen 显示新的面板
    │                                   │
    │                                   └─▶ ✅ 直播画面无缝切换
    │
    └─▶ VLC 播放列表继续播放
        （内容由后端自动切换）
```

**关键点 - Plan A 架构**：
- `vlc_player` 是唯一的 VLC 实例，由 Python 后端自动控制内容切换
- 轮播模式：VLC 播放歌曲库（循环、随机）
- 点歌模式：VLC 自动切换到用户点的歌曲（后端控制）
- 直播/PK：VLC 暂停（保持播放列表状态，便于恢复）
- OBS 脚本只负责显示/隐藏对应模式的源，内容切换完全由后端完成

---

## 配置清单

### OBS 场景结构

```
☐ MScreen (主场景)
  ☐ background.png
  ☐ AScreen (嵌套)
  ☐ BScreen (嵌套)
  ☐ CScreen (嵌套)
  ☐ frame-overlay.png

☐ AScreen (A区视频 - Plan A：单一VLC)
  ☐ vlc_player (VLC播放器 - 唯一实例)
  ☐ lyrics_display (歌词显示)
  ☐ broadcast_screen (直播画面)
  ☐ pk_background (PK背景)

☐ BScreen (B区面板)
  ☐ panel_image (panel.png)

☐ CScreen (C区虚拟人)
  ☐ vtuber_model 或 room_bg
```

### OBS 脚本

```
☐ ascreen_source_switcher.lua
  - Mode文件路径: D:\SingllLive\data\mode.txt
  - AScreen场景名称: AScreen
  - 检查间隔: 1000

☐ panel_refresh.lua
  - 图像源名称: panel_image
  - 刷新间隔: 1000
```

---

## 测试步骤（Plan A）

### 1️⃣ 验证源名称

```
1. OBS 中点击 AScreen
2. 查看源面板中的源名称
3. 确认这些名称（Plan A）:
   ✓ vlc_player
   ✓ lyrics_display
   ✓ broadcast_screen
   ✓ pk_background

如果名称不一致，修改脚本或重命名源
注意：不应该有 playback_video 或 song_request_video（已合并为 vlc_player）
```

### 2️⃣ 启动系统

```bash
python cyber_live.py
```

### 3️⃣ 验证脚本加载

```
OBS 日志中应该看到:
✅ A区源切换脚本已加载
✅ 面板刷新脚本已加载

Ctrl+F 搜索 "已加载"
```

### 4️⃣ 测试模式切换（Plan A）

```
发送弹幕: "轮播模式"
观察:
  ✓ vlc_player 显示 ✓ (播放歌曲库)
  ✓ lyrics_display 显示 ✓
  ✓ broadcast_screen 隐藏 ✗
  ✓ pk_background 隐藏 ✗
  ✓ BScreen 显示轮播信息

发送弹幕: "直播模式"
观察:
  ✓ vlc_player 隐藏 ✗ (VLC暂停)
  ✓ broadcast_screen 显示 ✓
  ✓ lyrics_display 隐藏 ✗
  ✓ pk_background 隐藏 ✗
  ✓ BScreen 显示直播信息

发送弹幕: "点歌 歌名"
观察:
  ✓ vlc_player 显示 ✓ (播放点的歌曲 - 后端自动切换)
  ✓ lyrics_display 显示 ✓
  ✓ broadcast_screen 隐藏 ✗
  ✓ pk_background 隐藏 ✗
  ✓ BScreen 显示队列

✅ 所有源切换正确（Plan A 完成）！
```

---

## 自定义模式配置

如果想改变某个模式的源配置，编辑脚本：

**编辑**: `scripts/obs/ascreen_source_switcher.lua`

```lua
-- 比如直播时也显示歌词
broadcast = {
    playback_video = false,
    lyrics_display = true,    -- 改为 true
    song_request_video = false,
    broadcast_screen = true,
    pk_background = false,
},

-- 保存后重启脚本生效
```

---

## 高级配置：添加新源

如果想在模式中添加新的源（比如转播、评论等）：

1. **在 OBS 中添加源到 AScreen**
   ```
   AScreen → [+] → (选择源类型)
   输入源名称: 如 "comments_display"
   ```

2. **在脚本中添加源配置**
   ```lua
   -- ascreen_source_switcher.lua

   local ascreen_sources = {
       playback_video = "轮播视频源",
       lyrics_display = "歌词/播放器显示",
       song_request_video = "点歌视频/MV源",
       broadcast_screen = "直播画面源",
       pk_background = "PK背景源",
       comments_display = "评论显示",    -- 新增
   }

   -- 然后在对应的模式中配置
   playback = {
       playback_video = true,
       lyrics_display = true,
       song_request_video = false,
       broadcast_screen = false,
       pk_background = false,
       comments_display = false,    -- 轮播时不显示评论
   },
   ```

3. **重启脚本**
   ```
   OBS → 工具 → 脚本 → ascreen_source_switcher.lua → 刷新
   ```

---

## 常见问题

### Q1: 脚本说源不存在？

**A**: 检查源名称是否完全一致

```
1. OBS 中右键源查看准确名称
2. 编辑脚本，在 mode_source_config 中
   确保名称完全一致（区分大小写）
3. 保存并重启脚本
```

### Q2: 源切换时有延迟？

**A**: 减小脚本检查间隔

```
OBS 脚本属性:
  检查间隔: 1000 → 改为 500

或改为 300 甚至 100（单位毫秒）
```

### Q3: 多个源同时显示？

**A**: 脚本配置有误

```
1. 启用调试模式: 脚本属性勾选 "调试模式"
2. 查看 OBS 日志看是哪个源没有隐藏
3. 检查 mode_source_config 中的配置
4. 确保对应模式下只有一个源为 true
```

### Q4: BScreen 面板不更新？

**A**: 检查 panel_refresh.lua 脚本

```
1. 确认脚本已启用
2. 检查"图像源名称"是否正确
3. 查看 SingllLive 是否正在运行
4. 检查 data/panel.png 文件是否在更新
```

---

## 总结

✅ **新方案特点**：

1. **AScreen/BScreen/CScreen 始终显示**
   - 不改变场景可见性
   - 不改变嵌套场景本身

2. **AScreen 内部源灵活切换**
   - 轮播模式：显示轮播视频 + 歌词
   - 直播模式：显示直播画面
   - 点歌模式：显示点歌MV + 歌词
   - PK模式：显示PK背景
   - 其他：全隐藏

3. **BScreen 动态渲染面板**
   - 自动刷新 panel.png
   - 显示对应模式的信息

4. **CScreen 虚拟人**
   - 始终显示
   - 可选择切换动作或保持不变

✅ **优势**：
- 完全无缝切换，零中断
- 支持同时显示多个源（如视频 + 歌词）
- 极高的灵活性
- 源管理集中在 AScreen

✅ **适用场景**：
- 需要同时显示多种视频源的直播
- 多种内容形式切换（歌曲、直播、评论等）
- 专业级多模式直播系统
