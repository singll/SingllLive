--[[
  OBS 源可见性切换脚本
  用途: 根据 mode.txt 切换 AScreen/BScreen/CScreen 的可见性

  优点:
  - 无场景切换，直播不中断
  - 完全平滑，延迟 < 100ms
  - 源显示/隐藏切换

  工作流程:
  1. 监听 mode.txt 文件变化
  2. 读取当前模式
  3. 根据模式配置设置各区可见性
  4. 不触发场景切换

  安装步骤:
  OBS → 工具 → 脚本 → Lua脚本 → [+]
  选择此文件，在属性中配置
]]

obs = obslua

-- ==================== 配置段 ====================
local mode_file = "data/mode.txt"
local main_scene_name = "MScreen"
local scene_a_name = "AScreen"
local scene_b_name = "BScreen"
local scene_c_name = "CScreen"
local check_interval_ms = 1000

local current_mode = "playback"
local last_mode = "playback"

-- ==================== 模式可见性配置 ====================
-- 定义每个模式下各区的显示状态
-- true = 显示，false = 隐藏
local mode_visibility = {
    -- 直播模式：隐藏VLC，显示面板统计信息
    broadcast = {
        a = false,    -- 隐藏A区(VLC) - 直播时不需要背景歌
        b = true,     -- 显示B区(面板) - 显示直播数据
        c = false,    -- 隐藏C区(虚拟人) - 可选：改为true显示陪伴虚拟人
    },

    -- PK模式：隐藏VLC，显示面板PK信息
    pk = {
        a = false,    -- 隐藏A区(VLC)
        b = true,     -- 显示B区(面板) - 显示PK分数
        c = false,    -- 隐藏C区
        -- 高级配置：PK时显示VLC背景歌
        -- a = true,   -- 改为true播放PK背景音乐/视频
    },

    -- 点歌模式：显示VLC，显示面板队列
    song_request = {
        a = true,     -- 显示A区(VLC) - 播放当前歌曲
        b = true,     -- 显示B区(面板) - 显示队列列表
        c = false,    -- 隐藏C区
        -- 高级配置：点歌时显示虚拟人
        -- c = true,   -- 改为true虚拟人跳舞
    },

    -- 轮播模式：显示VLC，显示面板，可选显示虚拟人
    playback = {
        a = true,     -- 显示A区(VLC) - 播放歌曲
        b = true,     -- 显示B区(面板) - 显示当前歌
        c = false,    -- 隐藏C区
        -- 高级配置：轮播时显示虚拟人伴舞
        -- c = true,   -- 改为true虚拟人跳舞
    },

    -- 其他/空闲模式：隐藏所有音视频内容
    other = {
        a = false,    -- 隐藏A区
        b = true,     -- 显示B区 - 显示欢迎信息
        c = false,    -- 隐藏C区
    },
}

-- ==================== 脚本接口 ====================

function script_description()
    return "根据模式切换源可见性\n" ..
           "无缝切换，直播不中断\n" ..
           "支持自定义每个模式的显示配置"
end

function script_properties()
    local props = obs.obs_properties_create()

    -- 基础配置
    obs.obs_properties_add_path(props, "mode_file",
        "📁 Mode文件路径", obs.OBS_PATH_FILE, "*.txt", "/")

    obs.obs_properties_add_text(props, "main_scene",
        "🎬 主场景名称", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "scene_a",
        "🎵 A区场景名称(VLC)", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "scene_b",
        "📊 B区场景名称(面板)", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "scene_c",
        "👤 C区场景名称(虚拟人)", obs.OBS_TEXT_DEFAULT)

    -- 高级配置
    obs.obs_properties_add_int(props, "check_interval",
        "⏱️ 检查间隔(ms)", 500, 10000, 100)

    obs.obs_properties_add_bool(props, "debug_mode",
        "🐛 调试模式(输出详细日志)")

    return props
end

function script_defaults(settings)
    obs.obs_data_set_default_string(settings, "mode_file", "data/mode.txt")
    obs.obs_data_set_default_string(settings, "main_scene", "MScreen")
    obs.obs_data_set_default_string(settings, "scene_a", "AScreen")
    obs.obs_data_set_default_string(settings, "scene_b", "BScreen")
    obs.obs_data_set_default_string(settings, "scene_c", "CScreen")
    obs.obs_data_set_default_int(settings, "check_interval", 1000)
    obs.obs_data_set_default_bool(settings, "debug_mode", false)
end

function script_update(settings)
    mode_file = obs.obs_data_get_string(settings, "mode_file")
    main_scene_name = obs.obs_data_get_string(settings, "main_scene")
    scene_a_name = obs.obs_data_get_string(settings, "scene_a")
    scene_b_name = obs.obs_data_get_string(settings, "scene_b")
    scene_c_name = obs.obs_data_get_string(settings, "scene_c")
    check_interval_ms = obs.obs_data_get_int(settings, "check_interval")

    debug_mode = obs.obs_data_get_bool(settings, "debug_mode")

    -- 重启定时器
    obs.timer_remove(check_mode_change)
    obs.timer_add(check_mode_change, check_interval_ms)

    obs.script_log(obs.LOG_INFO, "配置已更新")
end

-- ==================== 核心函数 ====================

function read_mode_from_file()
    """读取 mode.txt 文件，返回模式字符串"""
    local file = io.open(mode_file, "r")
    if file == nil then
        return nil
    end

    local content = file:read("*a")
    file:close()

    -- 去除首尾空白和换行
    return content:match("^%s*(.-)%s*$")
end

function set_source_visible(scene_name, visible)
    """
    设置嵌套场景源的可见性

    Args:
        scene_name: 场景名称 (如 "AScreen")
        visible: true=显示, false=隐藏

    Returns:
        成功返回 true
    """
    -- 获取主场景
    local main_scene = obs.obs_get_scene_by_name(main_scene_name)
    if main_scene == nil then
        obs.script_log(obs.LOG_ERROR,
            "❌ 主场景不存在: " .. main_scene_name)
        return false
    end

    -- 在主场景中查找子场景源
    local scene_source = obs.obs_scene_find_source(main_scene, scene_name)
    if scene_source == nil then
        obs.script_log(obs.LOG_ERROR,
            "❌ 未找到场景源: " .. scene_name)
        obs.source_release(main_scene)
        return false
    end

    -- 设置可见性
    obs.obs_sceneitem_set_visible(scene_source, visible)
    obs.source_release(main_scene)

    local status = visible and "✓ 显示" or "✗ 隐藏"
    if debug_mode then
        obs.script_log(obs.LOG_INFO,
            "[" .. scene_name .. "] " .. status)
    end

    return true
end

function apply_mode_visibility(mode)
    """
    根据模式配置应用可见性设置

    Args:
        mode: 模式字符串 (如 "playback")

    Returns:
        成功返回 true
    """
    if mode_visibility[mode] == nil then
        obs.script_log(obs.LOG_WARNING,
            "⚠️ 未知模式: " .. mode)
        return false
    end

    local config = mode_visibility[mode]

    obs.script_log(obs.LOG_INFO,
        "📢 应用模式: [" .. mode .. "]")

    -- 依次设置各区的可见性
    set_source_visible(scene_a_name, config.a)
    set_source_visible(scene_b_name, config.b)
    set_source_visible(scene_c_name, config.c)

    if debug_mode then
        obs.script_log(obs.LOG_INFO,
            "   A区:" .. (config.a and "显示" or "隐藏") ..
            " | B区:" .. (config.b and "显示" or "隐藏") ..
            " | C区:" .. (config.c and "显示" or "隐藏"))
    end

    return true
end

function check_mode_change()
    """定时检查 mode.txt 是否变化，变化则更新可见性"""
    local mode = read_mode_from_file()

    if mode == nil then
        obs.script_log(obs.LOG_WARNING,
            "⚠️ 无法读取 mode.txt: " .. mode_file)
        return
    end

    current_mode = mode

    -- 检测到模式变化
    if current_mode ~= last_mode then
        obs.script_log(obs.LOG_INFO,
            "🔄 模式变化: [" .. last_mode .. "] → [" .. current_mode .. "]")

        apply_mode_visibility(current_mode)
        last_mode = current_mode
    end
end

-- ==================== 脚本生命周期 ====================

function script_load(settings)
    -- 初始化定时器
    obs.timer_add(check_mode_change, check_interval_ms)

    obs.script_log(obs.LOG_INFO,
        "✅ 可见性切换脚本已加载")
    obs.script_log(obs.LOG_INFO,
        "   监听文件: " .. mode_file)
    obs.script_log(obs.LOG_INFO,
        "   主场景: " .. main_scene_name)
    obs.script_log(obs.LOG_INFO,
        "   A区: " .. scene_a_name .. " | B区: " .. scene_b_name .. " | C区: " .. scene_c_name)
end

function script_unload()
    obs.timer_remove(check_mode_change)
    obs.script_log(obs.LOG_INFO,
        "✅ 可见性切换脚本已卸载")
end

-- 调试模式默认关闭
debug_mode = false
