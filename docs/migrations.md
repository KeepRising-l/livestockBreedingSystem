# 数据库迁移指南（Alembic）

## 背景

此前表结构完全依赖两条路径维护：

1. `app/main.py` 启动时的 `Base.metadata.create_all`（只能建新表，不改已有表）；
2. `main.py` 里 5 个手写「轻量迁移」函数（补列/回填/建索引，异常只打印）。

结构漂移和迁移半途失败都无从追踪。现引入 Alembic（`alembic==1.13.1`，此前声明了依赖但从未使用）统一管理 schema 变更。

## 现状

- baseline 迁移：`migrations/versions/*_baseline_full_schema_from_models.py`（由模型 autogenerate，含全部 30 张表）
- 本机开发库已 `alembic stamp head`（表已由 create_all 建好，只登记版本号，不重复执行）
- 连接串自动取自 `.env`；需要指向别的库时用环境变量 `ALEMBIC_DATABASE_URI` 覆盖

## 日常流程（改了 models 之后）

```bash
# 1. 生成迁移（务必人工检查生成的 diff，autogenerate 不识别改名/数据迁移）
./venv/Scripts/python.exe -m alembic revision --autogenerate -m "描述"

# 2. 检查 migrations/versions/ 下新文件，删掉误判的变更

# 3. 应用到本地库
./venv/Scripts/python.exe -m alembic upgrade head
```

提交代码时把生成的迁移文件一起提交，其他环境各自 `upgrade head`。

## 环境接入

| 场景 | 做法 |
|------|------|
| 已有数据的库（表已存在） | `alembic stamp head` 一次性登记版本 |
| 全新空库 | `alembic upgrade head` 直接建全量表（可替代启动建表） |
| 回滚一版 | `alembic downgrade -1` |

## 约定

- `main.py` 启动期的 `create_all` 与 5 个轻量迁移函数暂时保留（兼容现有部署），新的结构变更一律走 Alembic，不再往里加新的补列函数。
- 迁移文件一经合并入库不得修改；改错了就再写一个新迁移修正。
