# 模式切换完整流程说明

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SingllLive 直播系统架构                           │
└─────────────────────────────────────────────────────────────────────────┘

                            弹幕输入 / 自动检测
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │    danmaku.py            │
                    │  弹幕机器人、命令解析    │
                    └──────────────┬───────────┘
                                   │
                 ┌─────────────────┴──────────────────┐
                 │                                    │
         直播模式/PK/点歌              自动检测队列
                 │                          │
                 ▼                          ▼
    ┌──────────────────────┐  ┌──────────────────────┐
    │  Mode.set_mode()     │  │ auto_switch_for_x()  │
    │  (手动命令)          │  │ (自动检测)           │
    └──────────┬───────────┘  └──────────┬───────────┘
               │                         │
               └────────────┬────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │    ModeManager.set_mode()     │
            │  优先级检查 + 状态管理        │
            └───────────┬───────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │   模式变更回调执行             │
        └───────────────┬───────────────┘

        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
  ┌──────────────┐           ┌──────────────────┐
  │ panel.py     │           │ cyber_live.py    │
  │ 更新B区      │           │ VLC管理 + 其他   │
  │ 面板内容     │           │ 写入mode.txt     │
  │             │           │                  │
  │ → panel.png │           │ → mode.txt       │
  └──────────────┘           └──────────────────┘
        │                               │
        ▼                               ▼
  ┌──────────────┐           ┌──────────────────┐
  │  OBS读取     │           │ OBS脚本监听      │
  │ panel.png    │           │ mode.txt文件变化 │
  │ (自动刷新)   │           │ 检查模式是否变更 │
  └──────────────┘           └────────┬─────────┘
        │                             │
        │                      ┌──────▼──────┐
        │                      │ 场景是否变化 │
        │                      │ 是否需要切换 │
        │                      └──────┬──────┘
        │                             │ 是
        │                      ┌──────▼──────────┐
        │                      │ 切换对应场景    │
        │                      │ Scene_Broadcast │
        │                      │ Scene_PK        │
        │                      │ Scene_Playback  │
        │                      │ 等等            │
        │                      └─────────────────┘
        │
        ▼
    ┌──────────────────────────┐
    │  OBS Studio 显示         │
    │  最终的直播画面          │
    └──────────────────────────┘

```

---

## 详细流程：以"点歌模式"为例

### 场景 1：用户发送点歌命令

```
时间轴:  0s              1s                2s                3s
         │               │                 │                 │
         ▼               ▼                 ▼                 ▼
    用户发送      → danmaku.py         → 解析命令        → 添加到歌曲
    "点歌 歌名"     接收弹幕          "点歌 歌名"       队列 queue++
                  (blivedm)            (正则匹配)
```

### 场景 2：检测到队列变化

```
时间轴:  3s              4s                5s                6s
         │               │                 │                 │
         ▼               ▼                 ▼                 ▼
    _mode_auto_       队列数 > 0     → 尝试切换到    → mode_manager
    switch_loop()     (songs.queue_  Mode.SONG_    检查优先级
    定时检查          count > 0)     REQUEST       是否被阻止

    ┌─ 队列从 0→1
    │  ✓ 成功→切换到点歌模式
    │  ✗ 失败→被直播/PK阻止
```

### 场景 3：模式管理器处理切换

```
时间轴:  6s              7s                8s                9s
         │               │                 │                 │
         ▼               ▼                 ▼                 ▼
    set_mode()       检查优先级        记录变更信息      触发回调函数
    PLAYBACK         SONG_REQUEST   previous_mode =   _call_mode_
    → SONG_          优先级=2         PLAYBACK       change_
    REQUEST          不被阻止          current_mode =  callbacks()
                     ✓ 允许切换       SONG_REQUEST
```

### 场景 4：模式变更回调 (多线程并行)

```
时间轴:  9s              10s               11s               12s
         │               │                 │                 │
    ┌────┴────┬──────────┴──────────┬──────┴────────┐
    │          │                    │               │
    ▼          ▼                    ▼               ▼
 panel.py   cyber_live.py      obs_control.py   其他回调
 更新B区    VLC继续播放       (可选)连接OBS   (自定义)
 内容       写入mode.txt       切换场景
 生成
 panel.png
```

### 场景 5：OBS 脚本检测文件变化

```
时间轴:  12s             13s               14s               15s
         │               │                 │                 │
         ▼               ▼                 ▼                 ▼
    scene_switcher    读取mode.txt     比较模式是否   ✓ 模式改变
    lua脚本定时       内容            变化
    check_mode_     = "song_request"   old_mode =
    change()                           "playback"
    (每秒执行)                         new_mode =
                                       "song_request"
```

### 场景 6：自动切换 OBS 场景

```
时间轴:  15s             16s               17s               18s
         │               │                 │                 │
         ▼               ▼                 ▼                 ▼
    判断对应          切换场景          直播画面        观众看到
    场景名称       Scene_SongRequest   自动更新        点歌模式界面
    = Scene_         切换成功 ✓        显示点歌        + 点歌队列
    SongRequest      OBS GUI显示       队列信息        + 动态面板
```

---

## 模式优先级规则

```
优先级决策树:

                    当前模式?
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    直播模式      PK模式          点歌/轮播
    优先级=1     优先级=2        优先级=2,3
        │              │          │
        │              │          │
    阻止:          阻止:        不阻止:
    • PK           • 点歌        • 可被直播/PK
    • 点歌         • 轮播         阻止
    • 轮播         • 其他         • 可被彼此
    • 其他                        降级

示例:
═══════════════════════════════════════════════════════════════════

情况1: 用户发送"直播模式"
  当前: PLAYBACK
  目标: BROADCAST
  结果: ✓ 成功 (BROADCAST 优先级更高)

  原因: BROADCAST(1) > PLAYBACK(3)
       无优先级冲突，直接切换

═══════════════════════════════════════════════════════════════════

情况2: 直播中，用户发送"点歌"
  当前: BROADCAST
  目标: SONG_REQUEST
  结果: ✗ 阻止 (SONG_REQUEST 优先级低)

  原因: SONG_REQUEST(2) < BROADCAST(1)
       被更高优先级模式阻止
  状态: is_blocked = True
        面板显示"直播进行中，点歌已禁用"

═══════════════════════════════════════════════════════════════════

情况3: 点歌中，检测到新歌曲被添加到队列
  当前: SONG_REQUEST
  目标: SONG_REQUEST
  结果: = 保持不变 (同一模式，不切换)

  行为: 只更新 queue_count 状态信息
       不触发场景切换
```

---

## 状态文件的作用

### mode.txt (OBS 场景切换的信号文件)

**路径**: `data/mode.txt`

**内容示例**:
```
playback           ← 轮播模式
song_request       ← 点歌模式
broadcast          ← 直播模式
```

**工作流程**:
```
cyber_live.py              OBS 脚本
     │                        │
     │ 模式变更              │
     ├──▶ write mode.txt     │
     │    (内容: "song_      │
     │     request")         │
     │                        │
     │                   ◀───┤ 定时读取 (每秒)
     │                        │
     │                   ◀───┤ 比较旧值
     │                        │
     │                   ◀───┤ 模式不同?
     │                        │
     │                        ├──▶ 是: 切换场景
     │                        │    obs_frontend_
     │                        │    set_current_scene()
     │                        │
     │                        └──▶ 否: 保持不变
```

### panel.png (面板动态刷新)

**路径**: `data/panel.png`

**内容示例**: 根据模式动态生成，每秒更新一次

**工作流程**:
```
cyber_live.py              OBS 脚本 (panel_refresh.lua)
     │                            │
     │ 每秒生成                   │
     ├──▶ panel.py             │
     │    render_to_png()      │
     │    ▼                    │
     │    生成新 PNG           │
     │                         │
     │ 保存到 panel.png        │
     │                         │
     │                    ◀────┤ 监听文件变化
     │                         │
     │                    ◀────┤ obs_source_update()
     │                         │
     │                    ◀────┤ 刷新显示
     │                         │
     │                    ◀────┤ OBS 更新 B 区画面
```

---

## 代码调用关系

```
cyber_live.py (主程序)
    │
    ├─▶ ModeManager.set_mode()
    │   └─▶ 触发模式变更回调
    │       │
    │       ├─▶ panel.py.on_mode_changed()
    │       │   └─▶ 生成新 panel.png
    │       │
    │       ├─▶ vlc_control.py.on_mode_changed()
    │       │   └─▶ 控制 VLC 启动/暂停/停止
    │       │
    │       └─▶ obs_control.py.on_mode_changed() [可选]
    │           └─▶ 通过 WebSocket 切换 OBS 场景
    │
    ├─▶ songs.queue_count 变化
    │   └─▶ 触发 auto_switch_for_song_request()
    │       └─▶ 调用 set_mode(SONG_REQUEST)
    │
    ├─▶ 弹幕收到"直播模式"命令
    │   └─▶ 调用 set_mode(BROADCAST, reason="用户命令")
    │
    └─▶ 数据文件写入
        ├─▶ data/mode.txt (OBS 脚本读取)
        ├─▶ data/panel.png (OBS 自动刷新)
        └─▶ data/now_playing.txt (字幕条使用)
```

---

## 时间序列示例：完整的模式切换过程

```
时刻    模块            操作                          输出/状态
────────────────────────────────────────────────────────────────
 0s   用户            弹幕发送 "点歌 五月天"

 1s   danmaku.py      ├─ 接收弹幕
                      ├─ 解析: 点歌 + 歌名
                      └─ songs.add_to_queue()

 2s   songs.py        └─ queue_count: 0 → 1

 3s   cyber_live.py   └─ _mode_auto_switch_loop()
      (定时检查)        检测 queue_count > 0

 4s   ModeManager     └─ set_mode(SONG_REQUEST, "队列有1首歌")

 5s   ModeManager     └─ 优先级检查 ✓ 允许切换
      (回调执行)        previous: PLAYBACK → current: SONG_REQUEST

 6s   panel.py        └─ on_mode_changed() 回调执行
                      └─ 生成 panel.png (显示点歌队列)

 6s   vlc_control.py  └─ on_mode_changed() 回调执行
                      └─ 继续播放 VLC

 7s   cyber_live.py   └─ 写入 data/mode.txt
                      └─ 内容: "song_request"

 8s   OBS脚本         └─ check_mode_change() 执行
      scene_switcher  ├─ 读取 mode.txt
                      ├─ 比较: "playback" → "song_request"
                      ├─ ✓ 模式改变
                      └─ 切换场景: Scene_SongRequest

 9s   OBS             └─ Scene_SongRequest 激活
      scene_switcher  ├─ 显示 VLC 视频 (A区)
      panel_refresh   ├─ 显示动态面板 (B区)
                      ├─ 显示虚拟人 (C区)
                      └─ 显示框架 (顶层)

 10s  OBS显示          └─ 直播画面更新: 现在显示点歌模式
                      ├─ 队列中有 1 首 "五月天"
                      ├─ 面板动态显示
                      └─ 观众看到点歌界面
```

---

## 三种集成方案对比

| 方案 | 技术 | 优点 | 缺点 | 推荐度 |
|------|------|------|------|--------|
| **方案A** | 写入 mode.txt + Lua脚本读取 | ✓ 无需依赖<br>✓ 跨平台<br>✓ 稳定 | ✗ 延迟1-2秒<br>✗ 需要额外脚本 | ⭐⭐⭐ 最佳 |
| **方案B** | Python WebSocket + ObsWebsocket 库 | ✓ 实时切换<br>✓ 代码内集成<br>✓ 易于扩展 | ✗ 需要安装库<br>✗ 需要 OBS 开启 WebSocket<br>✗ 网络依赖 | ⭐⭐ 次选 |
| **方案C** | OBS Python脚本 | ✓ 无需文件<br>✓ 直接访问OBS | ✗ OBS Python支持有限<br>✗ 难度高 | ⭐ 不推荐 |

**推荐使用方案 A**（Lua脚本）：
- 最稳定、最轻量
- 无需额外 Python 依赖
- 延迟可接受（1秒左右）
- 适合直播场景

