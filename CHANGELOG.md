# Changelog

逐版本记录用户能感知的更新要点；版本号提升与依赖更新不单独立目。

## v1.4.1

**主要功能**

- 命令权限全面收紧（安全修复）：全部 `/sleep` 命令统一受"管理员用户 ID"控制，留空时（默认）所有命令对所有人不可用；此前 `/sleep help`、`/sleep status` 等控制命令对所有人开放
- 新增"无权限静默拦截"开关（默认关闭）：开启后无权限命令零回复、仅拦截并记录日志，不希望 Bot 因命令暴露插件存在的场景适用

**细节**

- 配置字段 `force_sleep_commands_enabled` 改名 `admin_sleep_commands_enabled`（作用不变），旧配置里显式设过 `false` 的升级后需重新设置

## v1.4.0

**主要功能**

- 触发命令全面改名：去掉下划线改为空格分隔（如 `/sleep_status` → `/sleep status`），`force` 系列更名 `forced`（`/sleep forced`、`/sleep forced_all`），全部唤醒/入睡命令改为 `/sleep wake_all`、`/sleep forced_all`
- 新增 `/sleep help` 命令，随时查看当前可用的命令帮助；睡眠期间配合"允许控制命令"也能查询
- 新增本地文件日志：滚动写入插件数据目录的 `logs/sleep_manager.log`，排查行为问题不用再翻主程序日志；单文件 512KB、最多 3 个备份，不会无限增长，级别与开关可在 WebUI"日志"节调整
- 命令回复不再进入 Bot 的对话上下文，麦麦不会再把命令说明当成自己说过的话

**细节**

- 插件中心的命令列表与实际触发命令保持一致（显示 `sleep status` 等触发词形态）
- 命令调用也会记录到本地日志（含来源聊天流与用户），权限拒绝记 warning
- 仓库迁移至 `ValleyWinds/Sleep-Manager-Next`，manifest 链接与安装地址同步更新
- 主程序兼容范围调整为 `1.2.5` 至 `1.3.99`，已在 MaiBot 1.3.19 实测
- LICENSE 更新：本仓库采用 GPL-3.0-or-later 官方全文；上游原始代码的 MIT 许可声明以 `LICENSE-upstream` 副本保留
- README 重写，补充日志说明与本地测试指引

## v1.3.1

- 管理入睡命令（催睡/强制入睡）默认对所有人关闭，需在"管理员用户 ID"里显式填写至少一个用户 ID 才能启用

## v1.3.0

- 插件更名为「睡眠管理Next」，插件 ID 变更为 `valleywinds.sleep-manager`；从旧版本升级请重新配置并迁移 `sleep_state.json` 等数据文件

## v1.2.2

- 清理旧版主程序兼容代码，要求主程序 1.2.5 及以上

## v1.2.1

- 放宽主程序版本兼容范围，新版本主程序不再被版本校验挡住
