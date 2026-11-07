"""插件离线测试：配置注入、命令注册表、帮助命令与纯函数。

不启动 MaiBot 宿主：真实 SDK + 假 rpc_call，跑法见 conftest.py。
"""

import asyncio
import re
from datetime import datetime, time, timedelta

import pytest
from maibot_sdk.components import _COMPONENT_INFO_ATTR
from maibot_sdk.context import PluginContext

from schedule_utils import choose_sleep_until, format_datetime, is_inside_sleep_window, parse_clock

EXPECTED_COMMAND_TEXTS = {
    "/sleep help",
    "/sleep status",
    "/sleep wake",
    "/sleep wake_all",
    "/sleep now",
    "/sleep forced",
    "/sleep forced_all",
}


def make_plugin(plugin_module, **control_overrides):
    """创建带默认配置和假 RPC 上下文的插件实例，返回 (plugin, rpc_calls)。"""

    plugin = plugin_module.create_plugin()
    plugin.set_plugin_config({"plugin": {"config_version": "3.0.0"}})
    if control_overrides:
        plugin.set_plugin_config(
            {
                "plugin": {"config_version": "3.0.0"},
                "control": {"force_sleep_commands_enabled": control_overrides.get("force_sleep_commands_enabled", True)},
            }
        )
    rpc_calls: list[dict] = []

    async def fake_rpc(method, plugin_id, payload):
        rpc_calls.append(payload)
        return {"success": True}

    plugin._set_context(PluginContext("valleywinds.sleep-manager", rpc_call=fake_rpc))
    return plugin, rpc_calls


def iter_command_infos(plugin_module):
    """遍历命令 mixin 上声明过的 Command 组件元数据。"""

    mixin = plugin_module.SleepCommandHandlersMixin
    for attr_name in dir(mixin):
        func = getattr(mixin, attr_name)
        info = getattr(func, _COMPONENT_INFO_ATTR, None)
        if info is not None and getattr(info, "command_pattern", ""):
            yield info


def test_default_config(plugin_module):
    """默认配置注入后各节可访问且默认值正确。"""

    plugin = plugin_module.create_plugin()
    plugin.set_plugin_config({"plugin": {"config_version": "3.0.0"}})
    assert plugin.config.plugin.config_version == "3.0.0"
    assert plugin.config.schedule.sleep_window_start == "22:30"
    assert plugin.config.control.admin_user_ids == []
    assert plugin.config.logging.file_log_enabled is True
    assert plugin.config.logging.file_log_level == "INFO"


def test_command_registry_uses_new_names(plugin_module):
    """7 条命令全部注册，pattern 覆盖新命令名且不含旧下划线写法。"""

    infos = list(iter_command_infos(plugin_module))
    assert len(infos) == 7
    patterns = {info.command_pattern for info in infos}
    for text in EXPECTED_COMMAND_TEXTS:
        assert any(re.fullmatch(pattern, text) for pattern in patterns), text
    for legacy in ("/sleep_status", "/sleep_wake", "/sleep_wake_all", "/sleep_now", "/sleep_force", "/sleep_force_all"):
        assert not any(re.fullmatch(pattern, legacy) for pattern in patterns), legacy


def test_control_command_names(plugin_module):
    """睡眠期穿透白名单包含控制命令；管理命令随开关增减。"""

    plugin, _ = make_plugin(plugin_module)
    names = plugin._control_command_names()
    assert {"/sleep help", "/sleep status", "/sleep wake", "/sleep wake_all"} <= names
    assert "/sleep forced" in names and "/sleep forced_all" in names

    plugin_off, _ = make_plugin(plugin_module, force_sleep_commands_enabled=False)
    names_off = plugin_off._control_command_names()
    assert not any("forced" in name for name in names_off)


def test_help_command_lists_all_commands(plugin_module):
    """/sleep help 走 send.text 发送全部命令说明，返回拦截三元组。"""

    plugin, rpc_calls = make_plugin(plugin_module)
    success, message, level = asyncio.run(plugin.handle_help_command(stream_id="s1"))
    assert success is True and level is True
    for text in EXPECTED_COMMAND_TEXTS:
        assert text in message
    assert "管理命令" in message
    assert len(rpc_calls) == 1
    assert rpc_calls[0]["capability"] == "send.text"
    assert rpc_calls[0]["args"]["text"] == message


def test_help_command_hides_admin_when_disabled(plugin_module):
    """管理命令开关关闭时，帮助里不再列出 forced 系列。"""

    plugin, _ = make_plugin(plugin_module, force_sleep_commands_enabled=False)
    _, message, _ = asyncio.run(plugin.handle_help_command(stream_id="s1"))
    assert "/sleep now" not in message
    assert "/sleep forced" not in message
    assert "管理入睡命令已在配置中关闭" in message


def test_parse_clock():
    """HH:MM 解析：合法值生效，非法值回落默认。"""

    assert parse_clock("23:05", time(7, 0)) == time(23, 5)
    assert parse_clock("bad", time(7, 0)) == time(7, 0)
    assert parse_clock("24:00", time(7, 0)) == time(7, 0)


def test_sleep_window_crosses_midnight():
    """22:30-07:00 跨午夜窗口：深夜与清晨在窗口内，白天不在。"""

    class Schedule:
        sleep_window_start = "22:30"
        sleep_window_end = "07:00"

    schedule = Schedule()
    assert is_inside_sleep_window(datetime(2026, 11, 7, 23, 0), schedule) is True
    assert is_inside_sleep_window(datetime(2026, 11, 7, 6, 59), schedule) is True
    assert is_inside_sleep_window(datetime(2026, 11, 7, 7, 0), schedule) is False
    assert is_inside_sleep_window(datetime(2026, 11, 7, 12, 0), schedule) is False


def test_choose_sleep_until_clamps_to_bounds():
    """醒来时间倾向目标醒来点，并被最短/最长睡眠时长夹住。"""

    class Schedule:
        sleep_window_start = "22:30"
        sleep_window_end = "07:00"
        target_wake_time = "07:30"
        min_sleep_minutes = 45
        max_sleep_minutes = 480
        wake_jitter_minutes = 0

    # 23:00 入睡，目标醒来点是次日 07:30，共 510 分钟，被 max=480 截断
    until = choose_sleep_until(datetime(2026, 11, 7, 23, 0), Schedule())
    assert until == datetime(2026, 11, 7, 23, 0) + timedelta(minutes=480)

    # 07:10 入睡，目标醒来点 07:30 只有 20 分钟，被 min=45 抬高
    until_min = choose_sleep_until(datetime(2026, 11, 7, 7, 10), Schedule())
    assert (until_min - datetime(2026, 11, 7, 7, 10)).total_seconds() == 45 * 60


def test_format_datetime():
    """时间格式化为本地可读形式。"""

    assert format_datetime(datetime(2026, 11, 7, 23, 5, 9)) == "2026-11-07 23:05:09"
