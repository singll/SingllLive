# OBS 场景配置指南

> 📌 **重要提示**：本文档描述的是传统的 5 场景方案。我们现在推荐使用更优的 **Plan A（4 场景嵌套 + 单一 VLC 实例）** 方案。
>
> **为什么迁移到 Plan A？**
> - ✅ 直播无中断（无场景切换）
> - ✅ 切换延迟 < 100ms（vs 1-2秒）
> - ✅ 配置更简洁（4 个场景 vs 5 个）
> - ✅ 架构更清晰（职责分明）
>
> **立即开始 Plan A**：[PLAN_A_IMPLEMENTATION_SUMMARY.md](PLAN_A_IMPLEMENTATION_SUMMARY.md)
>
> **从这个方案迁移**：[MIGRATION_TO_NESTED_SCENES.md](MIGRATION_TO_NESTED_SCENES.md)

## 概述

本文档说明如何在 OBS Studio 中创建和配置 5 个场景，与 SingllLive 系统的模式切换相对应。

⚠️ **注意**：此方案已过时，仅供参考。请使用上述 Plan A 方案。

## 第一步：创建 5 个场景

### 场景列表

| 模式 | 场景名称 | 优先级 | 用途 | 标记颜色 |
|------|---------|--------|------|---------|
| BROADCAST | Scene_Broadcast | 1 (最高) | 直播模式 | 🔴 红色 |
| PK | Scene_PK | 2 | PK对战 | 🔴 红色 |
| SONG_REQUEST | Scene_SongRequest | 2 | 点歌 | 🟣 品红 |
| PLAYBACK | Scene_Playback | 3 | **轮播(默认)** | 🔵 青色 |
| OTHER | Scene_Other | 4 (最低) | 其他/空闲 | ⚫ 灰色 |

### 创建步骤

1. **打开 OBS Studio**

2. **在"场景"面板中创建 5 个场景**：
   - 点击 "场景" 下的 **[+]** 按钮
   - 输入场景名称：`Scene_Broadcast`
   - 重复 4 次，创建所有 5 个场景

   ```
   场景列表:
   ├── Scene_Broadcast
   ├── Scene_PK
   ├── Scene_SongRequest
   ├── Scene_Playback          ← 默认，先不编辑
   └── Scene_Other
   ```

---

## 第二步：为每个场景添加源

### 共同的源列表（所有场景相同）

每个场景需要以下 5 个源，按照**从下到上**的层级顺序添加：

| 层级 | 源名称 | 类型 | 文件路径 | 位置(x,y) | 大小(w×h) | 备注 |
|------|--------|------|---------|----------|----------|------|
| 1 | background | 图像 | assets/background.png | 0,0 | 1920×1080 | 最底层 |
| 2 | VLC-A区 | VLC源 | VLC播放列表 | 18,18 | 1344×756 | 左侧主内容 |
| 3 | Panel-B区 | 图像 | data/panel.png | 1385,45 | 522×440 | 右侧面板 |
| 4 | VTuber-C区 | 窗口捕获 | VTubeStudio | 1380,504 | 532×488 | 右侧虚拟人 |
| 5 | frame-overlay | 图像 | assets/frame-overlay.png | 0,0 | 1920×1080 | 最顶层 |

### 添加源的步骤

**以 Scene_Playback 为示例**：

#### 1. 添加背景 (background.png)

```
1. 选择 Scene_Playback 场景
2. 在源面板点击 [+] → 图像
3. 创建新的源：
   - 名称: background
   - 确认
4. 选择文件: SingllLive\assets\background.png
5. 位置: x=0, y=0
6. 大小: 宽=1920, 高=1080
7. 确认
8. 右键源 → 安排 → 发送到最底层
```

#### 2. 添加 VLC 视频源 (A区)

```
1. 在源面板点击 [+] → VLC 视频源
2. 创建新的源：
   - 名称: VLC-A区
   - 确认
3. 配置：
   - 输入: VLC 播放列表
   - 勾选"循环"和"随机"
4. 位置: x=18, y=18
5. 大小: 宽=1344, 高=756
6. 确认
```

#### 3. 添加面板图像源 (B区)

```
1. 在源面板点击 [+] → 图像
2. 创建新的源：
   - 名称: Panel-B区
   - 确认
3. 选择文件: SingllLive\data\panel.png
4. 位置: x=1385, y=45
5. 大小: 宽=522, 高=440
6. 确认
```

#### 4. 添加 C 区虚拟人（可选）

```
1. 在源面板点击 [+] → 窗口捕获
2. 创建新的源：
   - 名称: VTuber-C区
   - 确认
3. 选择窗口: VTubeStudio
4. 位置: x=1380, y=504
5. 大小: 宽=532, 高=488
6. 确认
```

或使用场景嵌套（见下方"高级配置"）

#### 5. 添加框架遮罩 (frame-overlay.png)

```
1. 在源面板点击 [+] → 图像
2. 创建新的源：
   - 名称: frame-overlay
   - 确认
3. 选择文件: SingllLive\assets\frame-overlay.png
4. 位置: x=0, y=0
5. 大小: 宽=1920, 高=1080
6. 确认
7. 右键源 → 安排 → 置于顶层
```

### 复制场景（快速方法）

如果想让所有 5 个场景都有相同的源：

1. **配置完成 Scene_Playback 后**：
   - 右键 `Scene_Playback`
   - 选择 **复制** (或 Duplicate)

2. **右键复制的场景**：
   - 重命名为 `Scene_Broadcast`

3. **重复此过程**创建其他 4 个场景

---

## 第三步：启用自动面板刷新脚本

### 安装 panel_refresh.lua 脚本

```
1. OBS → 工具 → 脚本 → Python 脚本
2. 点击 [+] 添加脚本
3. 选择: SingllLive\scripts\obs\panel_refresh.lua
4. 在脚本属性中配置：
   - 图像源名称: Panel-B区
   - 刷新间隔: 1000 (毫秒)
5. 确认
```

这样，panel.png 会每秒自动刷新，显示实时的模式信息。

---

## 第四步：启用场景自动切换脚本

### 方案 A：使用 Lua 脚本 (推荐)

```
1. OBS → 工具 → 脚本 → Lua 脚本
2. 点击 [+] 添加脚本
3. 选择: SingllLive\scripts\obs\scene_switcher.lua
4. 在脚本属性中配置：
   - Mode文件路径: D:\SingllLive\data\mode.txt
   - 直播模式场景名: Scene_Broadcast
   - PK模式场景名: Scene_PK
   - 点歌模式场景名: Scene_SongRequest
   - 轮播模式场景名: Scene_Playback
   - 其他模式场景名: Scene_Other
   - 检查间隔: 1000 (毫秒)
5. 确认
```

当 `mode.txt` 文件内容变化时，脚本会自动切换对应的场景。

### 方案 B：使用 Python WebSocket 连接 (高级)

在 Python 代码中集成 OBS 控制：

```python
# 在 cyber_live.py 中添加

from modules.obs_control import ObsController, ObsModeController

# 创建 OBS 控制器
obs = ObsController("localhost", 4455, "")  # 如果 OBS 有密码改这里

# 在启动时连接
await obs.connect()

# 向 mode_manager 注册模式变化回调
obs_mode_ctrl = ObsModeController(obs)
mode_manager.register_mode_change_callback(
    obs_mode_ctrl.on_mode_changed
)
```

这样，每当 Python 程序切换模式时，OBS 会自动切换场景。

---

## 第五步：测试配置

### 验证场景创建

```
1. 确保所有 5 个场景都已创建：
   ✓ Scene_Broadcast
   ✓ Scene_PK
   ✓ Scene_SongRequest
   ✓ Scene_Playback
   ✓ Scene_Other

2. 每个场景都应该包含：
   ✓ background.png
   ✓ VLC-A区
   ✓ Panel-B区
   ✓ VTuber-C区 (可选)
   ✓ frame-overlay.png
```

### 手动测试场景切换

```
1. 在 OBS 中手动切换场景：
   - 点击 Scene_Broadcast，确保视频正常显示
   - 点击 Scene_Playback，确保视频正常显示
   等等

2. 测试面板刷新：
   - 启动 SingllLive 程序
   - 观察 Panel-B区 是否每秒刷新
   - 检查显示的模式信息是否正确

3. 测试场景自动切换：
   - 在 OBS 中启用 scene_switcher.lua 脚本
   - 在 SingllLive 中发送弹幕命令改变模式
   - 观察 OBS 是否自动切换对应的场景
```

---

## 高级配置

### 1. 为不同模式添加视觉指示

每个场景可以在右下角添加 LED 指示灯，显示当前模式：

```
Scene_Broadcast:
  - 添加图像: assets/led-red.png (或自制红色方块)
  - 位置: (1880, 1040)
  - 大小: (30, 30)

Scene_PK:
  - 添加图像: assets/led-red.png

Scene_SongRequest:
  - 添加图像: assets/led-magenta.png

Scene_Playback:
  - 添加图像: assets/led-cyan.png

Scene_Other:
  - 添加图像: assets/led-gray.png
```

### 2. 使用嵌套场景组织 C 区

如果 C 区很复杂（多个虚拟人模型或多个摄像头），可以使用嵌套场景：

```
1. 创建嵌套场景: Nested_VirtualRoom
   - 添加 VTubeStudio 窗口捕获
   - 添加装饰图像等

2. 在每个场景中：
   - 添加场景源（而非窗口捕获）
   - 指向 Nested_VirtualRoom
   - 位置: (1380, 504)
   - 大小: (532, 488)
```

### 3. 添加场景说明文本

在每个场景右下角添加当前模式的文字说明：

```
1. 添加文本源：
   - 创建文本源
   - 文本内容: "直播模式" (对应的中文)
   - 字体: 20px, 青色 (#00ffff)
   - 位置: (20, 1050)
```

---

## 故障排查

### 问题 1：面板不刷新

```
❌ panel.png 不变化
✓ 确保 SingllLive 程序正在运行
✓ 检查 data/panel.png 文件是否存在
✓ 重启 OBS
✓ 在脚本属性中修改刷新间隔，然后改回原值
```

### 问题 2：场景切换不自动

```
❌ 发送弹幕改变模式，但 OBS 场景不变
✓ 确保 scene_switcher.lua 脚本已加载
✓ 检查 mode.txt 文件是否存在于正确的路径
✓ 查看 OBS 日志（帮助 → 日志文件）
✓ 确保 Scene_Broadcast 等场景名称准确拼写
```

### 问题 3：VLC 视频源黑屏

```
❌ VLC 源显示黑屏
✓ 确保 VLC 已安装
✓ 检查歌曲库目录是否非空
✓ 在 OBS 中右键 VLC 源 → 刷新缓存
✓ 重启 SingllLive 程序
```

---

## 配置示例文件

### config.ini 中的 OBS 配置（可选）

```ini
[obs]
# OBS WebSocket 连接配置 (仅当使用 Python 方案时)
enabled = true
host = localhost
port = 4455
password =

[scenes]
# 场景名称映射
broadcast = Scene_Broadcast
pk = Scene_PK
song_request = Scene_SongRequest
playback = Scene_Playback
other = Scene_Other
```

---

## 总结

✅ **完成以下步骤即可启用自动场景切换**：

1. ✓ 创建 5 个 OBS 场景
2. ✓ 为每个场景添加共同的源（背景、VLC、面板、虚拟人、框架）
3. ✓ 启用 panel_refresh.lua（面板自动刷新）
4. ✓ 启用 scene_switcher.lua（场景自动切换）
5. ✓ 配置正确的文件路径和场景名称
6. ✓ 测试整个流程

现在，当你通过弹幕或其他方式改变 SingllLive 的模式时，OBS 会自动切换到对应的场景！

