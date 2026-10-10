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
│   ├── requirements.txt
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

## 👤 默认账号

| 角色 | 账号 | 密码 | 说明 |
| --- | --- | --- | --- |
| 超级管理员 | admin | admin123 | 后端启动时自动初始化 |
| 养殖场主 | 注册或 seed 脚本生成 | - | 登录后管理本场 |

## 📚 文档

- [使用说明书](docs/使用说明书.md) —— 安装部署 + 逐模块操作说明 + 业务规则 + 常见问题
- [技术详解（小白版）](docs/技术详解.md) —— 每个功能背后用了什么技术，面向零基础讲解
- 设计文档：BRD / PRD / HDD / LLD / [API](docs/API-智能养殖信息管理系统.md) / [DBD](docs/DBD-智能养殖信息管理系统.md)

## 📄 License

仅供学习交流使用。
