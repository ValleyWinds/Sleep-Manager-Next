"""插件配置 Schema 文案。

当前插件配置页只渲染中文字符串（不支持把多语言对象作为 React 文本节点渲染），
因此这里只维护 zh_CN 文案，写回 Schema 时直接写字符串。
"""

from typing import Any

LocalizedText = dict[str, str]
DEFAULT_LOCALE = "zh_CN"

SECTION_TITLES: dict[str, LocalizedText] = {
    "plugin": {"zh_CN": "插件"},
    "trigger": {"zh_CN": "触发"},
    "sleep_request": {"zh_CN": "催睡"},
    "schedule": {"zh_CN": "作息"},
    "idle_sleep": {"zh_CN": "静默入睡"},
    "group_schedule": {"zh_CN": "分群作息"},
    "control": {"zh_CN": "拦截"},
    "sleep_review": {"zh_CN": "睡醒回顾"},
    "logging": {"zh_CN": "日志"},
}

SECTION_DESCRIPTIONS: dict[str, LocalizedText] = {
    "plugin": {"zh_CN": "插件基础配置"},
    "trigger": {"zh_CN": "Bot 自己确认入睡时使用的语义判定规则"},
    "sleep_request": {"zh_CN": "用户建议 Bot 睡觉时的处理方式"},
    "schedule": {"zh_CN": "允许入睡和醒来的时间计算"},
    "idle_sleep": {
        "zh_CN": "在允许入睡时间内长时间安静后自动进入睡眠",
    },
    "group_schedule": {
        "zh_CN": "按群号覆盖全局作息，命中时使用独立睡眠状态",
    },
    "control": {"zh_CN": "睡眠期间暂停的主程序链路"},
    "sleep_review": {
        "zh_CN": "醒来后整理睡眠期间被拦截的聊天记录，不会自动回复历史消息",
    },
    "logging": {
        "zh_CN": "插件运行日志的本地落盘与级别",
    },
}

FIELD_LABELS: dict[tuple[str, str], LocalizedText] = {
    ("plugin", "enabled"): {"zh_CN": "启用插件"},
    ("plugin", "config_version"): {"zh_CN": "配置版本"},
    ("trigger", "ai_confirmation_enabled"): {"zh_CN": "AI 语义入睡判定"},
    ("trigger", "ai_confirmation_log_enabled"): {"zh_CN": "显示 AI 入睡判定日志"},
    ("trigger", "ai_confirmation_keywords"): {
        "zh_CN": "AI 判定触发关键词",
    },
    ("trigger", "ai_confirmation_check_all_short_text"): {
        "zh_CN": "AI 判定全部短句",
    },
    ("trigger", "ai_confirmation_timeout_seconds"): {"zh_CN": "AI 入睡判定超时（秒）"},
    ("trigger", "ai_confirmation_max_tokens"): {"zh_CN": "AI 入睡判定输出上限（token）"},
    ("trigger", "max_trigger_chars"): {"zh_CN": "触发短句最大字数"},
    ("trigger", "reject_at_component"): {"zh_CN": "排除 @ 消息"},
    ("trigger", "reject_reply_message"): {"zh_CN": "排除引用回复"},
    ("sleep_request", "enabled"): {"zh_CN": "识别用户催睡"},
    ("sleep_request", "require_mention_in_group"): {"zh_CN": "群聊要求提及 Bot"},
    ("sleep_request", "pending_confirm_seconds"): {"zh_CN": "待确认时长（秒）"},
    ("sleep_request", "off_window_behavior"): {"zh_CN": "非入睡时间行为"},
    ("sleep_request", "off_window_reply"): {"zh_CN": "非入睡时间固定回复"},
    ("schedule", "sleep_window_start"): {"zh_CN": "允许入睡开始"},
    ("schedule", "sleep_window_end"): {"zh_CN": "允许入睡结束"},
    ("schedule", "target_wake_time"): {"zh_CN": "目标醒来时间"},
    ("schedule", "min_sleep_minutes"): {"zh_CN": "最短睡眠时长（分钟）"},
    ("schedule", "max_sleep_minutes"): {"zh_CN": "最长睡眠时长（分钟）"},
    ("schedule", "wake_jitter_minutes"): {"zh_CN": "醒来时间浮动（分钟）"},
    ("idle_sleep", "enabled"): {"zh_CN": "启用静默入睡"},
    ("idle_sleep", "silence_minutes"): {"zh_CN": "完全安静入睡时间（分钟）"},
    ("idle_sleep", "idle_minutes"): {"zh_CN": "无参与入睡时间（分钟）"},
    ("idle_sleep", "check_interval_seconds"): {"zh_CN": "检查间隔（秒）"},
    ("idle_sleep", "topic_grace_seconds"): {"zh_CN": "话题判断缓冲（秒）"},
    ("idle_sleep", "mention_extends_grace"): {"zh_CN": "提及延长缓冲"},
    ("idle_sleep", "at_extends_grace"): {"zh_CN": "@ 延长缓冲"},
    ("idle_sleep", "wake_on_mention_while_sleeping"): {
        "zh_CN": "睡眠中提及唤醒",
    },
    ("idle_sleep", "count_planner_actions_as_activity"): {
        "zh_CN": "Planner 动作算参与",
    },
    ("group_schedule", "independent_default_scopes"): {
        "zh_CN": "默认聊天流独立睡眠",
    },
    ("group_schedule", "group_schedules"): {"zh_CN": "群作息覆盖"},
    ("control", "block_inbound_messages"): {"zh_CN": "暂停入站消息"},
    ("control", "block_expression_learning"): {"zh_CN": "暂停表达学习"},
    ("control", "block_outbound_messages"): {"zh_CN": "暂停后续出站消息"},
    ("control", "planner_control_enabled"): {"zh_CN": "暂停 Planner 结果"},
    ("control", "control_commands_enabled"): {"zh_CN": "允许控制命令"},
    ("control", "persist_sleep_state"): {"zh_CN": "持久化睡眠状态"},
    ("control", "natural_wake_enabled"): {"zh_CN": "自然到点醒来"},
    ("control", "admin_sleep_commands_enabled"): {"zh_CN": "允许管理入睡命令"},
    ("control", "silent_permission_denial"): {"zh_CN": "无权限静默拦截"},
    ("control", "admin_user_ids"): {"zh_CN": "管理员用户 ID"},
    ("sleep_review", "enabled"): {"zh_CN": "启用睡醒回顾"},
    ("sleep_review", "max_summary_messages_per_chat"): {"zh_CN": "单聊最大消息数"},
    ("sleep_review", "max_summary_chars_per_chat"): {"zh_CN": "单聊最大字符数"},
    ("sleep_review", "max_review_chats_per_wake"): {"zh_CN": "单次最大聊天流"},
    ("sleep_review", "max_summary_tokens"): {"zh_CN": "单聊总结输出上限（token）"},
    ("logging", "file_log_enabled"): {"zh_CN": "文件日志"},
    ("logging", "file_log_level"): {"zh_CN": "文件日志级别"},
}

ITEM_FIELD_LABELS: dict[tuple[str, str, str], LocalizedText] = {
    ("group_schedule", "group_schedules", "enabled"): {"zh_CN": "启用"},
    ("group_schedule", "group_schedules", "group_id"): {"zh_CN": "群号"},
    ("group_schedule", "group_schedules", "sleep_window_start"): {"zh_CN": "允许入睡开始"},
    ("group_schedule", "group_schedules", "sleep_window_end"): {"zh_CN": "允许入睡结束"},
    ("group_schedule", "group_schedules", "target_wake_time"): {"zh_CN": "目标醒来时间"},
    ("group_schedule", "group_schedules", "min_sleep_minutes"): {"zh_CN": "最短睡眠时长（分钟）"},
    ("group_schedule", "group_schedules", "max_sleep_minutes"): {"zh_CN": "最长睡眠时长（分钟）"},
    ("group_schedule", "group_schedules", "wake_jitter_minutes"): {"zh_CN": "醒来时间浮动（分钟）"},
}

FIELD_HINTS: dict[tuple[str, str], LocalizedText] = {
    ("sleep_request", "off_window_reply"): {
        "zh_CN": "留空时会读取主程序人格和表达风格，用 replyer 模型生成一句回复",
    },
    ("sleep_request", "off_window_behavior"): {
        "zh_CN": "reply=回复并拦截，silent=静默拦截，pass=交给主链路处理",
    },
    ("trigger", "ai_confirmation_enabled"): {
        "zh_CN": "开启后，在允许入睡时间内，对已有合理催睡或 Bot 自己发出含睡眠意图的短句调用 replyer 模型，只接受 SLEEP/NOT_SLEEP/UNSURE",
    },
    ("trigger", "ai_confirmation_log_enabled"): {
        "zh_CN": "开启后会记录入睡判定跳过原因、AI 判定开始/结果/耗时，以及正则兜底结果",
    },
    ("trigger", "ai_confirmation_keywords"): {
        "zh_CN": "没有待确认催睡时，Bot 出站短句命中任一关键词才会调用 AI 入睡判定。使用英文逗号或中文逗号分隔；开启“AI 判定全部短句”后不依赖这里的关键词",
    },
    ("trigger", "ai_confirmation_check_all_short_text"): {
        "zh_CN": "默认关闭。开启后，在允许入睡时间内，所有短出站文本都会交给 AI 判定，不再要求先命中睡眠相关关键词；会增加模型调用次数",
    },
    ("trigger", "ai_confirmation_timeout_seconds"): {
        "zh_CN": "填 0 时插件内部不主动超时，会等待 LLM 自己返回；填大于 0 的秒数时，超时后按 UNSURE 处理并转入正则兜底。出站检测 Hook 为 120 秒",
    },
    ("trigger", "ai_confirmation_max_tokens"): {
        "zh_CN": "默认 256。过低可能导致部分模型在输出 SLEEP/NOT_SLEEP/UNSURE 前被截断并返回空内容；建议保持 256 或更高",
    },
    ("group_schedule", "group_schedules"): {
        "zh_CN": "同一群号命中后使用这里的作息和睡眠时长，并拥有独立睡眠状态，不受全局睡眠影响",
    },
    ("group_schedule", "independent_default_scopes"): {
        "zh_CN": "默认开启。未配置分群作息的群聊和私聊仍共用全局作息时间，但各自维护睡眠状态和静默计时；关闭后恢复旧逻辑，所有默认聊天流共用全局睡眠状态",
    },
    ("idle_sleep", "enabled"): {
        "zh_CN": "默认关闭。开启后不会调用模型，只按最近活动和 Bot 参与时间判断；进入睡眠时也不会主动补发晚安消息",
    },
    ("idle_sleep", "silence_minutes"): {
        "zh_CN": "进入允许入睡时间后，对应作用域完全没有入站消息和出站消息达到这么久，就自动进入睡眠",
    },
    ("idle_sleep", "idle_minutes"): {
        "zh_CN": "进入允许入睡时间后，Bot 连续这么久没有出站或有效 Planner 动作，就自动进入睡眠；群里有人聊天但 Bot 没参与也会继续累计",
    },
    ("idle_sleep", "check_interval_seconds"): {
        "zh_CN": "后台检查频率。数值越小越及时，但检查更频繁；该检查不消耗 LLM token",
    },
    ("idle_sleep", "topic_grace_seconds"): {
        "zh_CN": "无参与计时临近入睡时，新入站消息会获得一次判断缓冲，避免刚出现新话题就被后台检查切入睡眠；普通消息每个无参与周期只给一次缓冲",
    },
    ("idle_sleep", "mention_extends_grace"): {
        "zh_CN": "开启后，被文字提及时会延长临睡前判断缓冲，让 Planner 有机会响应直接呼唤",
    },
    ("idle_sleep", "at_extends_grace"): {
        "zh_CN": "开启后，被 @ 时会延长临睡前判断缓冲；适合启用了 @ 必回复的场景",
    },
    ("idle_sleep", "wake_on_mention_while_sleeping"): {
        "zh_CN": "默认关闭。开启后，睡眠期间被提及或 @ 会先唤醒再放行这条消息；关闭时会像普通睡眠消息一样拦截并可进入睡醒回顾",
    },
    ("idle_sleep", "count_planner_actions_as_activity"): {
        "zh_CN": "开启后，Planner 调用 reply、send_emoji 或其他有效动作时会刷新无参与计时；no_action/no_reply/no_react/no_plan/finish/wait/continue 不算参与",
    },
    ("control", "persist_sleep_state"): {
        "zh_CN": "开启后会把未过期的睡眠状态保存到插件数据目录（data/plugins/<插件 ID>/sleep_state.json）",
    },
    ("control", "natural_wake_enabled"): {
        "zh_CN": "默认开启。进入睡眠后才启动轻量后台检查，到达预计醒来时间后自动清理睡眠状态；不调用模型、不消耗 token。关闭后只会在消息、命令或其他链路查询睡眠状态时懒唤醒",
    },
    ("control", "admin_sleep_commands_enabled"): {
        "zh_CN": "开启后允许使用 /sleep now 引导入睡，或使用 /sleep forced、/sleep forced_all 强制入睡",
    },
    ("control", "silent_permission_denial"): {
        "zh_CN": "默认关闭，无权限使用命令时会回复一句无权限提示；开启后所有无权限命令零回复、仅拦截并记录日志，适合不希望 Bot 因命令暴露插件存在的场景",
    },
    ("control", "admin_user_ids"): {
        "zh_CN": "填写后只有这些用户 ID 可使用全部 /sleep 命令；留空时所有命令对所有人不可用（默认安全），需填写至少一个用户 ID 才能启用",
    },
    ("sleep_review", "enabled"): {
        "zh_CN": "开启后，睡眠期间被拦截的消息会保存到本地；对应作用域醒来时按群聊/私聊生成回顾文件，不会向聊天流补发回复",
    },
    ("sleep_review", "max_summary_messages_per_chat"): {
        "zh_CN": "启用睡醒回顾后生效。每个群聊/私聊只把最后这些条消息送入总结模型；完整轻量记录仍保存在回顾文件里",
    },
    ("sleep_review", "max_summary_chars_per_chat"): {
        "zh_CN": "启用睡醒回顾后生效。每个群聊/私聊送入总结模型的聊天文本字符上限，用于控制输入 token",
    },
    ("sleep_review", "max_review_chats_per_wake"): {
        "zh_CN": "启用睡醒回顾后生效。一次醒来最多调用模型总结这些聊天流；超出的聊天流只保存记录和基础统计",
    },
    ("sleep_review", "max_summary_tokens"): {
        "zh_CN": "启用睡醒回顾后生效。每个聊天流总结的输出 token 上限，用于控制输出成本",
    },
    ("logging", "file_log_enabled"): {
        "zh_CN": "开启后插件日志滚动写入插件数据目录的 logs/sleep_manager.log，单文件 512KB、最多 3 个备份，总体积约 2MB 上限，不会无限增长",
    },
    ("logging", "file_log_level"): {
        "zh_CN": "默认 INFO 满足日常排查；需要更细链路时再开 DEBUG，WARNING/ERROR 只记录异常",
    },
}

HIDDEN_VISUAL_FIELDS: set[tuple[str, str]] = {
    ("plugin", "config_version"),
    ("trigger", "goodnight_patterns"),
    ("trigger", "pending_goodnight_patterns"),
    ("trigger", "directed_patterns"),
    ("trigger", "max_trigger_chars"),
    ("sleep_request", "request_patterns"),
}

SLEEP_REVIEW_LIMIT_FIELDS: set[str] = {
    "max_summary_messages_per_chat",
    "max_summary_chars_per_chat",
    "max_review_chats_per_wake",
    "max_summary_tokens",
}

IDLE_SLEEP_LIMIT_FIELDS: set[str] = {
    "silence_minutes",
    "idle_minutes",
    "check_interval_seconds",
    "topic_grace_seconds",
}


def apply_config_schema_i18n(schema: dict[str, Any]) -> dict[str, Any]:
    """给插件 WebUI 配置 Schema 注入标题、标签和提示"""

    sections = schema.get("sections")
    if not isinstance(sections, dict):
        return schema

    for section_name, section in sections.items():
        if not isinstance(section, dict):
            continue
        if section_name in SECTION_TITLES:
            section["title"] = _resolve_text(SECTION_TITLES[section_name])
        if section_name in SECTION_DESCRIPTIONS:
            section["description"] = _resolve_text(SECTION_DESCRIPTIONS[section_name])

        fields = section.get("fields")
        if not isinstance(fields, dict):
            continue
        for field_name, field in fields.items():
            if not isinstance(field, dict):
                continue
            key = (str(section_name), str(field_name))
            if key in FIELD_LABELS:
                field["label"] = _resolve_text(FIELD_LABELS[key])
            if key in FIELD_HINTS:
                field["hint"] = _resolve_text(FIELD_HINTS[key])
            if key in HIDDEN_VISUAL_FIELDS:
                field["hidden"] = True
            if section_name == "idle_sleep" and field_name in IDLE_SLEEP_LIMIT_FIELDS:
                field["min"] = 1
                field["step"] = 1
            if section_name == "sleep_review" and field_name in SLEEP_REVIEW_LIMIT_FIELDS:
                field["min"] = 1
                field["step"] = 1
            _apply_item_field_labels(str(section_name), str(field_name), field)
    return schema


def _apply_item_field_labels(section_name: str, field_name: str, field: dict[str, Any]) -> None:
    """给列表对象项的字段注入本地化标签。"""

    item_fields = field.get("item_fields")
    if not isinstance(item_fields, dict):
        return

    for item_field_name, item_field in item_fields.items():
        if not isinstance(item_field, dict):
            continue
        key = (section_name, field_name, str(item_field_name))
        if key in ITEM_FIELD_LABELS:
            item_field["label"] = _resolve_text(ITEM_FIELD_LABELS[key])


def _resolve_text(text: LocalizedText) -> str:
    """取配置文案；当前 WebUI 只渲染中文字符串。"""

    return text.get(DEFAULT_LOCALE, "")
