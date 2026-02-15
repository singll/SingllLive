--[[
  OBS A区源切换脚本 (简化版)
  用途: 根据模式切换 AScreen 内部的多个源的可见性

  工作流程:
  1. 监听 mode.txt 文件变化
  2. 根据模式配置切换 AScreen 内部源的可见性
  3. 轮播/直播模式自动切换源

  源配置:
  - vlc_player: 轮播模式显示
  - broadcast_screen: 直播模式显示

  安装: OBS → 工具 → 脚本 → Lua脚本 → [+]
        选择此文件并配置
]]

obs = obslua

-- ==================== 配置段 ====================
local mode_file = "data/mode.txt"
local ascreen_name = "AScreen"
local check_interval_ms = 1000

local current_mode = "playback"
local last_mode = "playback"
local debug_mode = false

-- ==================== A区源配置（单一VLC源 + 直播画面） ====================
-- 定义每个模式下 AScreen 中各个源的显示状态
-- key: 源名称
-- value: 对应模式下是否显示
--
-- 注：vlc_player 是唯一的VLC实例，通过后端自动切换播放内容
-- 轮播模式 → 播放本地视频/音乐库
-- 直播模式 → VLC暂停，显示直播画面
local ascreen_sources = {
    vlc_player = "VLC播放器（唯一实例）",
    broadcast_screen = "直播画面源",
}

-- 模式配置: 每个模式下哪个源显示，其他源隐藏
local mode_source_config = {
    -- 轮播模式：显示VLC
    -- VLC自动播放本地视频/音乐（循环、随机）
    playback = {
        vlc_player = true,
        broadcast_screen = false,
    },

    -- 直播模式：隐藏VLC，显示直播画面
    -- VLC会暂停（由后端控制）
    broadcast = {
        vlc_player = false,
        broadcast_screen = true,
    },

    -- 其他/空闲模式：全部隐藏
    other = {
        vlc_player = false,
        broadcast_screen = false,
    },
}

-- ==================== 脚本接口 ====================

function script_description()
    return "A区源切换脚本\n" ..
           "根据模式切换 AScreen 内部源的可见性\n" ..
           "每个模式下只显示对应的源"
end

function script_properties()
    local props = obs.obs_properties_create()

    obs.obs_properties_add_path(props, "mode_file",
        "📁 Mode文件路径", obs.OBS_PATH_FILE, "*.txt", "/")
    obs.obs_properties_add_text(props, "ascreen_name",
        "🎬 AScreen场景名称", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_int(props, "check_interval",
        "⏱️ 检查间隔(ms)", 500, 10000, 100)
    obs.obs_properties_add_bool(props, "debug_mode",
        "🐛 调试模式")

    return props
end

function script_defaults(settings)
    obs.obs_data_set_default_string(settings, "mode_file", "data/mode.txt")
    obs.obs_data_set_default_string(settings, "ascreen_name", "AScreen")
    obs.obs_data_set_default_int(settings, "check_interval", 1000)
    obs.obs_data_set_default_bool(settings, "debug_mode", false)
end

function script_update(settings)
    mode_file = obs.obs_data_get_string(settings, "mode_file")
    ascreen_name = obs.obs_data_get_string(settings, "ascreen_name")
    check_interval_ms = obs.obs_data_get_int(settings, "check_interval")
    debug_mode = obs.obs_data_get_bool(settings, "debug_mode")

    obs.timer_remove(check_mode_change)
    obs.timer_add(check_mode_change, check_interval_ms)

    obs.script_log(obs.LOG_INFO, "✅ 配置已更新")
end

-- ==================== 核心函数 ====================

function read_mode_from_file()
    """读取 mode.txt 并返回模式字符串"""
    local file = io.open(mode_file, "r")
    if file == nil then
        return nil
    end
    local content = file:read("*a")
    file:close()
    return content:match("^%s*(.-)%s*$")
end

function get_ascreen()
    """获取 AScreen 场景对象"""
    local scene = obs.obs_get_scene_by_name(ascreen_name)
    if scene == nil then
        obs.script_log(obs.LOG_ERROR,
            "❌ AScreen 场景不存在: " .. ascreen_name)
        return nil
    end
    return scene
end

function set_source_visible(ascreen, source_name, visible)
    """
    设置 AScreen 内部源的可见性

    Args:
        ascreen: AScreen 场景对象
        source_name: 源名称
        visible: true=显示, false=隐藏

    Returns:
        成功返回 true
    """
    if ascreen == nil then
        return false
    end

    -- 在 AScreen 中查找该源
    local scene_item = obs.obs_scene_find_source(ascreen, source_name)
    if scene_item == nil then
        if debug_mode then
            obs.script_log(obs.LOG_WARNING,
                "⚠️ 未找到源: " .. source_name)
        end
        return false
    end

    -- 设置可见性
    obs.obs_sceneitem_set_visible(scene_item, visible)

    local status = visible and "✓ 显示" or "✗ 隐藏"
    if debug_mode then
        obs.script_log(obs.LOG_INFO,
            "   [" .. source_name .. "] " .. status)
    end

    return true
end

function apply_mode_config(mode)
    """
    根据模式配置应用源可见性

    Args:
        mode: 模式字符串

    Returns:
        成功返回 true
    """
    if mode_source_config[mode] == nil then
        obs.script_log(obs.LOG_WARNING,
            "⚠️ 未知模式: " .. mode)
        return false
    end

    local ascreen = get_ascreen()
    if ascreen == nil then
        return false
    end

    local config = mode_source_config[mode]

    obs.script_log(obs.LOG_INFO,
        "📢 应用模式: [" .. mode .. "]")

    -- 遍历所有源，根据配置设置可见性
    for source_name, desc in pairs(ascreen_sources) do
        local should_visible = config[source_name] or false
        set_source_visible(ascreen, source_name, should_visible)
    end

    obs.source_release(ascreen)

    if debug_mode then
        obs.script_log(obs.LOG_INFO,
            "✅ 模式配置已应用")
    end

    return true
end

function check_mode_change()
    """定时检查 mode.txt 是否变化，变化则更新源可见性"""
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

        apply_mode_config(current_mode)
        last_mode = current_mode
    end
end

-- ==================== 脚本生命周期 ====================

function script_load(settings)
    obs.timer_add(check_mode_change, check_interval_ms)

    obs.script_log(obs.LOG_INFO,
        "✅ A区源切换脚本已加载")
    obs.script_log(obs.LOG_INFO,
        "   监听文件: " .. mode_file)
    obs.script_log(obs.LOG_INFO,
        "   AScreen: " .. ascreen_name)
    obs.script_log(obs.LOG_INFO,
        "   管理源: vlc_player / broadcast_screen")

    if debug_mode then
        obs.script_log(obs.LOG_INFO, "🐛 调试模式已启用")
    end
end

function script_unload()
    obs.timer_remove(check_mode_change)
    obs.script_log(obs.LOG_INFO,
        "✅ A区源切换脚本已卸载")
end
