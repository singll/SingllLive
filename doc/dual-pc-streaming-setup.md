# 双机直播音视频互通配置方案

> 适用场景：PVE 虚拟机（Win10 GPU 直通）作为直播机 + 物理机（Win11）作为日用/游戏机
> 基于 Voicemeeter Banana v2122 + NDI + VBAN
> 最后更新：2026-03-01

## 目录

- [一、架构总览](#一架构总览)
- [二、核心概念：Voicemeeter 的 Strip 和 Bus](#二核心概念voicemeeter-的-strip-和-bus)
- [三、前置准备](#三前置准备)
- [四、Win11 端配置（日用机/发送端）](#四win11-端配置日用机发送端)
- [五、Win10 VM 端配置（直播机/接收端）](#五win10-vm-端配置直播机接收端)
- [六、NDI 视频传输配置](#六ndi-视频传输配置)
- [七、OBS 场景预设](#七obs-场景预设)
- [八、快捷键与音量控制](#八快捷键与音量控制)
- [九、验证与故障排查](#九验证与故障排查)
- [十、常见问题 FAQ](#十常见问题-faq)

---

## 一、架构总览

### 1.1 硬件拓扑

```
┌─────────── 局域网（千兆）───────────┐
│                                     │
┌───┴───────────┐              ┌──────────┴──────────┐
│  Win11 物理机   │              │  PVE - Win10 VM      │
│  （日用/游戏）  │              │  （GPU 直通/直播专用） │
│               │   VBAN ×2    │                      │
│  Voicemeeter ──┼──→ 麦克风 ──→──┤  Voicemeeter Banana  │
│  Banana       │  (Strip 1)   │    ↓                  │
│               ──┼──→ 游戏音频 →──┤  OBS（主推流）       │
│               │  (Strip 4)   │    ├─ VTS 模型         │
│               │              │    ├─ 弹幕姬           │
│  OBS (NDI发送) ─┼──→ 游戏画面 →──┤    ├─ NDI Source      │
│               │   NDI        │    └─→ 推流 B站        │
│               │              │                      │
│  CS2 / 工作    │              │  自动化脚本            │
└───────────────┘              └──────────────────────┘
```

### 1.2 数据流

```
Win11 麦克风 ──VBAN(Strip 1)──→ Win10 Strip 1 ──[B1]──┐
Win11 游戏   ──VBAN(Strip 4)──→ Win10 Strip 2 ──[B1]──┼→ BUS B1 → VoiceMeeter Out B1 → OBS
Win10 VTS/BGM ────────────────→ Win10 Strip 4 ──[B1]──┘

Win11 游戏画面 ──NDI──→ Win10 OBS NDI Source（视频，音频关闭避免重复）
```

### 1.3 需要安装的软件

| 软件 | Win10 VM | Win11 | 用途 | 费用 |
|------|:--------:|:-----:|------|------|
| Voicemeeter Banana | ✅ | ✅ | 音频路由 + VBAN | 免费（捐赠制） |
| NDI Runtime | ✅ | ✅ | NDI 协议底层支持 | 免费 |
| OBS + obs-ndi 插件 | ✅ | ✅ | 推流 / NDI 收发 | 免费 |
| Parsec（可选） | ✅ | ✅ | 远程管理 VM（不抢音频） | 免费个人版 |

> **不需要安装的**：VBAN Receptor — Voicemeeter Banana 自带 VBAN 收发功能，Receptor 是冗余的。

---

## 二、核心概念：Voicemeeter 的 Strip 和 Bus

> 如果你已经理解 Voicemeeter 的路由概念，可以跳过本节。

### 2.1 界面布局

打开 Voicemeeter Banana，界面从左到右：

```
◄──────────── 左侧：输入 Strips ────────────►  ◄── 右侧：输出 Buses ──►

┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐ ┌──────────┐  ┌──────┐ ┌──────┐
│硬件   │ │硬件   │ │硬件   │ │Voicemeeter│ │Voicemeeter│  │ BUS  │ │ BUS  │
│Input 1│ │Input 2│ │Input 3│ │  VAIO    │ │  AUX     │  │  A   │ │  B   │
│      │ │      │ │      │ │(虚拟输入) │ │(虚拟输入) │  │A1A2A3│ │B1 B2 │
│Strip 1│ │Strip 2│ │Strip 3│ │ Strip 4  │ │ Strip 5  │  │      │ │      │
│      │ │      │ │      │ │          │ │          │  │      │ │      │
│[A1]  │ │[A1]  │ │[A1]  │ │[A1]     │ │[A1]     │  │ 主音量│ │ 主音量│
│[A2]  │ │[A2]  │ │[A2]  │ │[A2]     │ │[A2]     │  │  滑块 │ │  滑块 │
│[A3]  │ │[A3]  │ │[A3]  │ │[A3]     │ │[A3]     │  │      │ │      │
│[B1]  │ │[B1]  │ │[B1]  │ │[B1]     │ │[B1]     │  │      │ │      │
│[B2]  │ │[B2]  │ │[B2]  │ │[B2]     │ │[B2]     │  │      │ │      │
│ 推子  │ │ 推子  │ │ 推子  │ │  推子   │ │  推子   │  │      │ │      │
└──────┘ └──────┘ └──────┘ └──────────┘ └──────────┘  └──────┘ └──────┘
```

### 2.2 术语对照表

| 术语 | 界面位置 | 作用 | VBAN 中的名称 |
|------|----------|------|--------------|
| **Strip 1** | 左侧第 1 列 | Hardware Input 1（物理设备输入） | Strip 1 |
| **Strip 2** | 左侧第 2 列 | Hardware Input 2 | Strip 2 |
| **Strip 3** | 左侧第 3 列 | Hardware Input 3 | Strip 3 |
| **Strip 4** | 左侧第 4 列 | Voicemeeter VAIO（虚拟输入，Windows 默认输出指向这里） | Strip 4 |
| **Strip 5** | 左侧第 5 列 | Voicemeeter AUX（虚拟输入） | Strip 5 |
| **BUS A1** | 右侧 A 区 | 物理输出设备 1（耳机/音箱） | BUS A1 |
| **BUS A2/A3** | 右侧 A 区 | 物理输出设备 2/3 | BUS A2/A3 |
| **BUS B1** | 右侧 B 区 | 虚拟输出 → 程序可录制（OBS 采集用） | BUS B1 |
| **BUS B2** | 右侧 B 区 | 虚拟输出 2 | BUS B2 |

### 2.3 路由按钮

每个 Strip 下面有 **A1 A2 A3 B1 B2** 五个按钮。按下 = 把该 Strip 的音频发送到对应 BUS：

```
Strip 1（麦克风）点亮了 [A1] 和 [B1]
→ 麦克风的声音同时送到 BUS A1（耳机）和 BUS B1（OBS 采集）
```

### 2.4 每个 Strip 上方的增益旋钮

```
      ╭───╮
      │ ○ │  ← 鼠标拖动或滚轮，范围 -60dB ~ +12dB
      ╰───╯
   ┌──────────┐
   │ Strip    │
   └──────────┘
```

这个旋钮用来调节输入信号的增益（放大/缩小），和下方的推子是两个独立控制。

### 2.5 VBAN Source 下拉框含义

| Source | 发送什么 |
|--------|---------|
| Strip 1 | Hardware Input 1 这一路的**单独**原始信号 |
| Strip 4 | Voicemeeter VAIO 虚拟输入的**单独**信号 |
| BUS A1 | 所有路由到 A1 的 Strip **混合后**的信号 |
| BUS B1 | 所有路由到 B1 的 Strip **混合后**的信号 |

> 分开发送用 Strip（接收端可分别调节），混合发送用 BUS。

### 2.6 v2122 设备名称对照

Voicemeeter Banana v2122 在 Windows 声音设置中显示的设备名称与旧版不同：

| 你看到的名称 | 旧版名称 | 对应的 Voicemeeter 概念 |
|-------------|---------|----------------------|
| VoiceMeeter Input | 同 | Strip 4 (VAIO) 的入口 |
| VoiceMeeter Aux Input | 同 | Strip 5 (AUX) 的入口 |
| **VoiceMeeter Out B1** | VoiceMeeter Output | **BUS B1 的输出**（录制设备） |
| **VoiceMeeter Out B2** | VoiceMeeter Aux Output | **BUS B2 的输出**（录制设备） |

---

## 三、前置准备

### 3.1 确认 IP 地址

两台机器各自打开 `cmd`，运行 `ipconfig`：

```
Win10 VM（直播机）IP:  __________ （后文用 VM_IP 代替）
Win11（日用机）IP:     __________ （后文用 PC_IP 代替）
```

### 3.2 确认互通

```bash
# Win11 上执行
ping VM_IP

# Win10 VM 上执行
ping PC_IP
```

都能通才能继续。如果不通，检查 PVE 的 VM 网卡是否为**桥接模式**（不能是 NAT）。

### 3.3 防火墙放行

**两台机器都要执行**，以管理员身份打开 cmd：

```bash
# VBAN 端口
netsh advfirewall firewall add rule name="VBAN-IN" dir=in action=allow protocol=UDP localport=6980
netsh advfirewall firewall add rule name="VBAN-OUT" dir=out action=allow protocol=UDP localport=6980

# NDI 端口（mDNS 发现 + 服务进程）
netsh advfirewall firewall add rule name="NDI-mDNS" dir=in action=allow protocol=UDP localport=5353
```

---

## 四、Win11 端配置（日用机/发送端）

### 4.1 Voicemeeter Banana 基础设置

#### 4.1.1 设置物理输出设备 A1（必须，否则音频引擎不工作）

界面右上角 **A1** 按钮 → 点击选择 → 选 `WDM: 你的耳机/音箱`

```
例如：WDM: Realtek HD Audio
     WDM: USB Audio Device
     WDM: 你的耳机名称
```

> A1 必须指定一个物理设备来驱动音频引擎。这也是你本地听声音的输出设备。

**A2、A3 不用设，留空。**

#### 4.1.2 设置物理麦克风输入

界面左侧第 1 列 **Hardware Input 1** 上方 → 点 `Select Input Device` → 选 `WDM: 你的麦克风`

```
例如：WDM: USB Microphone
     WDM: Realtek HD Audio (麦克风)
```

#### 4.1.3 确认采样率

右上角 **Menu → System Settings / Options**：

```
Preferred Main SampleRate:  48000 Hz
```

### 4.2 Windows 声音设置

打开 **设置 → 系统 → 声音**：

```
输出设备（播放）:  VoiceMeeter Input (VB-Audio VoiceMeeter VAIO)
                  → 系统/游戏的所有声音进入 Voicemeeter Strip 4

输入设备（录制）:  你的物理麦克风
                  → 保持物理麦克风！不要选 VoiceMeeter Out B1
                  → 这样游戏内语音（如 CS2）直接读物理麦克风，不受影响
```

> **重要**：输入设备必须选物理麦克风，不要选 Voicemeeter 的虚拟设备。否则游戏语音会出问题。

### 4.3 路由按钮

```
Strip 4（VAIO / 系统声音）:  点亮 [A1]  → 你本地能听到游戏/音乐
                             其他按钮不点

Strip 1（麦克风）:            全部不点
                             → 不点 A1 = 你不会听到自己说话（正常）
                             → VBAN 发送不依赖这些按钮
```

> **关键**：VBAN Outgoing 的 Source 选 Strip 时，是直接从 Strip 抽取信号，**和 A1/B1 按钮无关**。所以 Win11 端不需要点 B1，VBAN 照样能把声音发到 Win10。

### 4.4 VBAN 发送配置

点 Voicemeeter 右上角 **VBAN** 按钮（或 Menu → VBAN），打开 VBAN 面板。

**确保最上方的 VBAN 总开关为 ON。**

找到 **Outgoing Streams** 区域，配置两行：

#### 第 1 行：发送麦克风

| 字段 | 设置 |
|------|------|
| ON | ✅ 点亮 |
| Stream Name | `Win11Mic`（不要有空格） |
| IP Address To | `VM_IP`（Win10 VM 的 IP） |
| Port | 6980 |
| SR | 48000 |
| Ch | 2 |
| **Source** | **Strip 1**（麦克风那一路） |

#### 第 2 行：发送游戏/系统音频

| 字段 | 设置 |
|------|------|
| ON | ✅ 点亮 |
| Stream Name | `Win11Game`（不要有空格） |
| IP Address To | `VM_IP`（Win10 VM 的 IP） |
| Port | 6980 |
| SR | 48000 |
| Ch | 2 |
| **Source** | **Strip 4**（Voicemeeter VAIO，接收 Windows 系统声音） |

> **为什么选 Strip 而不选 BUS？** 选 Strip 发送的是单独这一路的原始信号，Win10 端可以分别调节麦克风和游戏音量。如果选 BUS，两路混在一起就没法单独调了。

### 4.5 麦克风声音太小的调节方法

如果对方收到的麦克风声音太小，**按顺序**从源头开始加大：

```
第 1 步：Windows 麦克风增益
  设置 → 系统 → 声音 → 输入 → 你的物理麦克风 → 音量拉到 100
  → 点「设备属性」→「其他设备属性」→ 级别 → 麦克风加强 +10 ~ +20 dB

第 2 步：Voicemeeter Strip 1 增益旋钮
  Strip 1 上方的旋钮 → 右拧到 +6 ~ +12 dB

第 3 步（Win10 端）：接收侧微调
  Win10 Voicemeeter Strip 1 旋钮 → 适当右拧（别拧太猛避免爆音）
```

> **原则**：先在源头（Win11）把信号拉大，接收端只做微调。源头信号太弱的话在接收端放大会同时放大底噪。

---

## 五、Win10 VM 端配置（直播机/接收端）

### 5.1 Voicemeeter Banana 基础设置

#### 5.1.1 设置物理输出 A1（驱动引擎用）

右上角 **A1** → 选 `WDM:` 开头的任意可用设备：

```
WDM: NVIDIA High Definition Audio    ← 显卡直通带的 HDMI 音频（推荐）
或
WDM: High Definition Audio Device    ← PVE 虚拟声卡
```

> 选哪个都行，VM 里不需要从本地听声音，只是让引擎跑起来。

#### 5.1.2 确认采样率

Menu → System Settings / Options → `Preferred Main SampleRate: 48000 Hz`

### 5.2 Windows 声音设置

```
输出设备（播放）:  VoiceMeeter Input
                  → VTS/BGM 等本地程序的声音进入 Strip 4

输入设备（录制）:  VoiceMeeter Out B1
                  → VTS 等需要"麦克风"的程序读取 BUS B1 的混合音频（用于驱动口型等）
```

> **注意**：v2122 版本中录制设备显示为 `VoiceMeeter Out B1`，不是旧版的 `VoiceMeeter Output`，它们是同一个东西。

### 5.3 VBAN 接收配置

点 **VBAN** 按钮打开面板，确保 **VBAN ON**。

找到 **Incoming Streams** 区域。

#### 第 1 行：接收 Win11 麦克风

| 字段 | 设置 |
|------|------|
| ON | ✅ 点亮 |
| Stream Name | `Win11Mic`（必须和 Win11 端**完全一致**，区分大小写） |
| IP Address From | `PC_IP`（Win11 的 IP） |
| Port | 6980 |
| SR | 48000 |
| Ch | 2 |

> **右键小技巧**：右键点击 Stream Name 字段，会弹出当前网络上已发现的 VBAN 流列表，直接选择即可自动填充，不用手动输入。

#### 第 2 行：接收 Win11 游戏音频

| 字段 | 设置 |
|------|------|
| ON | ✅ 点亮 |
| Stream Name | `Win11Game`（必须完全一致） |
| IP Address From | `PC_IP` |
| Port | 6980 |
| SR | 48000 |
| Ch | 2 |

#### VBAN 接收的音频去哪了？

每条 Incoming Stream 会**替换**指定 Strip 的输入源。接收到的音频直接出现在那个 Strip 的推子上，你可以用推子和路由按钮控制它：

- Stream 1（Win11Mic）→ 出现在 **Strip 1**（Hardware Input 1）
- Stream 2（Win11Game）→ 出现在 **Strip 2**（Hardware Input 2）

### 5.4 路由按钮设置

```
Strip 1（VBAN:Win11 麦克风）:  只点亮 [B1]  → 送给 OBS
Strip 2（VBAN:Win11 游戏）:    只点亮 [B1]  → 送给 OBS
Strip 4（VAIO:本地 VTS/BGM）:  只点亮 [B1]  → 送给 OBS

A1 按钮全部不点（VM 本地不需要出声，点了可能产生回声）
```

完整路由示意：

```
Strip 1 [VBAN: Win11 麦克风] ──[B1]──→ ┐
Strip 2 [VBAN: Win11 游戏]   ──[B1]──→ ├─→ BUS B1 ──→ VoiceMeeter Out B1 ──→ OBS 采集
Strip 4 [VAIO: 本地 VTS/BGM] ──[B1]──→ ┘
```

### 5.5 OBS 音频配置

OBS → **设置 → 音频**：

```
常规:
  采样率:          48000 Hz
  声道:            Stereo

全局音频设备:
  桌面音频:         禁用            ← 不用桌面音频，避免重复
  桌面音频 2:       禁用
  麦克风/辅助音频:   VoiceMeeter Out B1   ← 采集 BUS B1 混合音频
  麦克风/辅助音频 2: 禁用
```

> **为什么用「麦克风/辅助」而不是「桌面音频」？**
> BUS B1 的输出在 Windows 中是**录制设备**（`VoiceMeeter Out B1`），不是播放设备。
> OBS 的「桌面音频」抓的是播放设备，「麦克风/辅助」抓的是录制设备。
> 所以必须用「麦克风/辅助」来采集 BUS B1。

---

## 六、NDI 视频传输配置

### 6.1 安装 NDI Runtime（两台都要）

```
1. 浏览器打开 https://ndi.video/tools/
2. 下载「NDI Tools for Windows」（需要填邮箱获取下载链接）
3. 安装时默认全选
4. 安装完后重启电脑
```

### 6.2 安装 OBS NDI 插件（两台都要）

```
1. 浏览器打开 https://github.com/obs-ndi/obs-ndi/releases
2. 下载最新的 obs-ndi-x.x.x-windows-x64.exe
3. 关闭 OBS
4. 运行安装程序（自动识别 OBS 路径）
5. 重新打开 OBS，验证：
   - 菜单栏 Tools 下有「NDI Output settings」
   - 添加源时列表中有「NDI™ Source」
```

如果安装后找不到 NDI 相关选项，确认 NDI Runtime 已装且已重启。

### 6.3 Win11 OBS 配置（NDI 发送端）

```
1. 打开 OBS
2. 菜单 Tools → NDI Output settings
3. 勾选 ✅ Main Output
4. Output name 填 Win11OBS
5. 点 OK
6. 添加一个「游戏捕获」源（捕获你要玩的游戏）
```

> Win11 的 OBS 不需要推流，它只是一个 NDI 视频发送器，开着就会自动广播画面。

### 6.4 Win10 VM OBS 配置（NDI 接收端）

```
1. 打开 OBS
2. 新建场景 → 命名「游戏直播」
3. Sources → 点 + 号 → 选「NDI™ Source」
4. 命名为「Win11 游戏画面」
5. 属性窗口中：
   - Source Name 下拉 → 选择 你的Win11主机名 (Win11OBS)
     （需要等几秒让 NDI 发现设备）
   - Bandwidth: Highest
   - Sync: Source Timing
6. 点 OK
7. 重要：在 OBS 混音器中将 NDI 源的音频静音
   → 右键 NDI 源 → 高级音频属性 → 静音
   → 因为音频已经走 VBAN，避免重复
```

### 6.5 NDI 故障排查

如果 NDI Source 下拉列表是空的：

| 检查项 | 操作 |
|--------|------|
| Win11 OBS 是否开启了 NDI Output | Tools → NDI Output settings → Main Output ✅ |
| 两台机器是否同一网段 | 确认 IP 前三段相同（如都是 192.168.x.x） |
| NDI Runtime 是否安装 | 两台都要装 |
| 防火墙是否放行 | UDP 5353 + NDI 服务进程 |

---

## 七、OBS 场景预设

Win10 VM 的 OBS 建议建以下场景：

| 场景名 | 用途 | 内容源 |
|--------|------|--------|
| 挂机-氛围 | 无人值守日常 | 终端画面 + BGM + VTS |
| 挂机-播报 | AI 资讯播报 | 资讯画面 + TTS 音频 |
| 游戏直播 | Win11 打游戏时 | NDI Source + VTS + 弹幕姬 |
| 聊天/写代码 | Win11 桌面活动 | NDI Source + VTS + 弹幕姬 |
| BRB/离开 | 临时离开 | 静态图 + "马上回来" + BGM |

挂机场景使用 SingllLive 的自动化脚本管理，游戏场景通过 OBS 手动或热键切换。

---

## 八、快捷键与音量控制

### 8.1 系统音量键的行为

Windows 默认输出设为 `VoiceMeeter Input` 后，键盘音量键控制的是 VoiceMeeter Input 的端点音量。实际效果可能不明显，推荐使用以下方案替代。

### 8.2 方案 A：Windows 音量合成器（最简单）

**右键任务栏喇叭图标 → 打开音量合成器**

每个程序有独立滑块（Chrome、CS2、Spotify 等），这些按程序分别调节的滑块在 Voicemeeter 下**仍然生效**，因为它调的是程序送入 VoiceMeeter Input 之前的音量。

### 8.3 方案 B：内置 Hook Volume Keys

Voicemeeter 右上角 **Menu → Shortcut Key (Hook)**：

```
☑ Hook Volume Keys (For Level Output A1)   ← 勾选
  → 键盘音量+/- 键控制 BUS A1 输出音量
  → 适用于 Win11 端（A1 连接耳机，控制你听到的总音量）

☐ Hook Volume Keys (For Level Input #1)
  → 勾选后控制 Strip 1 输入增益

☐ Use Ctrl+F10/F11/F12
  → 如果键盘没有物理音量键，勾选这个：
    Ctrl+F10 = 静音切换
    Ctrl+F11 = 音量减小
    Ctrl+F12 = 音量增大
```

> **Hook 不生效的常见原因**：
> 1. Strip 4 的 A1 没点亮 → BUS A1 里没有音频，调 A1 音量没效果
> 2. 其他软件先抢占了音量键（Logitech/Razer/Corsair 驱动）
> 3. 键盘音量键发的是硬件级信号 → 用 `Ctrl+F10/F11/F12` 替代

### 8.4 方案 C：MacroButtons（完全自定义，推荐）

MacroButtons 是 Voicemeeter 自带的独立程序，可以绑定任意键盘快捷键到任意参数。

#### 启动 MacroButtons

```
Windows 开始菜单 → VB-Audio → MacroButtons

设置自动随启：Voicemeeter Menu → MacroButtons run on Voicemeeter start ☑
```

#### 配置方法

**右键点击任意按钮** → 弹出配置窗口：

```
┌────────────────────────────────────────────┐
│  Button Configuration                       │
│                                             │
│  Name:           [ Vol Up        ]          │
│  Button Type:    ● Push Button              │
│  Keyboard Shortcut: [按下你想绑定的键]        │
│  ☑ Exclusive Key                            │
│                                             │
│  Request for Button ON / Trigger IN:        │
│  ┌─────────────────────────────────────┐   │
│  │ Bus[0].Gain += 3;                   │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  Request for Button OFF / Trigger OUT:      │
│  ┌─────────────────────────────────────┐   │
│  │                                     │   │  ← 留空
│  └─────────────────────────────────────┘   │
└────────────────────────────────────────────┘
```

#### 推荐快捷键配置

| 按钮 | 名称 | 类型 | 快捷键 | Button ON 命令 | Button OFF 命令 |
|------|------|------|--------|---------------|----------------|
| 1 | Vol Up | Push Button | 音量+ 或 `Ctrl+↑` | `Bus[0].Gain += 3;` | 留空 |
| 2 | Vol Down | Push Button | 音量- 或 `Ctrl+↓` | `Bus[0].Gain -= 3;` | 留空 |
| 3 | Mute | Push Button | 静音键 或 `Ctrl+F10` | `Bus[0].Mute = 1;` | 留空 |
| 4 | Mic Mute | 2 Positions | `Ctrl+M` | `Strip[0].Mute = 1;` | `Strip[0].Mute = 0;` |

#### 命令语法参考

```
索引对照：
  Bus[0]   = BUS A1（耳机输出）
  Bus[3]   = BUS B1（OBS 采集）
  Strip[0] = Strip 1（第 1 个输入）
  Strip[3] = Strip 4（VAIO / 系统声音）

常用命令：
  .Gain += 3      增大 3dB
  .Gain -= 3      减小 3dB
  .Gain = 0.0     设为 0dB
  .Mute = 1       静音
  .Mute = 0       取消静音

注意：
  - 方括号 Bus[0] 或圆括号 Bus(0) 都可以
  - 命令末尾要有分号 ;
  - 多条命令用分号分隔：Strip[0].Mute = 0; Strip[3].Gain = -10.0;
```

---

## 九、验证与故障排查

### 9.1 分步验证清单

配置完成后，按顺序验证：

```
测试 1: VBAN 麦克风
  ✅ Win11 对着麦克风说话
  ✅ Win10 Voicemeeter 的 Strip 1 电平表有绿色跳动
  ✅ Win10 OBS 混音器的「麦克风/辅助」有电平跳动

测试 2: VBAN 游戏音频
  ✅ Win11 播放任意音乐/视频
  ✅ Win10 Voicemeeter 的 Strip 2 电平表有跳动
  ✅ Win10 OBS 混音器有反应

测试 3: 本地音频
  ✅ Win10 VM 播放 BGM / VTS 声音
  ✅ Win10 Voicemeeter 的 Strip 4 电平表有跳动
  ✅ Win10 OBS 混音器有反应

测试 4: NDI 视频
  ✅ Win11 OBS 正在运行且有画面
  ✅ Win10 OBS 的 NDI Source 能看到 Win11 的画面
  ✅ NDI Source 的音频已静音（避免重复）

测试 5: 完整推流测试
  ✅ OBS 开始推流
  ✅ B站直播间能看到画面 + 听到声音
  ✅ 无回声、无重复音频

测试 6: Win11 游戏语音（如 CS2）
  ✅ 游戏内能正常语音通话
  ✅ 队友能听到你说话
  ✅ 你能听到队友说话
```

### 9.2 常见问题速查

| 症状 | 原因 | 解决 |
|------|------|------|
| VBAN 连上但没声音 | Strip 的路由按钮没点亮 | 回主界面点亮对应 Strip 的 [B1]（Win10）或 [A1]（Win11） |
| Voicemeeter 电平表完全不动 | A1 没有分配物理设备 | 右上角 A1 选一个 WDM 设备 |
| VBAN 收不到流 | Stream Name 不匹配 | 两端名称必须完全一致（区分大小写，不要有空格） |
| VBAN 收不到流 | 防火墙阻挡 | 执行防火墙放行命令，或临时关闭防火墙测试 |
| NDI 列表是空的 | mDNS 被阻挡 | 放行 UDP 5353 端口 |
| NDI 列表是空的 | 不在同一网段 | 确认两台 IP 前三段相同 |
| 音频有回声/重复 | NDI Source 的音频没关 | OBS 混音器中将 NDI 源静音 |
| 音频有明显延迟 | VBAN Quality 设置不当 | VBAN 面板中 Quality 选 Optimal 或 Fast |
| Win11 本地听不到声音 | Strip 4 的 A1 没点亮 | Win11 Voicemeeter Strip 4 点亮 [A1] |
| Win11 音量键调节无效 | Hook 未生效或 A1 无音频 | 确认 Strip 4 [A1] 已亮，或改用 MacroButtons |
| 游戏语音没声音 | Win11 输入设备选错了 | Win11 输入设备选物理麦克风，不选 VoiceMeeter |
| 游戏语音传了全部声音 | Win11 输入设备选了 VoiceMeeter | 改回物理麦克风 |

---

## 十、常见问题 FAQ

### Q: VB-Cable 装了需要卸载吗？

**不用**。VB-Cable 和 Voicemeeter 是同一家公司（VB-Audio）的产品，完全兼容。留着它相当于额外多一条虚拟音频线路，后面多路音频路由时可能用得上。不运行时不占资源。

### Q: VBAN Receptor 需要装吗？

**不需要**。Voicemeeter Banana 自带 VBAN 收发功能。VBAN Receptor 只能收/发整个设备的音频，无法选择 Strip/BUS 精确发送，功能远不如 Voicemeeter 内置的 VBAN。如果已安装可以卸载。

### Q: 选 WDM 还是 MME 还是 KS？

| 前缀 | 含义 | 延迟 | 建议 |
|------|------|------|------|
| MME | 最老的 Windows 音频接口 | 高 ~50ms | 不选 |
| **WDM** | Windows 驱动模型 | 中 ~20ms | **推荐，稳定通用** |
| KS | 内核流 | 最低 ~5ms | 独占设备，易冲突，不推荐 |
| ASIO | 专业音频 | 极低 | 需专业声卡，一般用不到 |

### Q: 打游戏时 Voicemeeter 会不会影响游戏内语音？

**不会**，前提是 Win11 的 Windows 输入设备选的是**物理麦克风**。游戏直接读物理麦克风，跟 Voicemeeter 无关。如果游戏内仍有问题，在游戏设置里手动指定麦克风设备（不选「默认」）。

### Q: 远程管理 Win10 VM 用什么？

**不要用 RDP**，RDP 会抢占虚拟音频设备导致直播音频中断。推荐：

| 工具 | 特点 |
|------|------|
| **Parsec** | 不抢音频，延迟低，免费个人版，推荐日常管理 |
| Sunshine + Moonlight | 基于 NVIDIA GameStream，开源免费，适合有直通显卡的 VM |
| VNC (TightVNC) | 不影响音频，但画质帧率低，仅适合简单操作 |

### Q: VBAN 的带宽占用？

```
单路 48kHz/16bit/2ch ≈ 1.5 Mbps
双路同时传输 ≈ 3 Mbps
千兆局域网完全无压力
```

### Q: NDI 的延迟和带宽？

```
视频延迟（LAN）: 1-3 帧（16-50ms），几乎无感
带宽: 1080p 约 100-150 Mbps（千兆网够用）
加上 VBAN 音频: 总计约 150 Mbps
```
