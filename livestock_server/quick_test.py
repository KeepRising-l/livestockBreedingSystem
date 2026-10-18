"""
快速冒烟脚本：跑一遍端到端核心链路（注册→圈舍→入栏→饲喂→审核→库存→出栏销售）。

实现说明：旧的"import app 之前手动替换全局 DB 引擎"方式已废弃（依赖 import
顺序、导入路径失效）。现在冒烟链路收敛到 tests/test_smoke.py，由 pytest
夹具提供 SQLite 内存库与依赖覆盖，本脚本只是它的薄包装，保证可重复执行。

运行（livestock_server 目录下）：
    python quick_test.py
等价于：
    python -m pytest tests/test_smoke.py -v

完整回归测试：
    python -m pytest tests/ -v
"""
import os
import sys

import pytest

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    smoke = os.path.join(here, "tests", "test_smoke.py")
    sys.exit(pytest.main([smoke, "-v", "--no-header"]))
