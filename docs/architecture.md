# 开发文档（architecture）

> 本目录放**开发向文档**——贡献者与 AI 协作者看这里，README 面向用户，内容不要混。

## 模块结构

- `plugin.py` — 插件入口：生命周期（on_load / on_unload / on_config_update）、文件日志挂载、WebUI Schema 本地化
- `config_models.py` — 配置模型（8 个业务节 + 日志节），全部字段有默认值，WebUI 元数据走 `__ui_label__` / `json_schema_extra`
- `schema_i18n.py` — WebUI 配置表单的中文文案表（`(节, 字段) → zh_CN`）与隐藏字段清单
- `hook_handlers.py` — 6 个 `@HookHandler` 入口：出站入睡检测、入站双层拦截、表达学习拦截、Planner 请求/响应控制
- `command_handlers.py` — 7 条 `/sleep` 命令的 `@Command` 声明与处理；help / status / wake / wake_all / now / forced / forced_all
- `core_mixin.py` — 核心逻辑：睡眠状态机、作用域管理、入睡判定调度、拦截判断、控制命令白名单、自然唤醒与静默入睡后台任务
- `confirmation_judge.py` — AI 入睡确认判定（只接受 `SLEEP / NOT_SLEEP / UNSURE`），LLM 调用走 `ctx.llm.generate`
- `matchers.py` / `pattern_utils.py` — 正则规则匹配与非法正则跳过
- `message_utils.py` — 消息字段解析（文本提取、会话/群/用户 ID、@ 检测等）
- `context_items.py` — Planner Hook 的 Context Item 构造与解析（催睡上下文注入）
- `schedule_utils.py` — 作息窗口（支持跨午夜）与醒来时间计算，纯函数
- `state.py` / `state_storage.py` — 运行期状态结构与持久化（`data/plugins/<id>/sleep_state.json`）
- `sleep_review.py` — 睡醒回顾：拦截消息留存与醒来后本地总结报告
- `reply_generator.py` — 非入睡时间催睡的回复生成（固定文案或 LLM 生成）
- `defaults.py` — 默认正则规则与关键词数据
- `logging_setup.py` — 滚动文件日志（`RotatingFileHandler`，512KB × 3 备份）
- `tests/` — pytest：conftest 隔离加载 + 配置注入 / 命令注册表 / 帮助命令 / 纯函数测试

## 数据流

**入站链路**：`chat.receive.before_process`（EARLY）→ `_should_block_inbound`：未睡眠或未开拦截则放行；睡眠中且是控制命令（`_control_command_names` 白名单）则穿透；否则 abort 拦截并留存回顾消息。`chat.receive.after_process`（EARLY）做二次保险；未拦截的消息继续走 `_handle_sleep_request`（催睡识别 → 窗口外回复 / 窗口内记录待确认）。

**出站链路**：`send_service.after_build_message`（LATE）→ 睡眠中则拦截出站；醒着则 `_should_enter_sleep_from_outbound` 判定（AI 判定器优先、正则兜底，命中触发词 + 窗口内 + 非对个人晚安）→ `_enter_sleep` 建睡眠记录。

**Planner 链路**：`maisaka.planner.before_request` 睡眠中清空工具并改写请求；有待确认催睡时注入催睡上下文（Context Item）。`maisaka.planner.after_response` 睡眠中丢弃 `output_items`。

**副作用出口**：`ctx.send.text`（命令与提示回复）、`ctx.llm.generate`（入睡判定 / 回复生成 / 回顾总结）、数据目录文件（睡眠状态 JSON、回顾报告、滚动日志）。

## 设计取舍

- **Hook 而非 EventHandler**：主程序 `ON_MESSAGE` 已无发射点，入站拦截只能靠 `chat.receive.*` Hook；`expression.learn.*` 与 `maisaka.planner.*` 是宿主仅有的对应挂点。
- **planner.before_request 只改写不 abort**：该 Hook 不允许 abort（Timing Gate 也复用它），睡眠压制靠改写请求字段实现；改写时 `item_schema_version` 原样保留。
- **命令双层开关**：`control_commands_enabled` 只控制「睡眠期间是否穿透入站拦截」，命令注册本身不受它影响；`force_sleep_commands_enabled` + `admin_user_ids` 控制管理命令可用性，管理员留空 = 默认全禁（安全默认）。
- **`/sleep now` 不拦截消息**：命令返回三元组第三位为 `False`，让消息放行进入 Planner，催睡引导才能生效。
- **AI 判定 + 正则兜底**：AI 不可用或返回不确定时回落正则；为防被诱导入睡，默认只接受短句、自我入睡、群体收尾晚安，带 @ / 引用回复 / 对个人晚安不触发。
- **作用域模型**：`group:<群号>` / 私聊聊天流 / `all` 三层；分群作息命中时用独立配置，未命中群也默认独立作用域（可关）。
- **文件日志滚动限幅**：`RotatingFileHandler` 单文件 512KB、3 备份，避免长期运行磁盘无限增长；handler 挂在 `ctx.logger`（`plugin.<id>`）上，与主进程日志转发共用同一出口，卸载时显式关闭。

## 给接手者（含 AI）的提示

- **命令 pattern 是整行锚定**（`^/sleep xxx\s*$`），加新命令记得同步：`command_handlers.py` 装饰器、`core_mixin._control_command_names`（睡眠期穿透）、帮助命令文案、README、`tests/test_plugin.py` 的 `EXPECTED_COMMAND_TEXTS`。
- **Command 必须返回三元组** `(success, response, intercept)`，且自己调 `ctx.send.text`；`success` 位宿主忽略，拦截位非 0 才拦。
- **Hook kwargs 是嵌套结构**：用户 ID 在 `message_info.user_info.user_id`，不要从顶层取；每个 Hook 的 kwargs 都带 `hook_name`。
- **改配置模型只加字段不删字段**，且都要有默认值；`[plugin].enabled` 是宿主保留键，不要声明。
- **本地测试不需要宿主**：`PYTHONPATH=<maibot-plugin-sdk 副本> uv run --with pytest --with pydantic python -m pytest`，跑法见 `tests/conftest.py`。
- manifest 的 host 上界锁当前 MaiBot 小版本线（`1.3.99`），宿主出新小线后实测兼容再抬界发版；Release Tag 必须等于 manifest `version`。
