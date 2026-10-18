# 🐄 智能养殖信息管理系统

面向中小型养殖场的全栈管理系统，覆盖「入栏 → 饲喂 → 防疫诊疗 → 繁育 → 审核 → 库存 → 出栏」的完整生产流程。

## ✨ 功能特性

| 模块 | 说明 |
| --- | --- |
| 认证管理 | 养殖场主注册 / 员工添加、JWT 登录、多租户（按养殖场隔离数据） |
| 圈舍管理 | A/B/C/D 四类圈舍，容量校验，圈舍内畜禽列表 |
| 畜禽档案 | 个体/批量入栏、耳标自动生成（畜种位 + 圈舍编号2位 + 序号2位，共 5 位，空号复用）、转圈舍重生耳标、生长阶段自动判定（牛/羊/猪三套配置）、历史记录与恢复 |
| 饲喂管理 | 饲喂方案（成本自动计算）、饲喂记录提交 → 场主审核，同日同时段同圈舍防重复 |
| 物资库存 | 饲料/疫苗/兽药库存，进货/领用 → 审核通过后自动增减库存，有效期与缺货状态自动维护 |
| 防疫诊疗 | 防疫记录（支持批量）+ 诊疗记录，员工提交 → 场主审核，疫苗类型字典白名单 |
| 繁育管理 | 母畜/公畜档案、配种记录（预产期自动计算：牛280/羊150/猪114天）、孕检登记、产犊记录（存活率自动算）、繁育预警处理 |
| 审核中心 | 饲喂/进货/领用/防疫/诊疗/配种六类待审核记录统一入口，场主一键通过/驳回 |
| 系统管理 | 用户/角色/日志/通知公告；预置 13 类 57 条业务字典（供品种、疫苗类型等下拉使用） |

## 🛠 技术栈

- **后端**：Python 3.12 · FastAPI · SQLAlchemy 2 · MySQL · JWT + bcrypt · APScheduler
- **前端**：Vue 3 · TypeScript · Element Plus · Pinia · Vite
- **文档**：BRD / PRD / HDD / LLD / API / DBD

## 📁 项目结构

```
livestockBreedingSystem/
├── livestock_server/          # 后端（FastAPI）
│   ├── app/
│   │   ├── api/v1/            # 全局路由（auth/farm）
│   │   ├── core/              # 鉴权、异常、统一响应
│   │   ├── models/            # 全局基础模型
│   │   ├── modules/           # 业务模块（按模块分包）
│   │   │   ├── animal/        # 畜禽档案
│   │   │   ├── breeding/      # 繁育
│   │   │   ├── feeding/       # 饲喂
│   │   │   ├── health/        # 防疫诊疗
│   │   │   ├── inventory/     # 物资库存
│   │   │   ├── pen/           # 圈舍
│   │   │   ├── review/        # 审核中心
│   │   │   └── system/        # 系统字典
│   │   ├── schemas/           # 全局 DTO
│   │   └── services/          # 全局服务
│   ├── tests/                 # 后端 pytest 回归测试（SQLite 内存库，不连开发/生产库）
│   │   ├── conftest.py        # 夹具：内存库 + TestClient + 依赖覆盖
│   │   ├── test_farm_context.py        # 超管农场上下文 / 租户隔离
│   │   ├── test_inventory_audit.py     # 库存审核原子性（顺序语义）
│   │   ├── test_feeding_cost_allocation.py  # 单只饲料成本分摊
│   │   ├── test_smoke.py               # 端到端冒烟链路
│   │   └── test_concurrency_mysql.py   # MySQL 真并发（需 TEST_MYSQL_URL，默认跳过）
│   ├── requirements.txt
│   ├── requirements-dev.txt   # 测试依赖（pytest / httpx）
│   ├── pytest.ini
│   └── seed_data.py           # 测试数据脚本
├── livestock-web/             # 前端（Vue3）
│   ├── src/
│   │   ├── api/               # 接口封装
│   │   ├── views/             # 页面
│   │   ├── router/            # 路由
│   │   └── stores/            # Pinia 状态
│   └── package.json
└── docs/                      # 设计文档
```

每个业务模块采用固定分层：`model.py`（ORM）→ `schema.py`（DTO）→ `service.py`（业务逻辑）→ `api.py`（路由）。

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 5.7+ / 8.0

### 1. 启动后端

```bash
cd livestock_server

# 安装依赖
pip install -r requirements.txt

# 配置数据库：复制 .env.example 为 .env，填入你的 MySQL 账号密码
cp .env.example .env

# 创建数据库
mysql -uroot -p -e "CREATE DATABASE IF NOT EXISTS livestock_db DEFAULT CHARSET utf8mb4;"

# 启动（首次启动自动建表 + 初始化超管 admin/admin123）
python -m uvicorn app.main:app --reload --port 8000
```

启动后访问接口文档：http://127.0.0.1:8000/docs

### 2. 启动前端

```bash
cd livestock-web

npm install
npm run dev
```

访问 http://localhost:5173 （前端通过 `.env.development` 的 `VITE_API_BASE=/api/v1` 走 Vite 开发代理转发到后端 `http://127.0.0.1:8000`；后端地址不同则改 `vite.config.ts` 的 `server.proxy.target`）

### 3. 测试数据（可选）

```bash
cd livestock_server
python seed_data.py            # 基础测试数据（会清空动物档案后重建）
python init_sunshine_data.py   # 阳光牧场完整演示数据（清库重建）
python seed_missing_tables.py  # 仅补齐空表：公畜档案/公告/站内消息/档案历史（不清库，可重复执行）
```

## 🧪 测试

### 后端回归测试（推荐先跑这个）

用 SQLite 内存库运行，**不连接开发/生产数据库**，可重复执行：

```bash
cd livestock_server
pip install -r requirements.txt -r requirements-dev.txt

python -m pytest tests/ -v        # 全量回归：农场上下文 / 库存审核 / 成本分摊 / 冒烟链路
python quick_test.py              # 快速冒烟（= pytest tests/test_smoke.py）
```

覆盖范围：超管农场上下文与租户隔离、库存审核的原子性与重复审核、单只饲料成本分摊、
入栏/圈舍/饲喂/审核/库存/出栏销售端到端链路。失败用例返回非零退出码，可直接接入 CI。

**并发测试（需自备 MySQL 测试库）**：SQLite 无法代表生产数据库的并发语义，
真并发用例单独放在 `tests/test_concurrency_mysql.py`，默认跳过；指定专用测试库后运行
（严禁指向开发/生产库，该库会被反复建表清理）：

```bash
cd livestock_server
TEST_MYSQL_URL="mysql+pymysql://root:密码@127.0.0.1:3306/livestock_test?charset=utf8mb4" \
  python -m pytest tests/test_concurrency_mysql.py -v
```

### 前端测试

```bash
cd livestock-web
npm test          # Vitest 单元测试
npm run build     # vue-tsc 类型检查 + 生产构建
```

## 👤 默认账号

| 角色 | 账号 | 密码 | 说明 |
| --- | --- | --- | --- |
| 超级管理员 | admin | admin123 | 后端启动时自动初始化 |
| 养殖场主 | 注册或 seed 脚本生成 | - | 登录后管理本场 |

## 📚 文档

- [使用说明书](docs/使用说明书.md) —— 安装部署 + 逐模块操作说明 + 业务规则 + 常见问题
- [技术详解（小白版）](docs/技术详解.md) —— 每个功能背后用了什么技术，面向零基础讲解
- [API 接口文档](docs/API-智能养殖信息管理系统.md) —— 接口字段、错误码、请求头约定（运行时另有 `/docs` 自动生成）
- [数据库迁移指南](docs/migrations.md) —— Alembic 日常流程与环境接入

## 📄 License

仅供学习交流使用。
