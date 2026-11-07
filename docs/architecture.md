# 开发文档（architecture）

> 本目录放**开发向文档**——贡献者与 AI 协作者看这里，README 面向用户，内容不要混。
> 配套文档：[development.md](development.md)（环境、测试、发版流程）、[commands.md](commands.md)（命令与权限模型）。

## 系统概览

插件在 Bot 的出站/入站消息链路与 Planner 链路上挂 Hook，实现两件事：

1. **入睡**：Bot 在允许入睡时间窗口内自己发出入睡确认（AI 判定 + 正则兜底）后，建立睡眠记录；
2. **睡眠压制**：睡眠期间拦截入站主链路、暂停表达学习、清空 Planner 工具并丢弃 Planner 响应、拦截后续出站。

睡眠状态按作用域隔离，支持分群作息、静默入睡、睡醒回顾、本地滚动日志。全部 `/sleep` 命令统一受管理员名单门控（详见 [commands.md](commands.md)）。

## 模块结构

- `plugin.py` — 插件入口（必须在根目录）：生命周期（on_load / on_unload / on_config_update）、文件日志挂载、WebUI Schema 本地化。四个 Mixin 按序继承：`SleepHookHandlersMixin` → `SleepCommandHandlersMixin` → `SleepCoreMixin` → `MaiBotPlugin`
- `config/` — 配置模型与 WebUI 文案：
  - `config_models.py` — 9 个配置节（plugin / trigger / sleep_request / schedule / idle_sleep / group_schedule / control / sleep_review / logging），全部字段有默认值，WebUI 元数据走 `__ui_label__` / `json_schema_extra`
  - `schema_i18n.py` — 中文文案表（`SECTION_TITLES` / `FIELD_LABELS` / `FIELD_HINTS`，键为 `(节, 字段)`）与隐藏字段清单
  - `defaults.py` — 默认正则规则与关键词数据（default_factory 供 config_models 引用）
- `commands/handlers.py` — 7 条 `/sleep` 命令的 `@Command` 声明与处理
- `hooks/handlers.py` — 6 个 `@HookHandler` 入口
- `core/` — 核心状态机与工具：
  - `mixin.py` — 睡眠状态机（`_enter_sleep` / `_wake` / `_active_sleep_record`）、作用域解析、入睡判定调度、拦截判断（`_should_block_inbound`）、命令穿透白名单（`_control_command_names`）、自然唤醒与静默入睡后台任务、催睡待确认状态（pending sleep request）
  - `state.py` — `SleepRecord` / `SleepState` 数据类（纯结构，无 IO）
  - `state_storage.py` — 睡眠状态持久化（`sleep_state.json`，格式版本 `PERSISTENCE_VERSION = 2`），数据目录由 `set_data_dir` 注入（on_load 时传入 `ctx.paths.data_dir`）
  - `logging_setup.py` — 滚动文件日志（`RotatingFileHandler` 512KB × 3 备份，挂 `ctx.logger`）
  - `schedule_utils.py` — 作息窗口（支持跨午夜）与醒来时间计算，纯函数，测试直接覆盖
  - `matchers.py` / `pattern_utils.py` — 正则规则匹配（非法正则跳过并告警）
  - `message_utils.py` — 消息字段解析（文本提取、session/group/user ID、@ 检测等）
  - `context_items.py` — Planner Hook 的 Context Item 构造与解析（催睡上下文注入）
- `features/` — 特性模块：
  - `confirmation_judge.py` — AI 入睡确认判定，只接受 `SLEEP / NOT_SLEEP / UNSURE`，LLM 调用走 `ctx.llm.generate`
  - `sleep_review.py` — 睡醒回顾：拦截消息留存与醒来后本地总结报告（`sleep_review/reports/`）
  - `reply_generator.py` — 非入睡时间催睡的回复生成（固定文案或 LLM 生成）
- `tests/` — pytest：conftest 隔离加载 + 配置注入 / 命令注册表 / 权限门 / 纯函数测试

## 运行时状态与持久化

**`SleepRecord`**（每个作用域一条）：

| 字段 | 说明 |
| --- | --- |
| `scope_key` | 作用域键：`group:<群号>` / 私聊聊天流 session / `all`（全体） |
| `scope_label` | 展示名（命令回复里显示） |
| `sleep_started_at` / `sleep_until` | 入睡与预计醒来时间 |
| `sleep_reason` | 入睡原因（命令触发会带 `user=<ID>`） |
| `allowed_trigger_message_id` | 触发入睡的出站消息 ID |

**`SleepState`**（运行期，不持久化除 sleep_records 外的部分）：`session_scope_keys`（session → 作用域映射）、静默入睡计时器（`last_any_activity_by_scope` 等）、命令回复放行窗口（`control_reply_allowed_until`）、催睡待确认（`pending_sleep_request_*`，带 TTL）。

**持久化语义**：`control.persist_sleep_state` 开启时入睡/唤醒即写盘；on_load 恢复未过期记录（`sleep_until` 已过的直接清理）；v1 旧格式（无 `sleep_records` 键）不兼容，按空状态处理。文件位于 `data/plugins/<插件 ID>/sleep_state.json`。

## 数据流

**入站链路**：`chat.receive.before_process`（EARLY）→ `_should_block_inbound`：未启用/未开拦截/未睡眠则放行；睡眠中且文本命中命令穿透白名单（`_control_command_names`）则放行并 `_allow_control_reply()`（给命令回复开出站放行窗口）；否则 abort 拦截并留存睡醒回顾消息。`chat.receive.after_process`（EARLY）二次保险。未拦截的消息继续走 `_handle_sleep_request`（催睡识别 → 窗口外回复并拦截 / 窗口内记录待确认状态并放行）。

**出站链路**：`send_service.after_build_message`（LATE）→ 命令回复放行窗口内直接放行；睡眠中且开拦截则 abort；醒着则走入睡判定（见下节）。

**Planner 链路**：`maisaka.planner.before_request`（EARLY，BLOCKING）睡眠中清空工具并改写请求字段压制；有待确认催睡时注入催睡上下文 Context Item。`maisaka.planner.after_response` 睡眠中丢弃 `output_items`。

**表达学习**：`expression.learn.after_extract` / `before_upsert` 睡眠中 abort。

**副作用出口**：`ctx.send.text`（命令与提示回复，一律 `storage_message=False`，原因见「设计取舍」）、`ctx.llm.generate`（入睡判定 / 回复生成 / 回顾总结）、数据目录文件（`sleep_state.json`、`sleep_review/reports/`、`logs/sleep_manager.log`）。

## 入睡判定流程（出站）

1. 启用检查 → 命令回复放行窗口 → 睡眠压制检查
2. 不在入睡窗口内：命中触发词只记日志，不判定
3. 窗口内：有待确认催睡 → 判定 Bot 的回复；否则仅当出站短句命中「AI 判定触发关键词」（或开启「AI 判定全部短句」）才判定
4. AI 判定器（`confirmation_judge.py`）只接受 `SLEEP / NOT_SLEEP / UNSURE`，仅 `SLEEP` 入睡；AI 不可用/超时/不确定时回落正则兜底（`matchers.py`）
5. 防诱导限制：短句长度上限、拒绝带 @ 组件、拒绝引用回复、拒绝「晚安，某某」式对个人晚安（`directed_patterns`）
6. 判定通过 → `_enter_sleep` 建记录并持久化

## 命令与权限

7 条命令全部过 `admin_user_ids` 名单门（留空 = 对所有人不可用，默认安全）；管理命令（now/forced/forced_all）再过 `admin_sleep_commands_enabled` 开关；被拒时按 `silent_permission_denial` 回复统一提示或零回复拦截。完整模型、配置关系与实现辅助函数见 [commands.md](commands.md)。

## 设计取舍

- **Hook 而非 EventHandler**：主程序 `ON_MESSAGE` 已无发射点，入站拦截只能靠 `chat.receive.*` Hook；`expression.learn.*` 与 `maisaka.planner.*` 是宿主仅有的对应挂点。
- **命令回复一律 `storage_message=False`**：宿主从消息库恢复会话历史时按 `is_bot_self` 把消息标成 `guided_reply`（`is_self_message="true"`）带进 Planner/Replyer 上下文——命令系统文案不写库即可避免麦麦「自己说过」这些话；实时显示不受影响。
- **planner.before_request 只改写不 abort**：该 Hook 不允许 abort（Timing Gate 也复用它），睡眠压制靠改写请求字段实现；改写时 `item_schema_version` 原样保留。
- **命令三层权限**：全部 `/sleep` 命令统一过 `admin_user_ids` 名单门（留空 = 对所有人不可用，默认安全），被拒时按 `silent_permission_denial` 回复提示或零回复拦截；管理命令（now/forced/forced_all）在此之上再受 `admin_sleep_commands_enabled` 开关控制。`control_commands_enabled` 只控制「睡眠期间是否穿透入站拦截」，不做权限过滤——非睡眠期没有入站拦截层，权限只能放在命令层一处生效。
- **`/sleep now` 不拦截消息**：命令返回三元组第三位为 `False`，让消息放行进入 Planner，催睡引导才能生效。
- **AI 判定 + 正则兜底**：AI 不可用或返回不确定时回落正则；为防被诱导入睡，默认只接受短句、自我入睡、群体收尾晚安，带 @ / 引用回复 / 对个人晚安不触发。
- **作用域模型**：`group:<群号>` / 私聊聊天流 / `all` 三层；分群作息命中时用独立配置，未命中群也默认独立作用域（可关）。
- **文件日志滚动限幅**：`RotatingFileHandler` 单文件 512KB、3 备份，避免长期运行磁盘无限增长；handler 挂在 `ctx.logger`（`plugin.<id>`）上，与主进程日志转发共用同一出口，卸载时显式关闭。
- **数据目录不兼容旧版**：`state_storage.py` 未注入数据目录即抛错，不做上游旧版本回退（要求 SDK >= 2.6.0）。

## 给接手者（含 AI）的提示

- **加新命令要同步 6 处**：`commands/handlers.py` 装饰器、`core/mixin.py` 的 `_control_command_names`（睡眠期穿透）、帮助命令文案、README 命令节、`tests/test_plugin.py` 的 `EXPECTED_COMMAND_TEXTS`、`commands.md`。
- **命令必须返回三元组** `(success, response, intercept)`，且自己调 `ctx.send.text`；`success` 位宿主忽略，拦截位非 0 才拦。
- **Hook kwargs 是嵌套结构**：用户 ID 在 `message_info.user_info.user_id`，不要从顶层取；每个 Hook 的 kwargs 都带 `hook_name`。
- **改配置模型只加字段不删字段**，且都要有默认值；`[plugin].enabled` 是宿主保留键，不要声明。
- **本地测试不需要宿主**：`PYTHONPATH=<SDK 副本> uv run --with pytest --with pydantic python -m pytest`，见 [development.md](development.md)。
- manifest 的 host 上界锁当前 MaiBot 小版本线（`1.3.99`），宿主出新小线后实测兼容再抬界发版；Release Tag 必须等于 manifest `version`。
- **`plugin.py` 与 `_manifest.json` 必须留在仓库根目录**（Runner 入口约定，manifest v2 没有入口文件字段），子包重构不能移动它们。
- **文档禁止出现本机绝对路径、账号、服务器地址**——环境信息一律用 `<占位符>` 表述，提交前跑 `git grep` 泄漏自查。
