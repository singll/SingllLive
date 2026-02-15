--[[
  OBS Studio 模式自动切换脚本
  用途: 监听 mode.txt 文件，自动切换 OBS 场景

  工作流程:
  1. 定时读取 data/mode.txt (包含当前模式)
  2. 当模式变化时，自动切换对应的 OBS 场景
  3. 支持手动配置场景名称

  安装步骤:
  1. OBS → 工具 → 脚本 → Python 脚本 (或 Lua 脚本)
  2. 选择此文件: scripts/obs/scene_switcher.lua
  3. 在脚本属性中配置场景名称和 mode.txt 路径

  配置示例:
  - mode.txt 路径: D:\SingllLive\data\mode.txt
  - broadcast 场景: Scene_Broadcast
  - pk 场景: Scene_PK
  - song_request 场景: Scene_SongRequest
  - playback 场景: Scene_Playback
  - other 场景: Scene_Other
]]

obs = obslua

-- 默认配置
local mode_file_path = "data/mode.txt"
local current_mode = "playback"
local last_mode = "playback"
local check_interval_ms = 1000  -- 1秒检查一次

-- 场景名称映射
local scene_mapping = {
    broadcast = "Scene_Broadcast",
    pk = "Scene_PK",
    song_request = "Scene_SongRequest",
    playback = "Scene_Playback",
    other = "Scene_Other",
}

function script_description()
    return "自动切换OBS场景\n根据 mode.txt 文件的模式变化自动切换对应场景"
end

function script_properties()
    local props = obs.obs_properties_create()

    obs.obs_properties_add_path(props, "mode_file", "Mode文件路径",
        obs.OBS_PATH_FILE, "*.txt", "/")
    obs.obs_properties_add_int(props, "check_interval", "检查间隔(ms)",
        500, 10000, 100)

    obs.obs_properties_add_text(props, "scene_broadcast",
        "直播模式场景名", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "scene_pk",
        "PK模式场景名", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "scene_song_request",
        "点歌模式场景名", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "scene_playback",
        "轮播模式场景名", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "scene_other",
        "其他模式场景名", obs.OBS_TEXT_DEFAULT)

    return props
end

function script_defaults(settings)
    obs.obs_data_set_default_string(settings, "mode_file", "data/mode.txt")
    obs.obs_data_set_default_int(settings, "check_interval", 1000)
    obs.obs_data_set_default_string(settings, "scene_broadcast", "Scene_Broadcast")
    obs.obs_data_set_default_string(settings, "scene_pk", "Scene_PK")
    obs.obs_data_set_default_string(settings, "scene_song_request", "Scene_SongRequest")
    obs.obs_data_set_default_string(settings, "scene_playback", "Scene_Playback")
    obs.obs_data_set_default_string(settings, "scene_other", "Scene_Other")
end

function script_update(settings)
    mode_file_path = obs.obs_data_get_string(settings, "mode_file")
    check_interval_ms = obs.obs_data_get_int(settings, "check_interval")

    -- 更新场景名称映射
    scene_mapping.broadcast = obs.obs_data_get_string(settings, "scene_broadcast")
    scene_mapping.pk = obs.obs_data_get_string(settings, "scene_pk")
    scene_mapping.song_request = obs.obs_data_get_string(settings, "scene_song_request")
    scene_mapping.playback = obs.obs_data_get_string(settings, "scene_playback")
    scene_mapping.other = obs.obs_data_get_string(settings, "scene_other")

    -- 重新启动定时器
    obs.timer_remove(check_mode_change)
    obs.timer_add(check_mode_change, check_interval_ms)
end

function read_mode_from_file()
    -- 尝试打开并读取 mode.txt 文件
    local file = io.open(mode_file_path, "r")
    if file == nil then
        return nil
    end

    local content = file:read("*a")
    file:close()

    -- 清除空白和换行
    content = content:match("^%s*(.-)%s*$")

    return content
end

function switch_scene(scene_name)
    if scene_name == nil or scene_name == "" then
        return false
    end

    -- 获取场景源
    local scene = obs.obs_get_scene_by_name(scene_name)
    if scene == nil then
        obs.script_log(obs.LOG_WARNING,
            "场景不存在: " .. scene_name)
        return false
    end

    -- 切换场景
    obs.obs_frontend_set_current_scene(scene)
    obs.source_release(scene)

    obs.script_log(obs.LOG_INFO,
        "场景已切换: " .. scene_name)

    return true
end

function check_mode_change()
    -- 读取当前模式
    local mode = read_mode_from_file()

    if mode == nil then
        obs.script_log(obs.LOG_WARNING,
            "无法读取 mode.txt 文件: " .. mode_file_path)
        return
    end

    -- 更新当前模式
    current_mode = mode

    -- 如果模式改变，切换场景
    if current_mode ~= last_mode then
        obs.script_log(obs.LOG_INFO,
            "模式变化检测到: " .. last_mode .. " → " .. current_mode)

        -- 获取对应的场景名称
        local scene_name = scene_mapping[current_mode]

        if scene_name then
            switch_scene(scene_name)
            last_mode = current_mode
        else
            obs.script_log(obs.LOG_WARNING,
                "未找到模式对应的场景: " .. current_mode)
        end
    end
end

function script_load(settings)
    obs.timer_add(check_mode_change, check_interval_ms)
    obs.script_log(obs.LOG_INFO,
        "场景自动切换脚本已加载")
end

function script_unload()
    obs.timer_remove(check_mode_change)
    obs.script_log(obs.LOG_INFO,
        "场景自动切换脚本已卸载")
end
