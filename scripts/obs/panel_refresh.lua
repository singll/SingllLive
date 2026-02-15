--[[
  OBS Studio 图像源自动刷新脚本
  用途: 让 OBS Image Source 每隔几秒重新加载 panel.png
  安装: OBS -> 工具 -> 脚本 -> 添加此文件
  配置: 在脚本属性中填入图像源名称 (默认 "B区-终端面板")
]]

obs = obslua

local source_name = "B区-终端面板"
local interval_ms = 3000

function script_description()
    return "自动刷新B区终端面板图像源\n每隔数秒重新加载 panel.png 文件"
end

function script_properties()
    local props = obs.obs_properties_create()
    obs.obs_properties_add_text(props, "source_name", "图像源名称", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_int(props, "interval", "刷新间隔(ms)", 1000, 10000, 500)
    return props
end

function script_defaults(settings)
    obs.obs_data_set_default_string(settings, "source_name", "B区-终端面板")
    obs.obs_data_set_default_int(settings, "interval", 3000)
end

function script_update(settings)
    source_name = obs.obs_data_get_string(settings, "source_name")
    interval_ms = obs.obs_data_get_int(settings, "interval")

    obs.timer_remove(refresh_source)
    obs.timer_add(refresh_source, interval_ms)
end

function refresh_source()
    local source = obs.obs_get_source_by_name(source_name)
    if source ~= nil then
        local settings = obs.obs_source_get_settings(source)
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)
    end
end

function script_load(settings)
    obs.timer_add(refresh_source, interval_ms)
end
