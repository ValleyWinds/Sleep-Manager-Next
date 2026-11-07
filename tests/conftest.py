"""pytest 隔离加载插件（不需要 MaiBot 宿主）。

跑法（需要 maibot_sdk 可导入，指向本地 SDK 源码副本即可）：

    PYTHONPATH=<maibot-plugin-sdk 仓库路径> uv run --with pytest --with pydantic python -m pytest

裸 spec_from_file_location 加载带 `from .config import ...` 的多文件插件会直接
ImportError，必须设 submodule_search_locations + __path__ 并先注册 sys.modules。
"""

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

PLUGIN_DIR = Path(__file__).parents[1]


@pytest.fixture(scope="session")
def plugin_module():
    """把插件目录作为包隔离加载，返回 plugin 模块。"""

    spec = spec_from_file_location(
        "sleep_manager_next",
        PLUGIN_DIR / "plugin.py",
        submodule_search_locations=[str(PLUGIN_DIR)],
    )
    module = module_from_spec(spec)
    module.__path__ = [str(PLUGIN_DIR)]
    sys.modules["sleep_manager_next"] = module
    spec.loader.exec_module(module)
    return module
