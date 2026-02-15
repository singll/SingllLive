# 快速配置指南：模式切换 + OBS 场景自动化

> ⚡ **5分钟快速上手版本**
>
> 📌 **重要提示**：本文档描述的是传统的 5 场景方案。我们现在推荐使用更优的 **Plan A（4 场景嵌套 + 单一 VLC 实例）** 方案。
>
> **立即开始 Plan A**：[PLAN_A_IMPLEMENTATION_SUMMARY.md](PLAN_A_IMPLEMENTATION_SUMMARY.md) - 提供完整的 Plan A 实现指南
>
> **或者迁移到 Plan A**：[MIGRATION_TO_NESTED_SCENES.md](MIGRATION_TO_NESTED_SCENES.md) - 从 5 场景迁移到 4 场景的步骤

---

## 核心概念

### 工作原理（简化版）

```
弹幕输入 / 自动检测
    │
    ▼
修改当前模式 (Python代码)
    │
    ▼
写入 mode.txt (信号文件)
    │
    ▼
OBS脚本监听 (Lua脚本)
    │
    ▼
自动切换 OBS 场景 ✓
```

---

## 第一阶段：配置模式系统（已完成）

✅ **SingllLive 代码已支持模式切换**

你拥有的：
- `ModeManager` 类（优先级控制）
- `Mode` 枚举（5种模式）
- 自动模式检测（队列/直播/PK）
- 弹幕命令支持（直播模式/PK模式/etc）

验证：
```bash
python cyber_live.py
# 启动时输出:
# [14:24:08] vlc 启动 VLC (进入轮播模式)
# [14:24:15] panel 面板渲染器启动
# ✓ 模式系统已运行
```

---

## 第二阶段：配置 OBS 场景

### 快速配置（复制粘贴版本）

#### Step 1: 创建 5 个场景
```
OBS → 场景 面板 → 点击 [+]

依次创建:
☐ Scene_Broadcast
☐ Scene_PK
☐ Scene_SongRequest
☐ Scene_Playback      ← 先配置这个
☐ Scene_Other
```

#### Step 2: 配置 Scene_Playback

**添加源** (顺序很重要！):

1️⃣ **背景** (最底层)
   - 类型: 图像
   - 文件: `SingllLive\assets\background.png`
   - 位置: (0, 0)
   - 大小: 1920×1080

2️⃣ **VLC 视频**
   - 类型: VLC 视频源
   - 配置: ☑循环 ☑随机
   - 位置: (18, 18)
   - 大小: 1344×756

3️⃣ **B区面板**
   - 类型: 图像
   - 文件: `SingllLive\data\panel.png`
   - 位置: (1385, 45)
   - 大小: 522×440

4️⃣ **C区虚拟人** (可选)
   - 类型: 窗口捕获
   - 窗口: VTubeStudio
   - 位置: (1380, 504)
   - 大小: 532×488

5️⃣ **框架** (最顶层)
   - 类型: 图像
   - 文件: `SingllLive\assets\frame-overlay.png`
   - 位置: (0, 0)
   - 大小: 1920×1080
   - 右键 → 安排 → 置于顶层

#### Step 3: 复制到其他 4 个场景

```
右键 Scene_Playback → 复制
右键 副本 → 重命名为 Scene_Broadcast
重复 3 次...

最终:
✓ Scene_Broadcast (新建，已复制)
✓ Scene_PK (新建，已复制)
✓ Scene_SongRequest (新建，已复制)
✓ Scene_Playback (原始)
✓ Scene_Other (新建，已复制)
```

**验证**:
```
点击每个场景，确保:
✓ 背景显示正常
✓ VLC视频显示
✓ 面板图像存在 (可能是黑色，稍后会更新)
✓ 框架可见
```

---

## 第三阶段：启用自动化脚本

### 方案 A：Lua脚本（推荐）

#### 启用面板自动刷新

```
OBS → 工具 → 脚本 → Lua脚本 → [+]

选择: SingllLive\scripts\obs\panel_refresh.lua

在脚本属性中配置:
  图像源名称: Panel-B区
  刷新间隔: 1000

✓ 点击应用
```

**验证**:
```
启动 SingllLive:
  python cyber_live.py

观察 OBS 中 B区面板:
  - 显示 "系统状态面板加载中..."
  - 1-2秒后显示实时信息
  - ✓ 每秒自动更新
```

#### 启用场景自动切换

```
OBS → 工具 → 脚本 → Lua脚本 → [+]

选择: SingllLive\scripts\obs\scene_switcher.lua

在脚本属性中配置:
  Mode文件路径: D:\SingllLive\data\mode.txt
  检查间隔: 1000

  直播模式场景名: Scene_Broadcast
  PK模式场景名: Scene_PK
  点歌模式场景名: Scene_SongRequest
  轮播模式场景名: Scene_Playback
  其他模式场景名: Scene_Other

✓ 点击应用
```

**验证**:
```
启动 SingllLive，然后在直播间发送弹幕:
  "直播模式" → OBS 自动切换到 Scene_Broadcast
  "点歌模式" → OBS 自动切换到 Scene_SongRequest
  "轮播模式" → OBS 自动切换到 Scene_Playback

✓ 自动切换成功
```

---

### 方案 B：Python WebSocket（高级）

如果想在 Python 代码中直接控制 OBS：

#### 安装库
```bash
pip install obs-websocket-py
```

#### 在 cyber_live.py 中集成

在 `cyber_live.py` 中找到 `async def main(config, args):` 函数，添加：

```python
# 在导入部分
from modules.obs_control import ObsController, ObsModeController

# 在 main 函数中，初始化部分
obs = ObsController("localhost", 4455, "")  # password 如果 OBS 设置了就填入
await obs.connect()  # 连接 OBS

# 创建 OBS 模式控制器
obs_mode_ctrl = ObsModeController(obs)

# 注册模式变化回调
mode_manager.register_mode_change_callback(
    obs_mode_ctrl.on_mode_changed
)

# 验证场景
await obs.validate_scenes()
```

#### OBS 设置

```
OBS → 工具 → WebSocket 服务器设置

启用: ✓ 启用 WebSocket 服务器
地址: localhost
端口: 4455
密码: (可选，建议留空本地使用)

✓ 确认
```

---

## 完整流程测试

### 测试清单

```
□ SingllLive 已启动
  python cyber_live.py

□ data/mode.txt 文件已生成
  查看: D:\SingllLive\data\mode.txt
  内容应该包含: "playback" 或其他模式

□ data/panel.png 文件已生成
  查看: D:\SingllLive\data\panel.png
  内容: PNG 图像 (520×435)

□ OBS 中 5 个场景已创建并配置完毕
  □ Scene_Broadcast
  □ Scene_PK
  □ Scene_SongRequest
  □ Scene_Playback
  □ Scene_Other

□ OBS 脚本已启用
  □ panel_refresh.lua
  □ scene_switcher.lua

□ 测试自动切换
  发送弹幕: "轮播模式"
    → data/mode.txt 内容变更: "playback"
    → OBS Scene_Playback 被激活 ✓

  发送弹幕: "直播模式"
    → data/mode.txt 内容变更: "broadcast"
    → OBS Scene_Broadcast 被激活 ✓

  发送弹幕: "点歌 歌名"
    → data/mode.txt 内容变更: "song_request"
    → OBS Scene_SongRequest 被激活 ✓
    → panel.png 显示点歌队列 ✓
```

---

## 模式命令参考

### 用户可以发送的弹幕命令

```
直播模式    → 切换到直播模式 (优先级1，VLC暂停)
PK模式      → 切换到PK模式 (优先级2，VLC暂停)
点歌模式    → 切换到点歌模式 (优先级2，VLC播放)
轮播模式    → 切换到轮播模式 (优先级3，VLC播放)
其他模式    → 切换到其他模式 (优先级4，VLC停止)

点歌 歌名   → 添加歌曲到队列 (自动切换到点歌模式)
切歌        → 跳过当前歌曲
当前        → 查看当前播放的歌
歌单        → 显示歌曲库列表
帮助        → 显示帮助信息
```

---

## 故障排查速查表

| 问题 | 症状 | 解决方案 |
|------|------|---------|
| **面板不刷新** | panel.png 一直是初始画面 | 1. 确保 SingllLive 正在运行<br>2. 检查脚本 panel_refresh.lua 已启用<br>3. 在脚本属性中修改间隔后重新设置 |
| **场景不切换** | 发送弹幕改变模式，但 OBS 场景不变 | 1. 确保脚本 scene_switcher.lua 已启用<br>2. 检查 mode.txt 路径正确<br>3. 确保场景名称拼写准确<br>4. 查看 OBS 日志（帮助 → 日志文件） |
| **VLC 黑屏** | A区显示黑色，无视频 | 1. 检查歌曲库不为空<br>2. 重启 SingllLive<br>3. 在 OBS 中右键 VLC → 刷新缓存 |
| **mode.txt 不存在** | scene_switcher 无法读取文件 | 1. 确保 SingllLive 已启动<br>2. 检查配置文件 config.ini 中的 data_dir 路径<br>3. 手动创建 data 目录 |
| **OBS 连接超时** (WebSocket方案) | Python 无法连接 OBS | 1. 检查 OBS 工具 → WebSocket 服务器已启用<br>2. 确保端口 4455 未被占用<br>3. 查看 OBS 日志 |

---

## 进阶配置

### 为不同模式添加视觉指示

在每个场景中添加 LED 灯条，指示当前模式：

```
场景中添加 → 新建颜色源

Scene_Broadcast:
  颜色: #FF0000 (红)
  位置: (1900, 1050)
  大小: (15, 15)

Scene_PK:
  颜色: #FF0000 (红)

Scene_SongRequest:
  颜色: #FF00FF (品红)

Scene_Playback:
  颜色: #00FFFF (青)

Scene_Other:
  颜色: #808080 (灰)
```

### 添加模式文字说明

```
添加文本源到每个场景:

Scene_Broadcast:
  文本: "📡 直播模式 BROADCAST"
  字体: 16px, #FF5555
  位置: (20, 1050)

(以此类推...)
```

---

## 总结：你现在拥有什么

✅ **已完成**:
- 模式管理系统（优先级控制）
- 弹幕命令解析
- VLC 自动控制
- B区动态面板

✅ **新增能力**:
- OBS 自动场景切换
- 实时面板刷新
- 模式同步显示
- 完整的直播工作流

✅ **可以做到**:
1. 发送弹幕改变直播模式
2. OBS 自动切换对应场景
3. VLC 根据模式自动播放/暂停
4. 面板实时显示当前模式和信息
5. 完全自动化的多模式直播

---

## 下一步

1. **立即开始**:
   ```bash
   python cyber_live.py
   ```

2. **配置 OBS**:
   - 按照上面的步骤创建 5 个场景
   - 启用 panel_refresh.lua 脚本
   - 启用 scene_switcher.lua 脚本

3. **测试**:
   - 发送弹幕测试模式切换
   - 观察 OBS 场景自动变化
   - 检查面板信息更新

4. **优化** (可选):
   - 添加 LED 指示灯
   - 添加模式文字说明
   - 自定义 C区 场景

---

## 获取帮助

📖 **详细文档**:
- `OBS_SCENE_SETUP.md` - 完整的 OBS 配置指南
- `MODE_SWITCHING_FLOW.md` - 模式切换工作原理
- `singll-live-guide.md` - 系统整体说明

🔗 **相关文件**:
- 模式定义: `modules/modes.py`
- 自动切换逻辑: `cyber_live.py`
- OBS 控制: `modules/obs_control.py`
- Lua 脚本: `scripts/obs/scene_switcher.lua`

💬 **常见问题**:
- 查看本文档的"故障排查速查表"
- 检查 OBS 日志: 帮助 → 日志文件
- 查看 SingllLive 日志: data/cyber_live.log

