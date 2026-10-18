# 标记 tests 为包：保证 pytest 加载的 conftest 与测试文件
# `from tests.conftest import ...` 引用的是同一个模块实例（单一测试引擎/夹具）。
