"""睡眠管理Next命令处理器

命令回复统一 storage_message=False：不写入消息库，避免宿主从库中恢复
会话历史时把这些系统文案当成麦麦自己说过的话（is_self_message）带进
Planner / Replyer 上下文。实时显示不受影响。

全部命令统一过 admin_user_ids 名单门（留空 = 对所有人不可用，默认安全）；
被拒绝时按 silent_permission_denial 决定回复提示还是零回复静默拦截。
"""

from datetime import datetime
from typing import Any

from maibot_sdk import Command

from .core_mixin import ALL_SLEEP_SCOPE


class SleepCommandHandlersMixin:
    """声明插件命令入口"""

    @Command("sleep help", description="查看全部命令帮助", pattern=r"^/sleep help\s*$")
    async def handle_help_command(
        self,
        stream_id: str = "",
        group_id: str = "",
        user_id: str = "",
        **kwargs: Any,
    ) -> tuple[bool, str, bool]:
        """打印当前可用的全部命令帮助"""

        del kwargs

        self.ctx.logger.info(f"收到命令 /sleep help: stream={stream_id or '未知'}")
        self._allow_control_reply()
        if not self._can_use_sleep_command(user_id):
            return await self._deny_command(stream_id, user_id, "/sleep help")

        lines = [
            "[睡眠管理] 命令帮助",
            "/sleep help - 查看本帮助",
            "/sleep status - 查看当前作用域的睡眠状态",
            "/sleep wake - 手动唤醒当前作用域",
            "/sleep wake_all - 手动唤醒全部聊天流",
        ]
        if self.config.control.admin_sleep_commands_enabled:
            lines.extend(
                [
                    "/sleep now - 允许入睡时间内引导 Bot 自己决定是否入睡（管理命令）",
                    "/sleep forced - 无视时间窗口立即入睡（管理命令）",
                    "/sleep forced_all - 无视时间窗口让全部聊天流入睡（管理命令）",
                ]
            )
        else:
            lines.append("管理入睡命令已在配置中关闭")
        message = "\n".join(lines)
        await self.ctx.send.text(message, stream_id, storage_message=False)
        return True, message, True

    @Command("sleep status", description="查看当前作用域的睡眠状态", pattern=r"^/sleep status\s*$")
    async def handle_status_command(
        self,
        stream_id: str = "",
        group_id: str = "",
        user_id: str = "",
        **kwargs: Any,
    ) -> tuple[bool, str, bool]:
        """查看当前睡眠状态"""

        del kwargs

        self.ctx.logger.info(f"收到命令 /sleep status: stream={stream_id or '未知'}")
        self._allow_control_reply()
        if not self._can_use_sleep_command(user_id):
            return await self._deny_command(stream_id, user_id, "/sleep status")

        command_message = self._message_stub_for_command(stream_id, group_id)
        scope_key, scope_label = self._sleep_scope_for_message(command_message)
        sleep_record = self._active_sleep_record(message=command_message)
        if sleep_record is not None and sleep_record.sleep_until is not None:
            message = (
                "[睡眠管理] 当前正在睡眠\n"
                f"作用域: {sleep_record.scope_label}\n"
                f"预计醒来时间: {self._format_datetime(sleep_record.sleep_until)}\n"
                f"原因: {sleep_record.sleep_reason or '未记录'}\n"
                f"持久化: {'已启用' if self.config.control.persist_sleep_state else '已关闭'}"
            )
        else:
            message = (
                "[睡眠管理] 当前未处于睡眠状态\n"
                f"作用域: {scope_label}\n"
                f"持久化: {'已启用' if self.config.control.persist_sleep_state else '已关闭'}"
            )
        await self.ctx.send.text(message, stream_id, storage_message=False)
        return True, message, True

    @Command("sleep wake", description="手动唤醒当前作用域，不解除全部聊天流睡眠", pattern=r"^/sleep wake\s*$")
    async def handle_wake_command(
        self,
        stream_id: str = "",
        group_id: str = "",
        user_id: str = "",
        **kwargs: Any,
    ) -> tuple[bool, str, bool]:
        """手动解除睡眠状态"""

        del kwargs

        self.ctx.logger.info(f"收到命令 /sleep wake: stream={stream_id or '未知'}")
        self._allow_control_reply()
        if not self._can_use_sleep_command(user_id):
            return await self._deny_command(stream_id, user_id, "/sleep wake")

        command_message = self._message_stub_for_command(stream_id, group_id)
        scope_key, scope_label = self._sleep_scope_for_message(command_message)
        all_sleep_record = self._active_sleep_record(scope_key=ALL_SLEEP_SCOPE)
        sleep_record = self._active_sleep_record_exact(scope_key)
        if all_sleep_record is not None:
            message = (
                "[睡眠管理] 当前处于全部聊天流睡眠\n"
                f"当前作用域: {scope_label}\n"
                "需要解除全部聊天流睡眠时，请使用 /sleep wake_all"
            )
        elif sleep_record is not None:
            self._wake_sleep_record(sleep_record, "手动唤醒")
            message = f"[睡眠管理] 已手动唤醒\n作用域: {sleep_record.scope_label}"
        else:
            message = f"[睡眠管理] 当前本来就是醒着\n作用域: {scope_label}"
        await self.ctx.send.text(message, stream_id, storage_message=False)
        return True, message, True

    @Command("sleep wake_all", description="手动唤醒全部聊天流，解除所有睡眠作用域", pattern=r"^/sleep wake_all\s*$")
    async def handle_wake_all_command(
        self,
        stream_id: str = "",
        group_id: str = "",
        user_id: str = "",
        **kwargs: Any,
    ) -> tuple[bool, str, bool]:
        """手动解除全部睡眠状态"""

        del group_id
        del kwargs

        self.ctx.logger.info(f"收到命令 /sleep wake_all: stream={stream_id or '未知'}")
        self._allow_control_reply()
        if not self._can_use_sleep_command(user_id):
            return await self._deny_command(stream_id, user_id, "/sleep wake_all")

        wake_count = self._wake_all_sleep_records("手动全部唤醒")
        if wake_count:
            message = f"[睡眠管理] 已手动唤醒全部聊天流\n已解除睡眠作用域: {wake_count} 个"
        else:
            message = "[睡眠管理] 当前没有正在生效的睡眠状态"
        await self.ctx.send.text(message, stream_id, storage_message=False)
        return True, message, True

    @Command("sleep now", description="允许入睡时间内记录一次管理员催睡，等 Bot 自己确认", pattern=r"^/sleep now\s*$")
    async def handle_sleep_now_command(
        self,
        stream_id: str = "",
        group_id: str = "",
        user_id: str = "",
        **kwargs: Any,
    ) -> tuple[bool, str, bool]:
        """在允许入睡时间内记录一次管理员催睡，并放行给主链路判断"""

        del kwargs

        self._allow_control_reply()
        self.ctx.logger.info(f"收到命令 /sleep now: stream={stream_id or '未知'} user={user_id or '未知'}")
        deny_message = await self._check_command_permission(stream_id, user_id, "/sleep now")
        if deny_message is not None:
            return True, deny_message, True

        command_message = self._message_stub_for_command(stream_id, group_id)
        sleep_record = self._active_sleep_record(message=command_message)
        if sleep_record is not None and sleep_record.sleep_until is not None:
            message = (
                "[睡眠管理] 当前已经在睡眠中\n"
                f"作用域: {sleep_record.scope_label}\n"
                f"预计醒来时间: {self._format_datetime(sleep_record.sleep_until)}"
            )
            await self.ctx.send.text(message, stream_id, storage_message=False)
            return True, message, True

        now = datetime.now()
        schedule_config, schedule_source = self._schedule_for_message_with_source(command_message)
        if not self._is_inside_sleep_window(now, command_message):
            message = (
                "[睡眠管理] 当前不在允许入睡时间内\n"
                f"生效作息: {schedule_source}\n"
                f"允许入睡: {schedule_config.sleep_window_start} - {schedule_config.sleep_window_end}\n"
                "需要无视时间窗口测试时，请使用 /sleep forced"
            )
            await self.ctx.send.text(message, stream_id, storage_message=False)
            return True, message, True

        self._set_pending_sleep_request(command_message, "/sleep now 管理命令催睡")
        message = (
            "[睡眠管理] 已记录管理员催睡，将交给主链路判断是否入睡\n"
            f"生效作息: {schedule_source}"
        )
        await self.ctx.send.text(message, stream_id, storage_message=False)
        # 拦截位必须为 False：放行这条消息才能触发 Planner，
        # planner.before_request 才有机会注入催睡上下文（详见 core_mixin 的
        # _build_pending_sleep_request_planner_context）。拦截会让催睡引导失效。
        return True, message, False

    @Command("sleep forced", description="无视入睡窗口，让当前作用域立即睡眠（管理命令）", pattern=r"^/sleep forced\s*$")
    async def handle_sleep_force_command(
        self,
        stream_id: str = "",
        group_id: str = "",
        user_id: str = "",
        **kwargs: Any,
    ) -> tuple[bool, str, bool]:
        """无视允许入睡窗口手动触发入睡，用于管理员测试和紧急控制"""

        del kwargs

        self.ctx.logger.info(f"收到命令 /sleep forced: stream={stream_id or '未知'} user={user_id or '未知'}")
        return await self._handle_sleep_force_command(
            stream_id=stream_id,
            group_id=group_id,
            user_id=user_id,
        )

    @Command("sleep forced_all", description="无视入睡窗口，让全部聊天流进入睡眠（管理命令）", pattern=r"^/sleep forced_all\s*$")
    async def handle_sleep_force_all_command(
        self,
        stream_id: str = "",
        group_id: str = "",
        user_id: str = "",
        **kwargs: Any,
    ) -> tuple[bool, str, bool]:
        """无视允许入睡窗口，手动触发全部聊天流进入睡眠"""

        del kwargs
        del group_id

        self.ctx.logger.info(f"收到命令 /sleep forced_all: stream={stream_id or '未知'} user={user_id or '未知'}")
        return await self._handle_sleep_force_command(
            stream_id=stream_id,
            group_id="",
            user_id=user_id,
            force_all=True,
        )

    async def _handle_sleep_force_command(
        self,
        *,
        stream_id: str,
        group_id: str,
        user_id: str,
        force_all: bool = False,
    ) -> tuple[bool, str, bool]:
        """执行无视时间窗口的强制入睡命令。"""

        self._allow_control_reply()
        deny_message = await self._check_command_permission(
            stream_id, user_id, "/sleep forced_all" if force_all else "/sleep forced"
        )
        if deny_message is not None:
            return True, deny_message, True

        command_message = self._message_stub_for_command(stream_id, group_id)
        sleep_record = (
            self._active_sleep_record(scope_key=ALL_SLEEP_SCOPE)
            if force_all
            else self._active_sleep_record(message=command_message)
        )
        if sleep_record is not None and sleep_record.sleep_until is not None:
            message = (
                "[睡眠管理] 当前已经在睡眠中\n"
                f"作用域: {sleep_record.scope_label}\n"
                f"预计醒来时间: {self._format_datetime(sleep_record.sleep_until)}"
            )
            await self.ctx.send.text(message, stream_id, storage_message=False)
            return True, message, True

        now = datetime.now()
        replaced_count = self._wake_all_sleep_records("/sleep forced_all 覆盖已有睡眠状态") if force_all else 0
        _, schedule_source = (
            (self.config.schedule, "全局配置")
            if force_all
            else self._schedule_for_message_with_source(command_message)
        )

        sleep_until = self._choose_sleep_until(now, None if force_all else command_message)
        reason = "/sleep forced_all 管理命令触发" if force_all else "/sleep forced 管理命令触发"
        if user_id.strip():
            reason = f"{reason}: user={user_id.strip()}"
        if force_all:
            self._enter_sleep(sleep_until, reason, None, scope_key=ALL_SLEEP_SCOPE, scope_label="全部聊天流")
        else:
            self._enter_sleep(sleep_until, reason, command_message)
        message = (
            f"[睡眠管理] 已进入{'全体' if force_all else ''}睡眠\n"
            f"生效作息: {schedule_source}\n"
            f"预计醒来时间: {self._format_datetime(sleep_until)}"
        )
        if replaced_count:
            message = f"{message}\n已覆盖原有睡眠作用域: {replaced_count} 个"
        await self.ctx.send.text(message, stream_id, storage_message=False)
        return True, message, True
