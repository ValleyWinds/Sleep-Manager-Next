# 开发文档（development）

> 环境、测试与发版流程。架构见 [architecture.md](architecture.md)，命令与权限见 [commands.md](commands.md)。

## 目录约定

- `plugin.py` 与 `_manifest.json` **必须在仓库根目录**：Runner 以根目录的 `plugin.py` 为入口（manifest v2 没有入口文件字段），`_manifest.json` 也必须根目录。子包重构只能移动其余模块。
- 业务代码按职责分五个子包：`config/`、`commands/`、`hooks/`、`core/`、`features/`，各包一个只带 docstring 的 `__init__.py`。跨包一律相对导入（`from ..core.state import ...`），同包内 `from .xxx import`。
- `config.toml` 不入库（Runner 首次加载按 `config_model` 自动生成在插件目录），`.gitignore` 已覆盖。

## 本地环境

- 本地 MaiBot 实例：宿主源码仓库（checkout 需与目标宿主版本对齐，动手前 `git describe --tags` 确认基线），下文记为 `<MaiBot 实例目录>`
- SDK 源码副本：maibot-plugin-sdk 仓库本地 checkout，下文记为 `<SDK 副本>`；离线测试与实例 venv 共用其版本语义
- Python/包管理：uv（`uv run --with pytest --with pydantic` 临时环境即可，无需建 venv）

## 离线测试（不需要宿主）

```bash
PYTHONPATH=<SDK 副本路径> uv run --with pytest --with pydantic python -m pytest
```

- `tests/conftest.py` 用 `spec_from_file_location` + `submodule_search_locations` 把插件目录作为包隔离加载（带相对导入的多文件插件裸加载会 ImportError，必须预注册 `sys.modules`）
- 测试注入点（SDK 真实、只假最外层 RPC）：
  - `plugin.set_plugin_config({...})` — 注入配置 dict（带 `[plugin].config_version` 节）
  - `plugin._set_context(PluginContext(plugin_id, rpc_call=fake_rpc))` — 假 RPC 通道，断言 `send.text` 的 wire 级参数与三元组返回
- 覆盖面：默认配置、命令注册表（新命令 pattern 覆盖 + 旧命令不匹配回归断言）、穿透白名单、权限门三态（默认拒绝 / 静默零回复 / 名单放行）、作息窗口跨午夜、醒来时间 min/max 夹逼等纯函数

## 实例实测（热重载）

1. 部署：`<MaiBot 实例目录>/plugins/` 下 clone 本仓库并检出工作分支（或已有目录 `git fetch && git reset --hard origin/<branch>`）
2. watchfiles 约 2~6 秒自动热加载，无需重启；加载成功看插件数据目录日志 `data/plugins/valleywinds.sleep-manager/logs/sleep_manager.log` 的「睡眠管理Next已加载」
3. 命令在 WebUI 聊天页发（本地聊天室用户 ID 为 `owner`）；WebUI「插件管理」可见组件与配置表单
4. 注意：改 `config.toml` 的字段名时，宿主会把磁盘上的未知旧键原样保留，替换字段名要手工删旧键插新键；无 config_model 的探针插件打开配置页报「插件未提供配置定义」是正常现象

## 分支与发版

- 工作分支 `dev`，自由 push；**`main` 为发版分支，合入与推送前需维护者确认**
- 发版流程：
  1. dev 上验证完毕（离线测试全绿 + 实例实测）
  2. bump `_manifest.json` 的 `version`（严格三段式），`CHANGELOG.md` 「未发布」段改为实际版本号
  3. 合 dev → main，打与 `version` 一致的 Tag（`v<版本号>`，Tag 一经收录不可变，修复发新版本号）
  4. `gh release create`，Notes 只写用户可感知的更新要点（分「主要功能 / 细节」，一个功能一行）
- 发版前自检：
  - manifest 权威校验（宿主同款校验器）：在 `<MaiBot 实例目录>` 执行
    `uv run python -c "from src.plugin_runtime.runner.manifest_validator import PluginManifest; PluginManifest.model_validate(json.load(open('<插件>/_manifest.json', encoding='utf-8')))"`
  - 泄漏扫描：`git grep` 检查本机路径、邮箱、服务器 IP 等不入库；**提交前必做**，文档里的环境信息一律用 `<占位符>` 表述
  - Tag 必须等于 manifest `version`，插件 ID 不得变更，否则插件中心拒收
