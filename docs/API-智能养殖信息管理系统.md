# 智能养殖信息管理系统 API 接口文档

## 1. 文档信息

| 项目 | 内容 |
| --- | --- |
| 项目名称 | 智能养殖信息管理系统 |
| 后端项目 | livestock-server |
| 前端框架 | Vue3 |
| 接口规范 | RESTful + 统一返回格式 |
| 认证方式 | JWT / Sa-Token（Bearer Token） |
| 文档版本 | v1.0.0 |
| 作者 | 智能养殖研发组 |
| 创建日期 | 2026-08-10 |
| 适用范围 | 牛、羊、猪三种养殖种类 |

### 修订记录

| 版本 | 日期 | 修订人 | 修订内容 |
| --- | --- | --- | --- |
| v1.0.0 | 2026-08-10 | 研发组 | 首次发布，覆盖 12 个模块全部接口 |
| v1.0.1 | - | - | - |

---

## 2. 接口规范

### 2.1 基础路径

```
http://{ip}:{port}/api/v1
```

示例（本地开发）：

```
http://localhost:8080/api/v1
```

### 2.2 认证方式

系统采用 JWT / Sa-Token 进行身份认证。除登录、注册、刷新 token 等接口外，所有接口均需在请求头携带 Token：

```
Authorization: Bearer {token}
```

Token 默认有效期 2 小时，可通过 `/auth/refresh-token` 接口刷新。

### 2.3 统一返回格式

所有接口统一返回 JSON 格式，结构如下：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {},
  "timestamp": 1691616000000
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| code | int | 业务状态码，200 表示成功，其他表示业务错误 |
| msg | string | 提示信息 |
| data | object/array/null | 业务数据 |
| timestamp | long | 服务器时间戳（毫秒） |

### 2.4 分页请求参数

分页接口统一使用以下查询参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| pageNum | int | 否 | 1 | 当前页码，从 1 开始 |
| pageSize | int | 否 | 10 | 每页条数 |

### 2.5 分页响应格式

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [],
    "total": 100,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| list | array | 当前页数据列表 |
| total | long | 总记录数 |
| pageNum | int | 当前页码 |
| pageSize | int | 每页条数 |

### 2.6 HTTP 状态码说明

| HTTP 状态码 | 说明 |
| --- | --- |
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或 Token 失效 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 405 | 请求方法不允许 |
| 415 | 不支持的媒体类型 |
| 500 | 服务器内部错误 |
| 502 | 网关错误 |
| 503 | 服务不可用 |

### 2.7 业务错误码说明

错误码采用 5 位数字分段编码，各业务模块分配如下：

| 错误码段 | 模块 | 说明 |
| --- | --- | --- |
| 10000-10999 | 系统通用 | 系统级错误 |
| 20000-20999 | 用户/认证 | 登录、注册、权限相关 |
| 30000-30999 | 档案 | 畜禽档案相关 |
| 40000-40999 | 圈舍 | 圈舍管理相关 |
| 50000-50999 | 饲喂 | 饲喂方案和记录 |
| 60000-60999 | 繁育 | 配种、产犊、预警 |
| 70000-70999 | 防疫诊疗 | 防疫和诊疗记录 |
| 80000-80999 | 物资 | 库存、进货、领用 |
| 90000-90999 | 销售财务 | 销售、成本、利润 |

### 2.8 通用请求头

| 请求头 | 是否必填 | 说明 |
| --- | --- | --- |
| Authorization | 是（除登录注册外） | 认证 Token，格式：`Bearer {token}` |
| Content-Type | 是 | `application/json;charset=UTF-8` |
| X-Tenant-Id | 否 | 租户标识，由系统自动从 Token 解析注入 farm_id |
| Accept-Language | 否 | 语言标识，默认 `zh-CN` |

---

## 3. 接口清单

### 3.1 认证模块 auth

| 接口名称 | Method | URL | 鉴权 |
| --- | --- | --- | --- |
| 登录 | POST | /auth/login | 否 |
| 养殖场主注册 | POST | /auth/register/owner | 否 |
| 登出 | POST | /auth/logout | 是 |
| 获取当前用户信息 | GET | /auth/userinfo | 是 |
| 刷新 Token | POST | /auth/refresh-token | 是 |

### 3.2 养殖场模块 farm

| 接口名称 | Method | URL | 鉴权 |
| --- | --- | --- | --- |
| 获取养殖场信息 | GET | /farm/info | 是 |
| 更新养殖场信息 | PUT | /farm/update | 是 |
| 员工列表 | GET | /farm/employees | 是 |
| 添加员工 | POST | /farm/employees | 是 |
| 修改员工 | PUT | /farm/employees/{id} | 是 |
| 删除员工 | DELETE | /farm/employees/{id} | 是 |
| 获取薪资配置 | GET | /farm/salary-config | 是 |
| 更新薪资配置 | PUT | /farm/salary-config | 是 |

### 3.3 圈舍模块 pen

| 接口名称 | Method | URL | 鉴权 |
| --- | --- | --- | --- |
| 圈舍列表 | GET | /pen/list | 是 |
| 圈舍详情 | GET | /pen/{id} | 是 |
| 添加圈舍 | POST | /pen/add | 是 |
| 修改圈舍 | PUT | /pen/update | 是 |
| 删除圈舍 | DELETE | /pen/{id} | 是 |
| 查看圈舍内畜禽 | GET | /pen/{id}/animals | 是 |
| 自动分配圈舍预览 | POST | /pen/auto-allocate | 是 |

### 3.4 档案模块 animal

| 接口名称 | Method | URL | 鉴权 |
| --- | --- | --- | --- |
| 档案列表 | GET | /animal/list | 是 |
| 档案详情 | GET | /animal/{id} | 是 |
| 个体入栏 | POST | /animal/individual | 是 |
| 批量入栏 | POST | /animal/batch | 是 |
| 批量删除 | POST | /animal/batch/batch-delete | 是 |
| 修改档案 | PUT | /animal/update/{id} | 是 |
| 历史记录列表 | GET | /animal/history | 是 |
| 恢复档案 | POST | /animal/history/{id}/restore | 是 |
| 生成耳标 | GET | /animal/ear-tag/generate | 是 |

### 3.5 饲喂模块 feeding

| 接口名称 | Method | URL | 鉴权 |
| --- | --- | --- | --- |
| 饲喂方案列表 | GET | /feeding/plan/list | 是 |
| 新增方案 | POST | /feeding/plan/add | 是 |
| 修改方案 | PUT | /feeding/plan/update | 是 |
| 删除方案 | DELETE | /feeding/plan/{id} | 是 |
| 饲喂记录列表 | GET | /feeding/record/list | 是 |
| 员工提交饲喂记录 | POST | /feeding/record/submit | 是 |
| 批量提交 | POST | /feeding/record/batch-submit | 是 |
| 修改饲喂记录 | PUT | /feeding/record/update/{id} | 是 |

### 3.6 繁育模块 breeding

| 接口名称 | Method | URL | 鉴权 |
| --- | --- | --- | --- |
| 母畜档案列表 | GET | /breeding/females | 是 |
| 公畜档案列表 | GET | /breeding/males | 是 |
| 设置母畜生理状态 | PUT | /breeding/females/{耳标}/physio-status | 是 |
| 配种记录列表 | GET | /breeding/mating/list | 是 |
| 新增配种记录 | POST | /breeding/mating/add | 是 |
| 修改配种记录 | PUT | /breeding/mating/update/{id} | 是 |
| 产犊记录列表 | GET | /breeding/birth/list | 是 |
| 新增产犊记录 | POST | /breeding/birth/add | 是 |
| 繁育预警列表 | GET | /breeding/alert/list | 是 |
| 处理预警 | PUT | /breeding/alert/handle/{id} | 是 |

### 3.7 防疫诊疗模块 health

| 接口名称 | Method | URL | 鉴权 |
| --- | --- | --- | --- |
| 防疫记录列表 | GET | /health/vaccine/list | 是 |
| 新增防疫记录 | POST | /health/vaccine/add | 是 |
| 批量新增防疫记录 | POST | /health/vaccine/batch-add | 是 |
| 修改防疫记录 | PUT | /health/vaccine/update/{id} | 是 |
| 诊疗记录列表 | GET | /health/medical/list | 是 |
| 新增诊疗记录 | POST | /health/medical/add | 是 |
| 修改诊疗记录 | PUT | /health/medical/update/{id} | 是 |

### 3.8 物资模块 inventory

| 接口名称 | Method | URL | 鉴权 |
| --- | --- | --- | --- |
| 库存列表 | GET | /inventory/stock/list | 是 |
| 库存详情 | GET | /inventory/stock/{id} | 是 |
| 进货记录列表 | GET | /inventory/purchase/list | 是 |
| 新增进货记录 | POST | /inventory/purchase/add | 是 |
| 领用记录列表 | GET | /inventory/consume/list | 是 |
| 新增领用记录 | POST | /inventory/consume/add | 是 |

### 3.9 销售财务模块 finance

| 接口名称 | Method | URL | 鉴权 |
| --- | --- | --- | --- |
| 薪资记录列表 | GET | /finance/salary/list | 是 |
| 核算薪资 | POST | /finance/salary/calculate | 是 |
| 修改薪资 | PUT | /finance/salary/update/{id} | 是 |
| 待出栏畜禽列表 | GET | /finance/sale/ready | 是 |
| 出栏销售 | POST | /finance/sale/out | 是 |
| 销售订单列表 | GET | /finance/sale/order/list | 是 |
| 销售订单详情 | GET | /finance/sale/order/{id} | 是 |
| 结算订单 | PUT | /finance/sale/order/settle/{id} | 是 |
| 成本支出列表 | GET | /finance/cost/list | 是 |
| 新增成本支出 | POST | /finance/cost/add | 是 |
| 单只利润核算 | GET | /finance/profit/single/{earTag} | 是 |
| 利润汇总 | GET | /finance/profit/summary | 是 |

### 3.10 统计模块 statistics

| 接口名称 | Method | URL | 鉴权 |
| --- | --- | --- | --- |
| 综合大屏数据 | GET | /statistics/dashboard | 是 |
| 存栏繁育统计 | GET | /statistics/breeding | 是 |
| 防疫诊疗统计 | GET | /statistics/health | 是 |
| 物资消耗统计 | GET | /statistics/material | 是 |
| 财务统计 | GET | /statistics/finance | 是 |

### 3.11 审核模块 review

| 接口名称 | Method | URL | 鉴权 |
| --- | --- | --- | --- |
| 待审核列表 | GET | /review/pending/list | 是 |
| 全部审核记录 | GET | /review/list | 是 |
| 审批操作 | PUT | /review/audit/{id} | 是 |

### 3.12 系统模块 system

| 接口名称 | Method | URL | 鉴权 |
| --- | --- | --- | --- |
| 用户列表 | GET | /system/user/list | 是 |
| 角色列表 | GET | /system/role/list | 是 |
| 菜单列表 | GET | /system/menu/list | 是 |
| 字典类型列表 | GET | /system/dict/type/list | 是 |
| 字典数据列表 | GET | /system/dict/data/list | 是 |
| 操作日志 | GET | /system/oper-log/list | 是 |
| 登录日志 | GET | /system/login-log/list | 是 |
| 通知列表 | GET | /system/notice/list | 是 |

---

## 4. 各模块接口详细说明

### 4.1 认证模块 auth

#### 4.1.1 登录

- **接口名称**：登录
- **Method**：POST
- **URL**：`/auth/login`
- **请求头**：Content-Type: application/json
- **鉴权**：否
- **请求体示例**：

```json
{
  "phone": "13800138000",
  "password": "123456"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| phone | string | 是 | 手机号 |
| password | string | 是 | 密码（明文传输由前端加密） |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiw...",
    "refreshToken": "dGhpcyBpcyBhIHJlZnJl...",
    "expiresIn": 7200,
    "userInfo": {
      "id": 1,
      "phone": "13800138000",
      "nickname": "张三",
      "avatar": "https://example.com/avatar.png",
      "userType": "OWNER",
      "farmId": 1001,
      "roles": ["owner"],
      "permissions": ["farm:info", "animal:add"]
    }
  },
  "timestamp": 1691616000000
}
```

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 20001 | 手机号或密码错误 | 200 |
| 20002 | 账号已被禁用 | 200 |
| 20003 | 账号不存在 | 200 |
| 20004 | 密码错误次数过多，请稍后再试 | 200 |

- **备注**：登录成功后返回 Token 和刷新 Token，前端需保存 Token 并在后续请求中携带。

#### 4.1.2 养殖场主注册

- **接口名称**：养殖场主注册
- **Method**：POST
- **URL**：`/auth/register/owner`
- **鉴权**：否
- **请求体示例**：

```json
{
  "phone": "13800138001",
  "password": "123456",
  "nickname": "李四",
  "farmName": "阳光养殖场",
  "farmType": ["CATTLE", "SHEEP"],
  "address": "内蒙古呼和浩特市XX镇",
  "contactName": "李四",
  "contactPhone": "13800138001"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| phone | string | 是 | 手机号（作为登录账号） |
| password | string | 是 | 密码 |
| nickname | string | 是 | 昵称 |
| farmName | string | 是 | 养殖场名称 |
| farmType | array | 是 | 养殖种类，CATTLE 牛 / SHEEP 羊 / PIG 猪，可多选 |
| address | string | 否 | 养殖场地址 |
| contactName | string | 否 | 联系人姓名 |
| contactPhone | string | 否 | 联系电话 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "注册成功",
  "data": {
    "userId": 1001,
    "farmId": 1001,
    "phone": "13800138001"
  },
  "timestamp": 1691616000000
}
```

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 20005 | 手机号已被注册 | 200 |
| 20006 | 养殖场名称已存在 | 200 |
| 20007 | farmType 不能为空 | 200 |

- **备注**：系统无员工自助注册接口。员工由养殖场主在「养殖场模块 - 添加员工」（`POST /farm/employees`）创建，并按岗位（饲喂员/兽医/繁育员/库管员）分配角色。

#### 4.1.3 登出

- **接口名称**：登出
- **Method**：POST
- **URL**：`/auth/logout`
- **鉴权**：是
- **请求体示例**：无
- **响应体示例**：

```json
{
  "code": 200,
  "msg": "退出成功",
  "data": null,
  "timestamp": 1691616000000
}
```

- **备注**：登出后服务端使 Token 失效。

#### 4.1.4 获取当前用户信息

- **接口名称**：获取当前用户信息
- **Method**：GET
- **URL**：`/auth/userinfo`
- **鉴权**：是
- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "id": 1,
    "phone": "13800138000",
    "nickname": "张三",
    "realName": "张三",
    "avatar": "https://example.com/avatar.png",
    "userType": "OWNER",
    "post": null,
    "farmId": 1001,
    "farmName": "阳光养殖场",
    "roles": ["owner"],
    "permissions": ["farm:info", "animal:add"],
    "createTime": "2026-08-01 10:00:00"
  },
  "timestamp": 1691616000000
}
```

#### 4.1.5 刷新 Token

- **接口名称**：刷新 Token
- **Method**：POST
- **URL**：`/auth/refresh-token`
- **鉴权**：是
- **请求体示例**：

```json
{
  "refreshToken": "dGhpcyBpcyBhIHJlZnJl..."
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "刷新成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiw...",
    "refreshToken": "bmV3IHJlZnJlc2ggdG9rZW4...",
    "expiresIn": 7200
  },
  "timestamp": 1691616000000
}
```

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 20010 | refresh_token 无效 | 200 |
| 20011 | refresh_token 已过期 | 200 |

---

### 4.2 养殖场模块 farm

#### 4.2.1 获取养殖场信息

- **接口名称**：获取养殖场信息
- **Method**：GET
- **URL**：`/farm/info`
- **鉴权**：是
- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "id": 1001,
    "farmName": "阳光养殖场",
    "farmType": ["CATTLE", "SHEEP"],
    "address": "内蒙古呼和浩特市XX镇",
    "contactName": "李四",
    "contactPhone": "13800138001",
    "employeeCount": 15,
    "penCount": 20,
    "animalCount": 580,
    "createTime": "2026-08-01 10:00:00"
  },
  "timestamp": 1691616000000
}
```

#### 4.2.2 更新养殖场信息

- **接口名称**：更新养殖场信息
- **Method**：PUT
- **URL**：`/farm/update`
- **鉴权**：是
- **请求体示例**：

```json
{
  "farmName": "阳光养殖场（更新）",
  "address": "内蒙古呼和浩特市XX镇XX村",
  "contactName": "李四",
  "contactPhone": "13800138001"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "更新成功",
  "data": null,
  "timestamp": 1691616000000
}
```

#### 4.2.3 员工列表

- **接口名称**：员工列表
- **Method**：GET
- **URL**：`/farm/employees`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| keyword | string | 否 | 关键字（姓名/手机号） |
| post | string | 否 | 岗位类型 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1002,
        "phone": "13800138002",
        "nickname": "王五",
        "realName": "王五",
        "post": "FEEDER",
        "postName": "饲喂员",
        "gender": 1,
        "age": 30,
        "entryDate": "2026-08-01",
        "status": 1,
        "createTime": "2026-08-01 10:00:00"
      }
    ],
    "total": 15,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.2.4 添加员工

- **接口名称**：添加员工
- **Method**：POST
- **URL**：`/farm/employees`
- **鉴权**：是
- **请求体示例**：

```json
{
  "phone": "13800138003",
  "password": "123456",
  "nickname": "赵六",
  "realName": "赵六",
  "post": "VET",
  "gender": 1,
  "age": 28,
  "entryDate": "2026-08-10"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "添加成功",
  "data": {
    "id": 1003,
    "phone": "13800138003"
  },
  "timestamp": 1691616000000
}
```

#### 4.2.5 修改员工

- **接口名称**：修改员工
- **Method**：PUT
- **URL**：`/farm/employees/{id}`
- **鉴权**：是
- **路径参数**：id（员工 ID）
- **请求体示例**：

```json
{
  "nickname": "赵六（修改）",
  "post": "BREEDER",
  "gender": 1,
  "age": 28,
  "status": 1
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "修改成功",
  "data": null,
  "timestamp": 1691616000000
}
```

#### 4.2.6 删除员工

- **接口名称**：删除员工
- **Method**：DELETE
- **URL**：`/farm/employees/{id}`
- **鉴权**：是
- **路径参数**：id（员工 ID）
- **响应体示例**：

```json
{
  "code": 200,
  "msg": "删除成功",
  "data": null,
  "timestamp": 1691616000000
}
```

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 20012 | 不能删除自己 | 200 |

#### 4.2.7 获取薪资配置

- **接口名称**：获取薪资配置
- **Method**：GET
- **URL**：`/farm/salary-config`
- **鉴权**：是
- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "farmId": 1001,
    "baseSalary": {
      "FEEDER": 4000,
      "VET": 6000,
      "BREEDER": 5000,
      "KEEPER": 4500
    },
    "subsidy": {
      "FEEDING_PER_HEAD": 0.5,
      "MEDICAL_PER_CASE": 50,
      "BREEDING_PER_CASE": 30
    },
    "updateTime": "2026-08-05 10:00:00"
  },
  "timestamp": 1691616000000
}
```

#### 4.2.8 更新薪资配置

- **接口名称**：更新薪资配置
- **Method**：PUT
- **URL**：`/farm/salary-config`
- **鉴权**：是
- **请求体示例**：

```json
{
  "baseSalary": {
    "FEEDER": 4500,
    "VET": 6500,
    "BREEDER": 5500,
    "KEEPER": 5000
  },
  "subsidy": {
    "FEEDING_PER_HEAD": 0.6,
    "MEDICAL_PER_CASE": 60,
    "BREEDING_PER_CASE": 40
  }
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "更新成功",
  "data": null,
  "timestamp": 1691616000000
}
```

---

### 4.3 圈舍模块 pen

#### 4.3.1 圈舍列表

- **接口名称**：圈舍列表
- **Method**：GET
- **URL**：`/pen/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| penType | string | 否 | 圈舍类型：A/B/C/D |
| keyword | string | 否 | 圈舍名称关键字 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "penName": "A1育雏舍",
        "penCode": "A001",
        "penType": "A",
        "penTypeName": "育雏舍",
        "capacity": 100,
        "currentCount": 85,
        "animalType": "CATTLE",
        "remark": "1号育雏舍",
        "createTime": "2026-08-01 10:00:00"
      }
    ],
    "total": 20,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.3.2 圈舍详情

- **接口名称**：圈舍详情
- **Method**：GET
- **URL**：`/pen/{id}`
- **鉴权**：是
- **路径参数**：id（圈舍 ID）
- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "id": 1,
    "penName": "A1育雏舍",
    "penCode": "A001",
    "penType": "A",
    "penTypeName": "育雏舍",
    "capacity": 100,
    "currentCount": 85,
    "animalType": "CATTLE",
    "remark": "1号育雏舍",
    "createTime": "2026-08-01 10:00:00"
  },
  "timestamp": 1691616000000
}
```

#### 4.3.3 添加圈舍

- **接口名称**：添加圈舍
- **Method**：POST
- **URL**：`/pen/add`
- **鉴权**：是
- **请求体示例**：

```json
{
  "penName": "B2育成舍",
  "penCode": "B002",
  "penType": "B",
  "capacity": 80,
  "animalType": "CATTLE",
  "remark": "2号育成舍"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| penName | string | 是 | 圈舍名称 |
| penCode | string | 是 | 圈舍编码 |
| penType | string | 是 | 圈舍类型：A 育雏舍 / B 育成舍 / C 繁育舍 / D 种畜圈舍 |
| capacity | int | 是 | 容量 |
| animalType | string | 是 | 养殖种类：CATTLE/SHEEP/PIG |
| remark | string | 否 | 备注 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "添加成功",
  "data": {
    "id": 21
  },
  "timestamp": 1691616000000
}
```

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 40001 | 圈舍编码已存在 | 200 |
| 40002 | 圈舍类型不合法 | 200 |

#### 4.3.4 修改圈舍

- **接口名称**：修改圈舍
- **Method**：PUT
- **URL**：`/pen/update`
- **鉴权**：是
- **请求体示例**：

```json
{
  "id": 21,
  "penName": "B2育成舍（修改）",
  "capacity": 90,
  "remark": "2号育成舍修改后"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "修改成功",
  "data": null,
  "timestamp": 1691616000000
}
```

#### 4.3.5 删除圈舍

- **接口名称**：删除圈舍
- **Method**：DELETE
- **URL**：`/pen/{id}`
- **鉴权**：是
- **路径参数**：id（圈舍 ID）
- **响应体示例**：

```json
{
  "code": 200,
  "msg": "删除成功",
  "data": null,
  "timestamp": 1691616000000
}
```

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 40003 | 圈舍内仍有畜禽，无法删除 | 200 |

#### 4.3.6 查看圈舍内畜禽

- **接口名称**：查看圈舍内畜禽
- **Method**：GET
- **URL**：`/pen/{id}/animals`
- **鉴权**：是
- **路径参数**：id（圈舍 ID）
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 5001,
        "earTag": "0101",
        "penId": 1,
        "penName": "A1育雏舍",
        "gender": 1,
        "breed": "西门塔尔牛",
        "birthDate": "2026-06-01",
        "entryDate": "2026-06-15",
        "ageDays": 70,
        "growthStage": "犊牛期",
        "growthStageName": "犊牛期",
        "status": "在栏"
      }
    ],
    "total": 85,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.3.7 自动分配圈舍预览

- **接口名称**：自动分配圈舍预览
- **Method**：POST
- **URL**：`/pen/auto-allocate`
- **鉴权**：是
- **请求体示例**：

```json
{
  "animalType": "CATTLE",
  "growthStage": "犊牛期",
  "count": 20
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| animalType | string | 是 | 养殖种类 |
| growthStage | string | 是 | 生长阶段（见枚举表） |
| count | int | 是 | 待分配数量 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "allocations": [
      {
        "penId": 1,
        "penName": "A1育雏舍",
        "penType": "A",
        "capacity": 100,
        "currentCount": 85,
        "allocateCount": 15,
        "availableCapacity": 15
      },
      {
        "penId": 2,
        "penName": "A2育雏舍",
        "penType": "A",
        "capacity": 100,
        "currentCount": 90,
        "allocateCount": 5,
        "availableCapacity": 10
      }
    ],
    "totalAllocated": 20,
    "totalRequested": 20,
    "feasible": true
  },
  "timestamp": 1691616000000
}
```

- **备注**：分配算法按圈舍类型与生长阶段对应（如犊牛分配至 A 育雏舍），并优先填满已有圈舍。

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 40004 | 无可用圈舍 | 200 |
| 40005 | 圈舍容量不足 | 200 |

---

### 4.4 档案模块 animal

#### 4.4.1 档案列表

- **接口名称**：档案列表
- **Method**：GET
- **URL**：`/animal/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| earTag | string | 否 | 耳标 |
| penId | long | 否 | 圈舍 ID |
| breed | string | 否 | 品种 |
| gender | int | 否 | 性别：0 母 / 1 公 |
| status | string | 否 | 状态：在栏/种用/隔离/待出栏/已出栏/死亡 |
| entryDateStart | string | 否 | 入栏开始日期 |
| entryDateEnd | string | 否 | 入栏结束日期 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 5001,
        "earTag": "0101",
        "penId": 1,
        "penName": "A1育雏舍",
        "animalType": "CATTLE",
        "gender": 1,
        "breed": "西门塔尔牛",
        "birthDate": "2026-06-01",
        "entryDate": "2026-06-15",
        "entryWeight": 50.0,
        "currentWeight": 95.0,
        "ageDays": 70,
        "growthStage": "犊牛期",
        "growthStageName": "犊牛期",
        "status": "在栏",
        "statusName": "在栏",
        "remark": "健康",
        "createTime": "2026-06-15 10:00:00"
      }
    ],
    "total": 580,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.4.2 档案详情

- **接口名称**：档案详情
- **Method**：GET
- **URL**：`/animal/{id}`
- **鉴权**：是
- **路径参数**：id（档案 ID）
- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "id": 5001,
    "earTag": "0101",
    "penId": 1,
    "penName": "A1育雏舍",
    "animalType": "CATTLE",
    "gender": 1,
    "breed": "西门塔尔牛",
    "birthDate": "2026-06-01",
    "entryDate": "2026-06-15",
    "entryWeight": 50.0,
    "currentWeight": 95.0,
    "ageDays": 70,
    "growthStage": "犊牛期",
    "growthStageName": "犊牛期",
    "status": "在栏",
    "statusName": "在栏",
    "remark": "健康",
    "createTime": "2026-06-15 10:00:00",
    "feedingRecords": 30,
    "vaccineRecords": 2,
    "medicalRecords": 0
  },
  "timestamp": 1691616000000
}
```

#### 4.4.3 个体入栏

- **接口名称**：个体入栏
- **Method**：POST
- **URL**：`/animal/individual`
- **鉴权**：是
- **请求体示例**：

```json
{
  "animalType": "CATTLE",
  "penId": 1,
  "earTag": "0102",
  "gender": 1,
  "breed": "西门塔尔牛",
  "birthDate": "2026-06-01",
  "entryDate": "2026-08-10",
  "entryWeight": 95.0,
  "source": "自繁",
  "remark": "健康"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| animalType | string | 是 | 养殖种类 |
| penId | long | 是 | 圈舍 ID |
| earTag | string | 是 | 耳标 |
| gender | int | 是 | 性别 |
| breed | string | 否 | 品种 |
| birthDate | string | 是 | 出生日期 |
| entryDate | string | 是 | 入栏日期 |
| entryWeight | double | 否 | 入栏体重 |
| source | string | 否 | 来源 |
| remark | string | 否 | 备注 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "入栏成功",
  "data": {
    "id": 5002,
    "earTag": "0102"
  },
  "timestamp": 1691616000000
}
```

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 30001 | 耳标已存在 | 200 |
| 30002 | 耳标格式不正确（4 位数字） | 200 |
| 30003 | 圈舍已满 | 200 |
| 40005 | 圈舍不存在或不属于本养殖场 | 200 |

#### 4.4.4 批量入栏

- **接口名称**：批量入栏
- **Method**：POST
- **URL**：`/animal/batch`
- **鉴权**：是
- **请求体示例**：

```json
{
  "animalType": "CATTLE",
  "growthStage": "犊牛期",
  "entryDate": "2026-08-10",
  "commonInfo": {
    "breed": "西门塔尔牛",
    "source": "外购",
    "remark": "批量入栏"
  },
  "items": [
    {
      "penId": 1,
      "earTag": "0103",
      "gender": 1,
      "birthDate": "2026-06-01",
      "entryWeight": 90.0
    },
    {
      "penId": 1,
      "earTag": "0104",
      "gender": 0,
      "birthDate": "2026-06-01",
      "entryWeight": 88.0
    }
  ]
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "批量入栏成功",
  "data": {
    "successCount": 2,
    "failCount": 0,
    "failItems": [],
    "preview": {
      "allocations": [
        {
          "penId": 1,
          "allocateCount": 2
        }
      ]
    }
  },
  "timestamp": 1691616000000
}
```

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 30004 | 批量入栏数量超过圈舍容量 | 200 |
| 30005 | 部分耳标已存在 | 200 |

#### 4.4.5 批量删除

- **接口名称**：批量删除
- **Method**：POST
- **URL**：`/animal/batch/batch-delete`
- **鉴权**：是
- **请求体示例**：

```json
{
  "ids": [5001, 5002, 5003],
  "reason": "死亡",
  "remark": "病亡处理"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| ids | array | 是 | 档案 ID 数组 |
| reason | string | 是 | 删除原因：死亡/出栏/其他 |
| remark | string | 否 | 备注 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "批量删除成功",
  "data": {
    "successCount": 3,
    "failCount": 0
  },
  "timestamp": 1691616000000
}
```

- **备注**：批量删除后将档案移入历史记录，支持后续恢复。

#### 4.4.6 修改档案

- **接口名称**：修改档案
- **Method**：PUT
- **URL**：`/animal/update/{id}`
- **鉴权**：是
- **路径参数**：id（档案 ID）
- **请求体示例**：

```json
{
  "penId": 2,
  "currentWeight": 110.0,
  "breed": "西门塔尔牛",
  "remark": "健康生长"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "修改成功",
  "data": null,
  "timestamp": 1691616000000
}
```

#### 4.4.7 历史记录列表

- **接口名称**：历史记录列表
- **Method**：GET
- **URL**：`/animal/history`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| earTag | string | 否 | 耳标 |
| reason | string | 否 | 删除原因 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 4999,
        "earTag": "0100",
        "animalType": "CATTLE",
        "gender": 1,
        "breed": "西门塔尔牛",
        "birthDate": "2026-03-01",
        "entryDate": "2026-03-15",
        "deleteTime": "2026-08-05 15:00:00",
        "deleteReason": "出栏",
        "deleteRemark": "出栏销售",
        "canRestore": true
      }
    ],
    "total": 25,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.4.8 恢复档案

- **接口名称**：恢复档案
- **Method**：POST
- **URL**：`/animal/history/{id}/restore`
- **鉴权**：是
- **路径参数**：id（历史记录 ID）
- **请求体示例**：

```json
{
  "penId": 1,
  "remark": "恢复入栏"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "恢复成功",
  "data": {
    "id": 4999,
    "earTag": "0100"
  },
  "timestamp": 1691616000000
}
```

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 30006 | 耳标已被占用，无法恢复 | 200 |
| 30007 | 历史记录不存在 | 200 |

#### 4.4.9 生成耳标

- **接口名称**：生成耳标
- **Method**：GET
- **URL**：`/animal/ear-tag/generate`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| penId | long | 是 | 圈舍 ID |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "penId": 1,
    "earTag": "0105",
    "availableEarTags": ["0105", "0106", "0107"]
  },
  "timestamp": 1691616000000
}
```

- **备注**：耳标 4 位数 = 前 2 位圈舍编号 + 后 2 位顺序号。系统会自动跳过已使用耳标，空出可重用。

---

### 4.5 饲喂模块 feeding

#### 4.5.1 饲喂方案列表

- **接口名称**：饲喂方案列表
- **Method**：GET
- **URL**：`/feeding/plan/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| animalType | string | 否 | 养殖种类 |
| growthStage | string | 否 | 生长阶段 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "planName": "犊牛标准饲喂方案",
        "animalType": "CATTLE",
        "growthStage": "犊牛期",
        "feedType": "代乳粉+精料",
        "feedAmount": 2.5,
        "unit": "kg/头/日",
        "feedTimes": 3,
        "remark": "适用于1-60日龄犊牛",
        "createTime": "2026-08-01 10:00:00"
      }
    ],
    "total": 8,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.5.2 新增方案

- **接口名称**：新增方案
- **Method**：POST
- **URL**：`/feeding/plan/add`
- **鉴权**：是
- **请求体示例**：

```json
{
  "planName": "生长牛饲喂方案",
  "animalType": "CATTLE",
  "growthStage": "生长期",
  "feedType": "青贮+精料",
  "feedAmount": 5.0,
  "unit": "kg/头/日",
  "feedTimes": 2,
  "remark": "适用于181-365日龄生长牛"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "新增成功",
  "data": {
    "id": 9
  },
  "timestamp": 1691616000000
}
```

#### 4.5.3 修改方案

- **接口名称**：修改方案
- **Method**：PUT
- **URL**：`/feeding/plan/update`
- **鉴权**：是
- **请求体示例**：

```json
{
  "id": 9,
  "planName": "生长牛饲喂方案（修改）",
  "feedAmount": 5.5,
  "remark": "调整后适用于181-365日龄生长牛"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "修改成功",
  "data": null,
  "timestamp": 1691616000000
}
```

#### 4.5.4 删除方案

- **接口名称**：删除方案
- **Method**：DELETE
- **URL**：`/feeding/plan/{id}`
- **鉴权**：是
- **路径参数**：id（方案 ID）
- **响应体示例**：

```json
{
  "code": 200,
  "msg": "删除成功",
  "data": null,
  "timestamp": 1691616000000
}
```

#### 4.5.5 饲喂记录列表

- **接口名称**：饲喂记录列表
- **Method**：GET
- **URL**：`/feeding/record/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| penId | long | 否 | 圈舍 ID |
| feedDateStart | string | 否 | 饲喂开始日期 |
| feedDateEnd | string | 否 | 饲喂结束日期 |
| status | string | 否 | 状态：PENDING 待审核 / APPROVED 已通过 / REJECTED 已驳回 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "penId": 1,
        "penName": "A1育雏舍",
        "planId": 1,
        "planName": "犊牛标准饲喂方案",
        "feedDate": "2026-08-10",
        "feedAmount": 212.5,
        "unit": "kg",
        "feedCount": 85,
        "feederId": 1002,
        "feederName": "王五",
        "status": "PENDING",
        "statusName": "待审核",
        "remark": "正常饲喂",
        "createTime": "2026-08-10 08:00:00"
      }
    ],
    "total": 60,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.5.6 员工提交饲喂记录

- **接口名称**：员工提交饲喂记录
- **Method**：POST
- **URL**：`/feeding/record/submit`
- **鉴权**：是
- **请求体示例**：

```json
{
  "penId": 1,
  "planId": 1,
  "feedDate": "2026-08-10",
  "feedAmount": 212.5,
  "unit": "kg",
  "feedCount": 85,
  "remark": "正常饲喂"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "提交成功，等待审核",
  "data": {
    "id": 61,
    "reviewId": 1001
  },
  "timestamp": 1691616000000
}
```

- **备注**：提交后自动生成审核记录，由管理员审核。

#### 4.5.7 批量提交

- **接口名称**：批量提交
- **Method**：POST
- **URL**：`/feeding/record/batch-submit`
- **鉴权**：是
- **请求体示例**：

```json
{
  "records": [
    {
      "penId": 1,
      "planId": 1,
      "feedDate": "2026-08-10",
      "feedAmount": 212.5,
      "unit": "kg",
      "feedCount": 85,
      "remark": "正常饲喂"
    },
    {
      "penId": 2,
      "planId": 2,
      "feedDate": "2026-08-10",
      "feedAmount": 300.0,
      "unit": "kg",
      "feedCount": 100,
      "remark": "正常饲喂"
    }
  ]
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "批量提交成功",
  "data": {
    "successCount": 2,
    "failCount": 0,
    "reviewIds": [1002, 1003]
  },
  "timestamp": 1691616000000
}
```

#### 4.5.8 修改饲喂记录

- **接口名称**：修改饲喂记录
- **Method**：PUT
- **URL**：`/feeding/record/update/{id}`
- **鉴权**：是
- **路径参数**：id（记录 ID）
- **请求体示例**：

```json
{
  "feedAmount": 215.0,
  "remark": "修正饲喂数量"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "修改成功",
  "data": null,
  "timestamp": 1691616000000
}
```

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 50001 | 饲喂记录已审核，无法修改 | 200 |
| 50002 | 饲喂方案不存在 | 200 |

---

### 4.6 繁育模块 breeding

#### 4.6.1 母畜档案列表

- **接口名称**：母畜档案列表
- **Method**：GET
- **URL**：`/breeding/females`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| animalType | string | 否 | 养殖种类 |
| breed | string | 否 | 品种 |
| physio_status | string | 否 | 母畜生理状态：发情/妊娠/泌乳/休情/淘汰 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 5002,
        "earTag": "0102",
        "animalType": "CATTLE",
        "breed": "西门塔尔牛",
        "birthDate": "2025-01-01",
        "ageDays": 586,
        "growthStage": "繁育期",
        "growthStageName": "繁育期",
        "physio_status": "发情",
        "lastMatingDate": null,
        "expectedBirthDate": null,
        "penId": 3,
        "penName": "C1繁育舍"
      }
    ],
    "total": 30,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.6.2 公畜档案列表

- **接口名称**：公畜档案列表
- **Method**：GET
- **URL**：`/breeding/males`
- **鉴权**：是
- **查询参数**：同母畜档案列表
- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 5100,
        "earTag": "0301",
        "animalType": "CATTLE",
        "breed": "西门塔尔牛",
        "birthDate": "2024-06-01",
        "ageDays": 800,
        "growthStage": "繁育期",
        "growthStageName": "繁育期",
        "matingCount": 15,
        "penId": 4,
        "penName": "D1种畜圈舍"
      }
    ],
    "total": 5,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.6.3 设置母畜生理状态

- **接口名称**：设置母畜生理状态
- **Method**：PUT
- **URL**：`/breeding/females/{耳标}/physio-status`
- **鉴权**：是
- **路径参数**：耳标（母畜耳标）
- **请求体示例**：

```json
{
  "physio_status": "妊娠"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| physio_status | string | 是 | 母畜生理状态：发情/妊娠/泌乳/休情/淘汰 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "生理状态已更新",
  "data": {
    "id": 5002,
    "earTag": "0102",
    "physio_status": "妊娠"
  },
  "timestamp": 1691616000000
}
```

- **备注**：配种后母畜自动置为「妊娠」；孕检阴性后自动恢复「发情」；产犊后自动置为「泌乳」。也可通过本接口手动调整。

#### 4.6.4 配种记录列表

- **接口名称**：配种记录列表
- **Method**：GET
- **URL**：`/breeding/mating/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| femaleEarTag | string | 否 | 母畜耳标 |
| maleEarTag | string | 否 | 公畜耳标 |
| matingDateStart | string | 否 | 配种开始日期 |
| matingDateEnd | string | 否 | 配种结束日期 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "femaleId": 5002,
        "femaleEarTag": "0102",
        "maleId": 5100,
        "maleEarTag": "0301",
        "animalType": "CATTLE",
        "matingDate": "2026-08-01",
        "matingMethod": "ARTIFICIAL",
        "matingMethodName": "人工授精",
        "expectedBirthDate": "2027-04-28",
        "pregnancyCheckDate": null,
        "pregnancyStatus": "UNCHECKED",
        "pregnancyStatusName": "未孕检",
        "operator": "赵六",
        "remark": "首次配种"
      }
    ],
    "total": 12,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.6.5 新增配种记录

- **接口名称**：新增配种记录
- **Method**：POST
- **URL**：`/breeding/mating/add`
- **鉴权**：是
- **请求体示例**：

```json
{
  "femaleId": 5002,
  "maleId": 5100,
  "animalType": "CATTLE",
  "matingDate": "2026-08-01",
  "matingMethod": "ARTIFICIAL",
  "operator": "赵六",
  "remark": "首次配种"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| femaleId | long | 是 | 母畜 ID |
| maleId | long | 否 | 公畜 ID（人工授精可不填） |
| animalType | string | 是 | 养殖种类 |
| matingDate | string | 是 | 配种日期 |
| matingMethod | string | 是 | 配种方式：NATURE 自然 / ARTIFICIAL 人工授精 |
| operator | string | 否 | 操作员 |
| remark | string | 否 | 备注 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "新增成功",
  "data": {
    "id": 13,
    "expectedBirthDate": "2027-04-28"
  },
  "timestamp": 1691616000000
}
```

- **备注**：系统根据养殖种类自动计算预计生产日期（牛 280 天、羊 150 天、猪 114 天）。

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 60001 | 母畜未达到可繁育日龄 | 200 |
| 60002 | 母畜正在妊娠中，不可重复配种 | 200 |
| 60003 | 母畜或公畜不存在 | 200 |

#### 4.6.6 修改配种记录

- **接口名称**：修改配种记录
- **Method**：PUT
- **URL**：`/breeding/mating/update/{id}`
- **鉴权**：是
- **路径参数**：id（配种记录 ID）
- **请求体示例**：

```json
{
  "matingDate": "2026-08-02",
  "matingMethod": "NATURE",
  "remark": "修改为自然配种"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "修改成功",
  "data": {
    "expectedBirthDate": "2027-04-29"
  },
  "timestamp": 1691616000000
}
```

#### 4.6.7 产犊记录列表

- **接口名称**：产犊记录列表
- **Method**：GET
- **URL**：`/breeding/birth/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| femaleEarTag | string | 否 | 母畜耳标 |
| birthDateStart | string | 否 | 生产开始日期 |
| birthDateEnd | string | 否 | 生产结束日期 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "matingId": 1,
        "femaleId": 5002,
        "femaleEarTag": "0102",
        "birthDate": "2027-04-28",
        "birthCount": 1,
        "survivalCount": 1,
        "birthType": "NORMAL",
        "birthTypeName": "顺产",
        "offspringEarTags": ["0302"],
        "remark": "顺产，母子平安",
        "operator": "赵六"
      }
    ],
    "total": 8,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.6.8 新增产犊记录

- **接口名称**：新增产犊记录
- **Method**：POST
- **URL**：`/breeding/birth/add`
- **鉴权**：是
- **请求体示例**：

```json
{
  "matingId": 1,
  "femaleId": 5002,
  "birthDate": "2027-04-28",
  "birthCount": 1,
  "survivalCount": 1,
  "birthType": "NORMAL",
  "offspringEarTags": ["0302"],
  "remark": "顺产，母子平安",
  "operator": "赵六"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| matingId | long | 是 | 关联配种记录 ID |
| femaleId | long | 是 | 母畜 ID |
| birthDate | string | 是 | 生产日期 |
| birthCount | int | 是 | 产仔数 |
| survivalCount | int | 是 | 存活数 |
| birthType | string | 是 | 生产类型：NORMAL 顺产 / DIFFICULT 难产 / CESAREAN 剖腹产 |
| offspringEarTags | array | 否 | 后代耳标列表 |
| remark | string | 否 | 备注 |
| operator | string | 否 | 操作员 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "新增成功",
  "data": {
    "id": 9
  },
  "timestamp": 1691616000000
}
```

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 60004 | 配种记录不存在 | 200 |
| 60005 | 母畜未到生产日期 | 200 |

#### 4.6.9 繁育预警列表

- **接口名称**：繁育预警列表
- **Method**：GET
- **URL**：`/breeding/alert/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| alertType | string | 否 | 预警类型 |
| status | string | 否 | 状态：PENDING 待处理 / HANDLED 已处理 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "alertType": "PREGNANCY_CHECK",
        "alertTypeName": "孕检提醒",
        "femaleId": 5002,
        "femaleEarTag": "0102",
        "matingDate": "2026-08-01",
        "alertDate": "2026-09-30",
        "content": "配种后 60 天，建议进行孕检",
        "status": "PENDING",
        "statusName": "待处理"
      },
      {
        "id": 2,
        "alertType": "PRE_BIRTH",
        "alertTypeName": "临产预警",
        "femaleId": 5002,
        "femaleEarTag": "0102",
        "expectedBirthDate": "2027-04-28",
        "alertDate": "2027-04-13",
        "content": "距预产期 15 天，请做好接产准备",
        "status": "PENDING",
        "statusName": "待处理"
      },
      {
        "id": 3,
        "alertType": "POST_BIRTH_ESTRUS",
        "alertTypeName": "产后发情预警",
        "femaleId": 5003,
        "femaleEarTag": "0103",
        "lastBirthDate": "2026-06-01",
        "alertDate": "2026-07-31",
        "content": "产后 60 天未发情，请关注母畜状态",
        "status": "PENDING",
        "statusName": "待处理"
      }
    ],
    "total": 5,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

- **备注**：预警类型包括：
  - `PREGNANCY_CHECK`：配种后 60 天孕检提醒
  - `PRE_BIRTH`：临产前 15 天预警
  - `POST_BIRTH_ESTRUS`：产后 60 天未发情预警

#### 4.6.10 处理预警

- **接口名称**：处理预警
- **Method**：PUT
- **URL**：`/breeding/alert/handle/{id}`
- **鉴权**：是
- **路径参数**：id（预警 ID）
- **请求体示例**：

```json
{
  "handleResult": "CONFIRMED",
  "remark": "已完成孕检，确认妊娠"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| handleResult | string | 是 | 处理结果：CONFIRMED 已确认 / IGNORED 忽略 / RECHECK 待复查 |
| remark | string | 否 | 备注 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "处理成功",
  "data": null,
  "timestamp": 1691616000000
}
```

---

### 4.7 防疫诊疗模块 health

#### 4.7.1 防疫记录列表

- **接口名称**：防疫记录列表
- **Method**：GET
- **URL**：`/health/vaccine/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| earTag | string | 否 | 耳标 |
| vaccineType | string | 否 | 疫苗类型 |
| vaccineDateStart | string | 否 | 防疫开始日期 |
| vaccineDateEnd | string | 否 | 防疫结束日期 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "earTag": "0101",
        "animalType": "CATTLE",
        "vaccineType": "口蹄疫",
        "vaccineDate": "2026-08-05",
        "dose": 2.0,
        "unit": "ml",
        "operator": "赵六",
        "nextVaccineDate": "2027-02-05",
        "remark": "首次免疫"
      }
    ],
    "total": 50,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.7.2 新增防疫记录

- **接口名称**：新增防疫记录
- **Method**：POST
- **URL**：`/health/vaccine/add`
- **鉴权**：是
- **请求体示例**：

```json
{
  "earTag": "0101",
  "animalType": "CATTLE",
  "vaccineType": "口蹄疫",
  "vaccineDate": "2026-08-05",
  "dose": 2.0,
  "unit": "ml",
  "operator": "赵六",
  "nextVaccineDate": "2027-02-05",
  "remark": "首次免疫"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "新增成功",
  "data": {
    "id": 51
  },
  "timestamp": 1691616000000
}
```

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 70001 | 畜禽档案不存在 | 200 |
| 70002 | 疫苗类型不存在 | 200 |

#### 4.7.3 批量新增防疫记录

- **接口名称**：批量新增防疫记录
- **Method**：POST
- **URL**：`/health/vaccine/batch-add`
- **鉴权**：是
- **请求体示例**：

```json
{
  "earTags": ["0101", "0102", "0103"],
  "animalType": "CATTLE",
  "vaccineType": "口蹄疫",
  "vaccineDate": "2026-08-05",
  "dose": 2.0,
  "unit": "ml",
  "operator": "赵六",
  "nextVaccineDate": "2027-02-05",
  "remark": "整圈防疫"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "批量新增成功",
  "data": {
    "successCount": 3,
    "failCount": 0,
    "failEarTags": []
  },
  "timestamp": 1691616000000
}
```

#### 4.7.4 修改防疫记录

- **接口名称**：修改防疫记录
- **Method**：PUT
- **URL**：`/health/vaccine/update/{id}`
- **鉴权**：是
- **路径参数**：id（防疫记录 ID）
- **请求体示例**：

```json
{
  "vaccineType": "口蹄疫（O型）",
  "dose": 2.5,
  "remark": "修正剂量"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "修改成功",
  "data": null,
  "timestamp": 1691616000000
}
```

#### 4.7.5 诊疗记录列表

- **接口名称**：诊疗记录列表
- **Method**：GET
- **URL**：`/health/medical/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| earTag | string | 否 | 耳标 |
| diagnoseDateStart | string | 否 | 诊疗开始日期 |
| diagnoseDateEnd | string | 否 | 诊疗结束日期 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "earTag": "0101",
        "animalType": "CATTLE",
        "diagnoseDate": "2026-07-20",
        "symptom": "食欲下降，体温升高",
        "diagnosis": "感冒",
        "treatment": "注射抗生素，补充维生素",
        "medicine": "青霉素+维生素C",
        "cost": 50.0,
        "vetId": 1003,
        "vetName": "赵六",
        "remark": "5天后痊愈"
      }
    ],
    "total": 20,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.7.6 新增诊疗记录

- **接口名称**：新增诊疗记录
- **Method**：POST
- **URL**：`/health/medical/add`
- **鉴权**：是
- **请求体示例**：

```json
{
  "earTag": "0101",
  "animalType": "CATTLE",
  "diagnoseDate": "2026-07-20",
  "symptom": "食欲下降，体温升高",
  "diagnosis": "感冒",
  "treatment": "注射抗生素，补充维生素",
  "medicine": "青霉素+维生素C",
  "cost": 50.0,
  "remark": "5天后痊愈"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "新增成功",
  "data": {
    "id": 21
  },
  "timestamp": 1691616000000
}
```

#### 4.7.7 修改诊疗记录

- **接口名称**：修改诊疗记录
- **Method**：PUT
- **URL**：`/health/medical/update/{id}`
- **鉴权**：是
- **路径参数**：id（诊疗记录 ID）
- **请求体示例**：

```json
{
  "diagnosis": "感冒（修正）",
  "cost": 55.0,
  "remark": "修正诊断和费用"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "修改成功",
  "data": null,
  "timestamp": 1691616000000
}
```

---

### 4.8 物资模块 inventory

#### 4.8.1 库存列表

- **接口名称**：库存列表
- **Method**：GET
- **URL**：`/inventory/stock/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| materialType | string | 否 | 物资类型：FEED 饲料 / VACCINE 疫苗 / MEDICINE 药品 / OTHER 其他 |
| keyword | string | 否 | 物资名称关键字 |
| status | string | 否 | 状态：NORMAL 正常 / EXPIRED 过期 / LOW_STOCK 低库存 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "materialName": "代乳粉",
        "materialType": "FEED",
        "materialTypeName": "饲料",
        "specification": "25kg/袋",
        "unit": "袋",
        "quantity": 100,
        "warningValue": 20,
        "unitPrice": 200.0,
        "totalValue": 20000.0,
        "productionDate": "2026-07-01",
        "expiryDate": "2026-12-01",
        "status": "NORMAL",
        "statusName": "正常",
        "warehouse": "1号库房"
      }
    ],
    "total": 30,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.8.2 库存详情

- **接口名称**：库存详情
- **Method**：GET
- **URL**：`/inventory/stock/{id}`
- **鉴权**：是
- **路径参数**：id（库存 ID）
- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "id": 1,
    "materialName": "代乳粉",
    "materialType": "FEED",
    "materialTypeName": "饲料",
    "specification": "25kg/袋",
    "unit": "袋",
    "quantity": 100,
    "warningValue": 20,
    "unitPrice": 200.0,
    "totalValue": 20000.0,
    "productionDate": "2026-07-01",
    "expiryDate": "2026-12-01",
    "status": "NORMAL",
    "statusName": "正常",
    "warehouse": "1号库房",
    "purchaseCount": 5,
    "consumeCount": 2
  },
  "timestamp": 1691616000000
}
```

#### 4.8.3 进货记录列表

- **接口名称**：进货记录列表
- **Method**：GET
- **URL**：`/inventory/purchase/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| materialType | string | 否 | 物资类型 |
| purchaseDateStart | string | 否 | 进货开始日期 |
| purchaseDateEnd | string | 否 | 进货结束日期 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "stockId": 1,
        "materialName": "代乳粉",
        "materialType": "FEED",
        "specification": "25kg/袋",
        "quantity": 50,
        "unit": "袋",
        "unitPrice": 200.0,
        "totalPrice": 10000.0,
        "supplier": "XX饲料厂",
        "purchaseDate": "2026-07-01",
        "productionDate": "2026-07-01",
        "expiryDate": "2026-12-01",
        "operator": "库管员",
        "remark": "正常进货"
      }
    ],
    "total": 10,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.8.4 新增进货记录

- **接口名称**：新增进货记录
- **Method**：POST
- **URL**：`/inventory/purchase/add`
- **鉴权**：是
- **请求体示例**：

```json
{
  "stockId": 1,
  "quantity": 50,
  "unitPrice": 200.0,
  "supplier": "XX饲料厂",
  "purchaseDate": "2026-07-01",
  "productionDate": "2026-07-01",
  "expiryDate": "2026-12-01",
  "remark": "正常进货"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| stockId | long | 是 | 库存 ID（若物资不存在则先创建） |
| quantity | int | 是 | 进货数量 |
| unitPrice | double | 是 | 单价 |
| supplier | string | 否 | 供应商 |
| purchaseDate | string | 是 | 进货日期 |
| productionDate | string | 否 | 生产日期 |
| expiryDate | string | 否 | 过期日期 |
| remark | string | 否 | 备注 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "新增成功，库存已同步更新",
  "data": {
    "id": 11,
    "currentStock": 150
  },
  "timestamp": 1691616000000
}
```

- **备注**：新增进货记录后系统自动同步增加库存数量。

#### 4.8.5 领用记录列表

- **接口名称**：领用记录列表
- **Method**：GET
- **URL**：`/inventory/consume/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| materialType | string | 否 | 物资类型 |
| consumeDateStart | string | 否 | 领用开始日期 |
| consumeDateEnd | string | 否 | 领用结束日期 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "stockId": 1,
        "materialName": "代乳粉",
        "materialType": "FEED",
        "quantity": 10,
        "unit": "袋",
        "unitPrice": 200.0,
        "totalPrice": 2000.0,
        "consumeDate": "2026-08-01",
        "purpose": "饲喂犊牛",
        "receiver": "王五",
        "operator": "库管员",
        "remark": "正常领用"
      }
    ],
    "total": 8,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.8.6 新增领用记录

- **接口名称**：新增领用记录
- **Method**：POST
- **URL**：`/inventory/consume/add`
- **鉴权**：是
- **请求体示例**：

```json
{
  "stockId": 1,
  "quantity": 10,
  "consumeDate": "2026-08-01",
  "purpose": "饲喂犊牛",
  "receiver": "王五",
  "remark": "正常领用"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "新增成功，库存已扣减",
  "data": {
    "id": 9,
    "currentStock": 90
  },
  "timestamp": 1691616000000
}
```

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 80001 | 库存不足，无法领用 | 200 |
| 80002 | 物资已过期，无法领用 | 200 |
| 80003 | 库存物资不存在 | 200 |

---

### 4.9 销售财务模块 finance

#### 4.9.1 薪资记录列表

- **接口名称**：薪资记录列表
- **Method**：GET
- **URL**：`/finance/salary/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| employeeId | long | 否 | 员工 ID |
| month | string | 否 | 月份 yyyy-MM |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "employeeId": 1002,
        "employeeName": "王五",
        "post": "FEEDER",
        "postName": "饲喂员",
        "month": "2026-07",
        "baseSalary": 4000.0,
        "feedingSubsidy": 500.0,
        "medicalSubsidy": 200.0,
        "breedingSubsidy": 0.0,
        "deduction": 0.0,
        "totalSalary": 4700.0,
        "status": "UNPAID",
        "statusName": "未发放",
        "createTime": "2026-08-01 10:00:00"
      }
    ],
    "total": 15,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.9.2 核算薪资

- **接口名称**：核算薪资
- **Method**：POST
- **URL**：`/finance/salary/calculate`
- **鉴权**：是
- **请求体示例**：

```json
{
  "month": "2026-08",
  "employeeIds": [1002, 1003]
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| month | string | 是 | 核算月份 yyyy-MM |
| employeeIds | array | 否 | 员工 ID 数组，为空则核算全部 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "核算成功",
  "data": {
    "calculatedCount": 2,
    "totalAmount": 9800.0,
    "details": [
      {
        "employeeId": 1002,
        "employeeName": "王五",
        "totalSalary": 4700.0
      },
      {
        "employeeId": 1003,
        "employeeName": "赵六",
        "totalSalary": 5100.0
      }
    ]
  },
  "timestamp": 1691616000000
}
```

#### 4.9.3 修改薪资

- **接口名称**：修改薪资
- **Method**：PUT
- **URL**：`/finance/salary/update/{id}`
- **鉴权**：是
- **路径参数**：id（薪资记录 ID）
- **请求体示例**：

```json
{
  "baseSalary": 4500.0,
  "feedingSubsidy": 600.0,
  "deduction": 100.0,
  "remark": "调整饲喂补贴"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "修改成功",
  "data": {
    "totalSalary": 5000.0
  },
  "timestamp": 1691616000000
}
```

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 90001 | 薪资已发放，无法修改 | 200 |

#### 4.9.4 待出栏畜禽列表

- **接口名称**：待出栏畜禽列表
- **Method**：GET
- **URL**：`/finance/sale/ready`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| animalType | string | 否 | 养殖种类 |
| minAgeDays | int | 否 | 最小饲养天数 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 4999,
        "earTag": "0100",
        "animalType": "CATTLE",
        "breed": "西门塔尔牛",
        "penId": 2,
        "penName": "B2育成舍",
        "birthDate": "2026-03-01",
        "entryDate": "2026-03-15",
        "currentWeight": 500.0,
        "ageDays": 162,
        "feedDays": 148,
        "materialCost": 1200.0,
        "medicalCost": 50.0,
        "totalCost": 1250.0,
        "suggestedPrice": 10000.0
      }
    ],
    "total": 30,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

- **备注**：系统自动读取每只畜禽的饲养天数和累计物资成本。

#### 4.9.5 出栏销售

- **接口名称**：出栏销售
- **Method**：POST
- **URL**：`/finance/sale/out`
- **鉴权**：是
- **请求体示例**：

```json
{
  "saleItems": [
    {
      "earTag": "0100",
      "unitPrice": 20.0,
      "weight": 500.0
    },
    {
      "earTag": "0101",
      "unitPrice": 22.0,
      "weight": 480.0
    }
  ],
  "customerName": "XX肉业公司",
  "customerPhone": "13900139000",
  "saleDate": "2026-08-10",
  "paymentMethod": "BANK_TRANSFER",
  "remark": "批量销售"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| saleItems | array | 是 | 销售明细数组 |
| saleItems[].earTag | string | 是 | 耳标 |
| saleItems[].unitPrice | double | 是 | 单价（元/斤或元/kg） |
| saleItems[].weight | double | 是 | 重量 |
| customerName | string | 是 | 客户名称 |
| customerPhone | string | 否 | 客户电话 |
| saleDate | string | 是 | 销售日期 |
| paymentMethod | string | 否 | 付款方式：CASH 现金 / BANK_TRANSFER 银行转账 / WECHAT 微信 / ALIPAY 支付宝 |
| remark | string | 否 | 备注 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "出栏销售成功",
  "data": {
    "orderId": 1001,
    "totalAmount": 20560.0,
    "totalCost": 2500.0,
    "totalProfit": 18060.0,
    "soldCount": 2
  },
  "timestamp": 1691616000000
}
```

- **备注**：销售成功后畜禽状态变更为「已出栏」，自动生成销售订单。

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 90002 | 畜禽已出栏，不可重复销售 | 200 |
| 90003 | 畜禽不存在或不属于本养殖场 | 200 |

#### 4.9.6 销售订单列表

- **接口名称**：销售订单列表
- **Method**：GET
- **URL**：`/finance/sale/order/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| customerName | string | 否 | 客户名称 |
| saleDateStart | string | 否 | 销售开始日期 |
| saleDateEnd | string | 否 | 销售结束日期 |
| settleStatus | string | 否 | 结算状态：UNSETTLED 未结算 / SETTLED 已结算 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1001,
        "orderNo": "SA202608100001",
        "customerName": "XX肉业公司",
        "customerPhone": "13900139000",
        "saleDate": "2026-08-10",
        "totalAmount": 20560.0,
        "totalCost": 2500.0,
        "totalProfit": 18060.0,
        "soldCount": 2,
        "paymentMethod": "BANK_TRANSFER",
        "paymentMethodName": "银行转账",
        "settleStatus": "UNSETTLED",
        "settleStatusName": "未结算",
        "remark": "批量销售",
        "createTime": "2026-08-10 10:00:00"
      }
    ],
    "total": 12,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.9.7 销售订单详情

- **接口名称**：销售订单详情
- **Method**：GET
- **URL**：`/finance/sale/order/{id}`
- **鉴权**：是
- **路径参数**：id（订单 ID）
- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "id": 1001,
    "orderNo": "SA202608100001",
    "customerName": "XX肉业公司",
    "customerPhone": "13900139000",
    "saleDate": "2026-08-10",
    "totalAmount": 20560.0,
    "totalCost": 2500.0,
    "totalProfit": 18060.0,
    "soldCount": 2,
    "paymentMethod": "BANK_TRANSFER",
    "paymentMethodName": "银行转账",
    "settleStatus": "UNSETTLED",
    "settleStatusName": "未结算",
    "remark": "批量销售",
    "items": [
      {
        "earTag": "0100",
        "animalType": "CATTLE",
        "breed": "西门塔尔牛",
        "weight": 500.0,
        "unitPrice": 20.0,
        "amount": 10000.0,
        "cost": 1250.0,
        "profit": 8750.0
      },
      {
        "earTag": "0101",
        "animalType": "CATTLE",
        "breed": "西门塔尔牛",
        "weight": 480.0,
        "unitPrice": 22.0,
        "amount": 10560.0,
        "cost": 1250.0,
        "profit": 9310.0
      }
    ],
    "createTime": "2026-08-10 10:00:00"
  },
  "timestamp": 1691616000000
}
```

#### 4.9.8 结算订单

- **接口名称**：结算订单
- **Method**：PUT
- **URL**：`/finance/sale/order/settle/{id}`
- **鉴权**：是
- **路径参数**：id（订单 ID）
- **请求体示例**：

```json
{
  "actualAmount": 20560.0,
  "settleDate": "2026-08-10",
  "remark": "已收款"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "结算成功",
  "data": {
    "settleStatus": "SETTLED",
    "actualAmount": 20560.0
  },
  "timestamp": 1691616000000
}
```

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 90004 | 订单已结算，不可重复结算 | 200 |
| 90005 | 订单不存在 | 200 |

#### 4.9.9 成本支出列表

- **接口名称**：成本支出列表
- **Method**：GET
- **URL**：`/finance/cost/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| costType | string | 否 | 成本类型：PURCHASE 进货 / SALARY 薪资 / MEDICAL 医疗 / UTILITY 水电 / OTHER 其他 |
| costDateStart | string | 否 | 开始日期 |
| costDateEnd | string | 否 | 结束日期 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "costType": "PURCHASE",
        "costTypeName": "进货",
        "amount": 10000.0,
        "costDate": "2026-07-01",
        "relatedId": 1,
        "relatedType": "PURCHASE",
        "remark": "代乳粉进货"
      }
    ],
    "total": 50,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.9.10 新增成本支出

- **接口名称**：新增成本支出
- **Method**：POST
- **URL**：`/finance/cost/add`
- **鉴权**：是
- **请求体示例**：

```json
{
  "costType": "UTILITY",
  "amount": 500.0,
  "costDate": "2026-08-01",
  "remark": "8月份电费"
}
```

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "新增成功",
  "data": {
    "id": 51
  },
  "timestamp": 1691616000000
}
```

#### 4.9.11 单只利润核算

- **接口名称**：单只利润核算
- **Method**：GET
- **URL**：`/finance/profit/single/{earTag}`
- **鉴权**：是
- **路径参数**：earTag（耳标）
- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "earTag": "0100",
    "animalType": "CATTLE",
    "breed": "西门塔尔牛",
    "entryDate": "2026-03-15",
    "saleDate": "2026-08-10",
    "feedDays": 148,
    "entryWeight": 50.0,
    "saleWeight": 500.0,
    "costDetail": {
      "feedCost": 800.0,
      "medicalCost": 50.0,
      "vaccineCost": 30.0,
      "otherCost": 0.0,
      "totalCost": 880.0
    },
    "incomeDetail": {
      "saleAmount": 10000.0,
      "otherIncome": 0.0,
      "totalIncome": 10000.0
    },
    "profit": 9120.0,
    "profitMargin": 91.2
  },
  "timestamp": 1691616000000
}
```

#### 4.9.12 利润汇总

- **接口名称**：利润汇总
- **Method**：GET
- **URL**：`/finance/profit/summary`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| startDate | string | 否 | 开始日期 |
| endDate | string | 否 | 结束日期 |
| animalType | string | 否 | 养殖种类 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "totalIncome": 150000.0,
    "totalCost": 80000.0,
    "totalProfit": 70000.0,
    "profitMargin": 46.67,
    "soldCount": 30,
    "details": [
      {
        "animalType": "CATTLE",
        "soldCount": 20,
        "totalIncome": 100000.0,
        "totalCost": 50000.0,
        "totalProfit": 50000.0
      },
      {
        "animalType": "SHEEP",
        "soldCount": 10,
        "totalIncome": 50000.0,
        "totalCost": 30000.0,
        "totalProfit": 20000.0
      }
    ]
  },
  "timestamp": 1691616000000
}
```

---

### 4.10 统计模块 statistics

#### 4.10.1 综合大屏数据

- **接口名称**：综合大屏数据
- **Method**：GET
- **URL**：`/statistics/dashboard`
- **鉴权**：是
- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "farmInfo": {
      "farmName": "阳光养殖场",
      "animalTypes": ["CATTLE", "SHEEP"]
    },
    "animalSummary": {
      "totalCount": 580,
      "todayInCount": 5,
      "todayOutCount": 2,
      "todayDeathCount": 1
    },
    "penSummary": {
      "totalPen": 20,
      "usedPen": 18,
      "utilizationRate": 90.0
    },
    "feedingSummary": {
      "todayFeedCount": 15,
      "pendingReviewCount": 3
    },
    "breedingSummary": {
      "pregnantCount": 8,
      "expectedBirthThisWeek": 2,
      "alertCount": 5
    },
    "healthSummary": {
      "vaccineThisMonth": 20,
      "medicalThisMonth": 5
    },
    "inventorySummary": {
      "totalValue": 50000.0,
      "warningCount": 2,
      "expiredCount": 1
    },
    "financeSummary": {
      "monthIncome": 50000.0,
      "monthCost": 20000.0,
      "monthProfit": 30000.0
    },
    "todos": {
      "pen_count": 20,
      "shortage_count": 2,
      "expiring_count": 1,
      "expired_count": 1,
      "alert_by_type": {
        "临产": 1,
        "孕检": 3,
        "未发情": 1
      },
      "recent_alerts": [
        {
          "id": 1,
          "alert_type": "临产",
          "animal_tag": "0102",
          "alert_content": "距预产期 15 天，请做好接产准备",
          "alert_date": "2027-04-13"
        }
      ],
      "shortage_items": [
        {
          "id": 1,
          "material_name": "代乳粉",
          "material_type": "饲料",
          "quantity": 10.0
        }
      ]
    }
  },
  "timestamp": 1691616000000
}
```

- **备注**：首页今日待办（临产提醒、库存不足提醒、圈舍总数等）由 `data.todos` 字段提供，无独立 `/review/todo` 端点。

#### 4.10.2 存栏繁育统计

- **接口名称**：存栏繁育统计
- **Method**：GET
- **URL**：`/statistics/breeding`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| startDate | string | 否 | 开始日期 |
| endDate | string | 否 | 结束日期 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "stockByType": [
      {
        "animalType": "CATTLE",
        "totalCount": 300,
        "maleCount": 50,
        "femaleCount": 250,
        "byStage": [
          {"growthStage": "犊牛期", "count": 80},
          {"growthStage": "保育期", "count": 60},
          {"growthStage": "生长期", "count": 100},
          {"growthStage": "育肥期", "count": 50},
          {"growthStage": "繁育期", "count": 10}
        ]
      }
    ],
    "breedingSummary": {
      "matingCount": 12,
      "pregnancyCount": 8,
      "birthCount": 5,
      "survivalCount": 5
    }
  },
  "timestamp": 1691616000000
}
```

#### 4.10.3 防疫诊疗统计

- **接口名称**：防疫诊疗统计
- **Method**：GET
- **URL**：`/statistics/health`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| startDate | string | 否 | 开始日期 |
| endDate | string | 否 | 结束日期 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "vaccineStats": [
      {
        "vaccineType": "口蹄疫",
        "count": 50,
        "nextVaccineCount": 10
      }
    ],
    "medicalStats": [
      {
        "diagnosis": "感冒",
        "count": 5,
        "totalCost": 250.0
      }
    ],
    "totalVaccineCount": 50,
    "totalMedicalCount": 10,
    "totalMedicalCost": 500.0
  },
  "timestamp": 1691616000000
}
```

#### 4.10.4 物资消耗统计

- **接口名称**：物资消耗统计
- **Method**：GET
- **URL**：`/statistics/material`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| startDate | string | 否 | 开始日期 |
| endDate | string | 否 | 结束日期 |
| materialType | string | 否 | 物资类型 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "totalPurchaseAmount": 50000.0,
    "totalConsumeAmount": 30000.0,
    "currentStockValue": 20000.0,
    "consumeByType": [
      {
        "materialType": "FEED",
        "materialTypeName": "饲料",
        "consumeCount": 100,
        "consumeAmount": 20000.0
      },
      {
        "materialType": "VACCINE",
        "materialTypeName": "疫苗",
        "consumeCount": 50,
        "consumeAmount": 5000.0
      }
    ],
    "trend": [
      {"date": "2026-08", "purchaseAmount": 5000.0, "consumeAmount": 3000.0}
    ]
  },
  "timestamp": 1691616000000
}
```

#### 4.10.5 财务统计

- **接口名称**：财务统计
- **Method**：GET
- **URL**：`/statistics/finance`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| startDate | string | 否 | 开始日期 |
| endDate | string | 否 | 结束日期 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "totalIncome": 150000.0,
    "totalCost": 80000.0,
    "totalProfit": 70000.0,
    "profitMargin": 46.67,
    "incomeBreakdown": [
      {"type": "SALE", "typeName": "销售收入", "amount": 150000.0}
    ],
    "costBreakdown": [
      {"type": "PURCHASE", "typeName": "进货", "amount": 50000.0},
      {"type": "SALARY", "typeName": "薪资", "amount": 20000.0},
      {"type": "MEDICAL", "typeName": "医疗", "amount": 5000.0},
      {"type": "UTILITY", "typeName": "水电", "amount": 5000.0}
    ],
    "monthlyTrend": [
      {"month": "2026-07", "income": 60000.0, "cost": 35000.0, "profit": 25000.0},
      {"month": "2026-08", "income": 90000.0, "cost": 45000.0, "profit": 45000.0}
    ]
  },
  "timestamp": 1691616000000
}
```

---

### 4.11 审核模块 review

#### 4.11.1 待审核列表

- **接口名称**：待审核列表
- **Method**：GET
- **URL**：`/review/pending/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| bizType | string | 否 | 业务类型：FEEDING 饲喂 / 其他 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1001,
        "bizType": "FEEDING",
        "bizTypeName": "饲喂记录",
        "bizId": 61,
        "title": "饲喂记录审核 - A1育雏舍 2026-08-10",
        "submitterId": 1002,
        "submitterName": "王五",
        "submitTime": "2026-08-10 08:00:00",
        "status": "PENDING",
        "statusName": "待审核",
        "content": "饲喂方案：犊牛标准饲喂方案，数量：85头，总饲喂量：212.5kg"
      }
    ],
    "total": 5,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.11.2 全部审核记录

- **接口名称**：全部审核记录
- **Method**：GET
- **URL**：`/review/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| bizType | string | 否 | 业务类型 |
| status | string | 否 | 状态：PENDING / APPROVED / REJECTED |
| submitDateStart | string | 否 | 提交开始日期 |
| submitDateEnd | string | 否 | 提交结束日期 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1001,
        "bizType": "FEEDING",
        "bizTypeName": "饲喂记录",
        "bizId": 61,
        "title": "饲喂记录审核 - A1育雏舍 2026-08-10",
        "submitterId": 1002,
        "submitterName": "王五",
        "submitTime": "2026-08-10 08:00:00",
        "auditorId": 1,
        "auditorName": "张三",
        "auditTime": "2026-08-10 09:00:00",
        "status": "APPROVED",
        "statusName": "已通过",
        "auditRemark": "审核通过",
        "content": "饲喂方案：犊牛标准饲喂方案，数量：85头，总饲喂量：212.5kg"
      }
    ],
    "total": 60,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.11.3 审批操作

- **接口名称**：审批操作
- **Method**：PUT
- **URL**：`/review/audit/{id}`
- **鉴权**：是
- **路径参数**：id（审核记录 ID）
- **请求体示例**：

```json
{
  "auditResult": "APPROVED",
  "remark": "审核通过"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| auditResult | string | 是 | 审批结果：APPROVED 通过 / REJECTED 驳回 |
| remark | string | 否 | 备注（驳回时建议必填） |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "审批成功",
  "data": {
    "status": "APPROVED"
  },
  "timestamp": 1691616000000
}
```

- **错误码**：

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 10001 | 审核记录不存在 | 200 |
| 10002 | 审核记录已被处理 | 200 |
| 10003 | 无权限审批 | 200 |

#### 4.11.4 今日待办

- **说明**：系统无独立 `/review/todo` 端点。今日待办（今日待办、临产提醒、库存不足提醒、存栏总数、圈舍总数）由 `GET /statistics/dashboard` 响应中的 `todos` 字段提供，详见 4.10.1。

---

### 4.12 系统模块 system

#### 4.12.1 用户列表

- **接口名称**：用户列表
- **Method**：GET
- **URL**：`/system/user/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| keyword | string | 否 | 关键字 |
| userType | string | 否 | 用户类型 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "phone": "13800138000",
        "nickname": "张三",
        "realName": "张三",
        "userType": "OWNER",
        "userTypeName": "养殖场主",
        "post": null,
        "farmId": 1001,
        "farmName": "阳光养殖场",
        "status": 1,
        "createTime": "2026-08-01 10:00:00"
      }
    ],
    "total": 16,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.12.2 角色列表

- **接口名称**：角色列表
- **Method**：GET
- **URL**：`/system/role/list`
- **鉴权**：是
- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "roleName": "超级管理员",
        "roleCode": "admin",
        "description": "系统超级管理员",
        "userCount": 1,
        "createTime": "2026-08-01 10:00:00"
      },
      {
        "id": 2,
        "roleName": "养殖场主",
        "roleCode": "owner",
        "description": "养殖场主管理员",
        "userCount": 1,
        "createTime": "2026-08-01 10:00:00"
      },
      {
        "id": 3,
        "roleName": "饲喂员",
        "roleCode": "feeder",
        "description": "负责日常饲喂",
        "userCount": 4,
        "createTime": "2026-08-01 10:00:00"
      },
      {
        "id": 4,
        "roleName": "兽医",
        "roleCode": "vet",
        "description": "负责防疫诊疗",
        "userCount": 3,
        "createTime": "2026-08-01 10:00:00"
      },
      {
        "id": 5,
        "roleName": "繁育员",
        "roleCode": "breeder",
        "description": "负责配种繁育",
        "userCount": 4,
        "createTime": "2026-08-01 10:00:00"
      },
      {
        "id": 6,
        "roleName": "库管员",
        "roleCode": "keeper",
        "description": "负责物资管理",
        "userCount": 4,
        "createTime": "2026-08-01 10:00:00"
      }
    ],
    "total": 6,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.12.3 菜单列表

- **接口名称**：菜单列表
- **Method**：GET
- **URL**：`/system/menu/list`
- **鉴权**：是
- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "menuName": "养殖场管理",
        "parentId": 0,
        "path": "/farm",
        "component": "farm/index",
        "icon": "farm",
        "sort": 1,
        "visible": 1,
        "children": [
          {
            "id": 11,
            "menuName": "员工管理",
            "parentId": 1,
            "path": "/farm/employee",
            "component": "farm/employee",
            "icon": "user",
            "sort": 1,
            "visible": 1
          }
        ]
      }
    ]
  },
  "timestamp": 1691616000000
}
```

#### 4.12.4 字典类型列表

- **接口名称**：字典类型列表
- **Method**：GET
- **URL**：`/system/dict/type/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| keyword | string | 否 | 关键字 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "dictName": "用户类型",
        "dictType": "user_type",
        "status": 1,
        "remark": "用户类型字典",
        "createTime": "2026-08-01 10:00:00"
      },
      {
        "id": 2,
        "dictName": "圈舍类型",
        "dictType": "pen_type",
        "status": 1,
        "remark": "圈舍类型字典",
        "createTime": "2026-08-01 10:00:00"
      }
    ],
    "total": 10,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.12.5 字典数据列表

- **接口名称**：字典数据列表
- **Method**：GET
- **URL**：`/system/dict/data/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| dictType | string | 是 | 字典类型 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "dictType": "role",
        "dictLabel": "超级管理员",
        "dictValue": "admin",
        "sort": 1,
        "status": 1,
        "remark": "系统超级管理员"
      },
      {
        "id": 2,
        "dictType": "role",
        "dictLabel": "养殖场主",
        "dictValue": "owner",
        "sort": 2,
        "status": 1,
        "remark": "养殖场主管理员"
      },
      {
        "id": 3,
        "dictType": "role",
        "dictLabel": "饲喂员",
        "dictValue": "feeder",
        "sort": 3,
        "status": 1,
        "remark": "负责日常饲喂"
      },
      {
        "id": 4,
        "dictType": "role",
        "dictLabel": "兽医",
        "dictValue": "vet",
        "sort": 4,
        "status": 1,
        "remark": "负责防疫诊疗"
      },
      {
        "id": 5,
        "dictType": "role",
        "dictLabel": "繁育员",
        "dictValue": "breeder",
        "sort": 5,
        "status": 1,
        "remark": "负责配种繁育"
      },
      {
        "id": 6,
        "dictType": "role",
        "dictLabel": "库管员",
        "dictValue": "keeper",
        "sort": 6,
        "status": 1,
        "remark": "负责物资管理"
      }
    ],
    "total": 6,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.12.6 操作日志

- **接口名称**：操作日志
- **Method**：GET
- **URL**：`/system/oper-log/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| userId | long | 否 | 操作用户 ID |
| operDateStart | string | 否 | 操作开始日期 |
| operDateEnd | string | 否 | 操作结束日期 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "userId": 1,
        "userName": "张三",
        "module": "档案管理",
        "operType": "新增",
        "operUrl": "/api/v1/animal/individual",
        "operParam": "{\"earTag\":\"0102\"}",
        "operResult": "成功",
        "operIp": "192.168.1.1",
        "operLocation": "内网",
        "operTime": "2026-08-10 10:00:00"
      }
    ],
    "total": 100,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.12.7 登录日志

- **接口名称**：登录日志
- **Method**：GET
- **URL**：`/system/login-log/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| userId | long | 否 | 用户 ID |
| loginDateStart | string | 否 | 登录开始日期 |
| loginDateEnd | string | 否 | 登录结束日期 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "userId": 1,
        "userName": "张三",
        "phone": "13800138000",
        "loginIp": "192.168.1.1",
        "loginLocation": "内网",
        "browser": "Chrome",
        "os": "Windows 10",
        "loginStatus": "SUCCESS",
        "loginStatusName": "成功",
        "msg": "登录成功",
        "loginTime": "2026-08-10 08:00:00"
      }
    ],
    "total": 50,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

#### 4.12.8 通知列表

- **接口名称**：通知列表
- **Method**：GET
- **URL**：`/system/notice/list`
- **鉴权**：是
- **查询参数**：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |
| noticeType | string | 否 | 通知类型 |

- **响应体示例**：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "list": [
      {
        "id": 1,
        "title": "系统升级通知",
        "noticeType": "SYSTEM",
        "noticeTypeName": "系统通知",
        "content": "系统将于今晚 23:00 进行升级维护，预计耗时 1 小时",
        "status": 1,
        "publishTime": "2026-08-09 18:00:00"
      }
    ],
    "total": 5,
    "pageNum": 1,
    "pageSize": 10
  },
  "timestamp": 1691616000000
}
```

---

## 5. 数据模型（DTO/VO）

### 5.1 通用响应体 CommonResult

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| code | int | 业务状态码 |
| msg | string | 提示信息 |
| data | object/array/null | 业务数据 |
| timestamp | long | 时间戳 |

### 5.2 分页响应 PageResult

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| list | array | 数据列表 |
| total | long | 总记录数 |
| pageNum | int | 当前页码 |
| pageSize | int | 每页条数 |

### 5.3 登录请求 LoginDTO

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| phone | string | 是 | 手机号 |
| password | string | 是 | 密码 |

### 5.4 登录响应 LoginVO

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| token | string | 访问 Token |
| refreshToken | string | 刷新 Token |
| expiresIn | long | 过期时间（秒） |
| userInfo | object | 用户信息 |

### 5.5 养殖场主注册 OwnerRegisterDTO

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| phone | string | 是 | 手机号 |
| password | string | 是 | 密码 |
| nickname | string | 是 | 昵称 |
| farmName | string | 是 | 养殖场名称 |
| farmType | array | 是 | 养殖种类数组 |
| address | string | 否 | 地址 |
| contactName | string | 否 | 联系人 |
| contactPhone | string | 否 | 联系电话 |

### 5.6 圈舍 PenVO

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | long | 圈舍 ID |
| penName | string | 圈舍名称 |
| penCode | string | 圈舍编码 |
| penType | string | 圈舍类型 A/B/C/D |
| penTypeName | string | 圈舍类型名称 |
| capacity | int | 容量 |
| currentCount | int | 当前数量 |
| animalType | string | 养殖种类 |
| remark | string | 备注 |

### 5.7 畜禽档案 AnimalVO

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | long | 档案 ID |
| earTag | string | 耳标 |
| penId | long | 圈舍 ID |
| penName | string | 圈舍名称 |
| animalType | string | 养殖种类 |
| gender | int | 性别 |
| breed | string | 品种 |
| birthDate | string | 出生日期 |
| entryDate | string | 入栏日期 |
| entryWeight | double | 入栏体重 |
| currentWeight | double | 当前体重 |
| ageDays | int | 日龄 |
| growthStage | string | 生长阶段 |
| growthStageName | string | 生长阶段名称 |
| status | string | 状态 |
| statusName | string | 状态名称 |

### 5.8 个体入栏 IndividualEntryDTO

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| animalType | string | 是 | 养殖种类 |
| penId | long | 是 | 圈舍 ID |
| earTag | string | 是 | 耳标 |
| gender | int | 是 | 性别 |
| breed | string | 否 | 品种 |
| birthDate | string | 是 | 出生日期 |
| entryDate | string | 是 | 入栏日期 |
| entryWeight | double | 否 | 入栏体重 |
| source | string | 否 | 来源 |
| remark | string | 否 | 备注 |

### 5.9 批量入栏 BatchEntryDTO

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| animalType | string | 是 | 养殖种类 |
| growthStage | string | 是 | 生长阶段 |
| entryDate | string | 是 | 入栏日期 |
| commonInfo | object | 否 | 公共信息 |
| items | array | 是 | 入栏明细数组 |

### 5.10 饲喂方案 FeedingPlanVO

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | long | 方案 ID |
| planName | string | 方案名称 |
| animalType | string | 养殖种类 |
| growthStage | string | 生长阶段 |
| feedType | string | 饲料类型 |
| feedAmount | double | 饲喂量 |
| unit | string | 单位 |
| feedTimes | int | 饲喂次数 |
| remark | string | 备注 |

### 5.11 配种记录 MatingRecordVO

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | long | 记录 ID |
| femaleId | long | 母畜 ID |
| femaleEarTag | string | 母畜耳标 |
| maleId | long | 公畜 ID |
| maleEarTag | string | 公畜耳标 |
| animalType | string | 养殖种类 |
| matingDate | string | 配种日期 |
| matingMethod | string | 配种方式 |
| expectedBirthDate | string | 预计生产日期 |
| pregnancyStatus | string | 孕检状态 |
| operator | string | 操作员 |

### 5.12 防疫记录 VaccineRecordVO

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | long | 记录 ID |
| earTag | string | 耳标 |
| animalType | string | 养殖种类 |
| vaccineType | string | 疫苗类型 |
| vaccineDate | string | 防疫日期 |
| dose | double | 剂量 |
| unit | string | 单位 |
| operator | string | 操作员 |
| nextVaccineDate | string | 下次防疫日期 |
| remark | string | 备注 |

### 5.13 库存 StockVO

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | long | 库存 ID |
| materialName | string | 物资名称 |
| materialType | string | 物资类型 |
| materialTypeName | string | 物资类型名称 |
| specification | string | 规格 |
| unit | string | 单位 |
| quantity | int | 数量 |
| warningValue | int | 预警值 |
| unitPrice | double | 单价 |
| totalValue | double | 总价值 |
| productionDate | string | 生产日期 |
| expiryDate | string | 过期日期 |
| status | string | 状态 |
| statusName | string | 状态名称 |

### 5.14 销售订单 SaleOrderVO

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | long | 订单 ID |
| orderNo | string | 订单编号 |
| customerName | string | 客户名称 |
| customerPhone | string | 客户电话 |
| saleDate | string | 销售日期 |
| totalAmount | double | 总金额 |
| totalCost | double | 总成本 |
| totalProfit | double | 总利润 |
| soldCount | int | 销售数量 |
| paymentMethod | string | 付款方式 |
| settleStatus | string | 结算状态 |
| items | array | 销售明细 |

### 5.15 繁育预警 BreedingAlertVO

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | long | 预警 ID |
| alertType | string | 预警类型 |
| alertTypeName | string | 预警类型名称 |
| femaleId | long | 母畜 ID |
| femaleEarTag | string | 母畜耳标 |
| alertDate | string | 预警日期 |
| content | string | 预警内容 |
| status | string | 状态 |
| statusName | string | 状态名称 |

---

## 6. 错误码列表

### 6.1 系统通用错误码（10000-10999）

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 10000 | 系统内部错误 | 500 |
| 10001 | 审核记录不存在 | 200 |
| 10002 | 审核记录已被处理 | 200 |
| 10003 | 无权限审批 | 200 |
| 10004 | 参数校验失败 | 200 |
| 10005 | 文件上传失败 | 200 |
| 10006 | 文件下载失败 | 200 |
| 10007 | 数据不存在 | 200 |
| 10008 | 数据已存在 | 200 |
| 10009 | 操作失败 | 200 |

### 6.2 用户/认证错误码（20000-20999）

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 20001 | 手机号或密码错误 | 200 |
| 20002 | 账号已被禁用 | 200 |
| 20003 | 账号不存在 | 200 |
| 20004 | 密码错误次数过多，请稍后再试 | 200 |
| 20005 | 手机号已被注册 | 200 |
| 20006 | 养殖场名称已存在 | 200 |
| 20007 | farmType 不能为空 | 200 |
| 20008 | 当前用户无权限添加员工 | 200 |
| 20009 | 岗位类型不合法 | 200 |
| 20010 | refresh_token 无效 | 200 |
| 20011 | refresh_token 已过期 | 200 |
| 20012 | 不能删除自己 | 200 |
| 20013 | Token 已过期 | 401 |
| 20014 | Token 无效 | 401 |
| 20015 | 无权限访问该资源 | 403 |

### 6.3 档案错误码（30000-30999）

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 30001 | 耳标已存在 | 200 |
| 30002 | 耳标格式不正确（4 位数字） | 200 |
| 30003 | 圈舍已满 | 200 |
| 30004 | 批量入栏数量超过圈舍容量 | 200 |
| 30005 | 部分耳标已存在 | 200 |
| 30006 | 耳标已被占用，无法恢复 | 200 |
| 30007 | 历史记录不存在 | 200 |
| 30008 | 档案不存在 | 200 |
| 30009 | 档案已出栏，不可操作 | 200 |
| 30010 | 性别字段不合法 | 200 |
| 30011 | 出生日期不合法 | 200 |
| 30012 | 养殖种类不合法 | 200 |
| 30013 | 生长阶段与日龄不匹配 | 200 |

### 6.4 圈舍错误码（40000-40999）

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 40001 | 圈舍编码已存在 | 200 |
| 40002 | 圈舍类型不合法 | 200 |
| 40003 | 圈舍内仍有畜禽，无法删除 | 200 |
| 40004 | 无可用圈舍 | 200 |
| 40005 | 圈舍容量不足 | 200 |
| 40006 | 圈舍不存在 | 200 |
| 40007 | 圈舍不属于本养殖场 | 200 |
| 40008 | 圈舍类型与生长阶段不匹配 | 200 |

### 6.5 饲喂错误码（50000-50999）

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 50001 | 饲喂记录已审核，无法修改 | 200 |
| 50002 | 饲喂方案不存在 | 200 |
| 50003 | 饲喂记录不存在 | 200 |
| 50004 | 饲喂量不能小于 0 | 200 |
| 50005 | 圈舍内无畜禽，无法提交饲喂记录 | 200 |
| 50006 | 饲喂方案已被引用，无法删除 | 200 |

### 6.6 繁育错误码（60000-60999）

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 60001 | 母畜未达到可繁育日龄 | 200 |
| 60002 | 母畜正在妊娠中，不可重复配种 | 200 |
| 60003 | 母畜或公畜不存在 | 200 |
| 60004 | 配种记录不存在 | 200 |
| 60005 | 母畜未到生产日期 | 200 |
| 60006 | 繁育预警不存在 | 200 |
| 60007 | 繁育预警已被处理 | 200 |
| 60008 | 母畜耳标不存在 | 200 |
| 60009 | 公畜耳标不存在 | 200 |
| 60010 | 产犊记录不存在 | 200 |

### 6.7 防疫诊疗错误码（70000-70999）

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 70001 | 畜禽档案不存在 | 200 |
| 70002 | 疫苗类型不存在 | 200 |
| 70003 | 防疫记录不存在 | 200 |
| 70004 | 诊疗记录不存在 | 200 |
| 70005 | 剂量必须大于 0 | 200 |
| 70006 | 防疫日期不能晚于当前日期 | 200 |
| 70007 | 批量防疫耳标不存在 | 200 |

### 6.8 物资错误码（80000-80999）

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 80001 | 库存不足，无法领用 | 200 |
| 80002 | 物资已过期，无法领用 | 200 |
| 80003 | 库存物资不存在 | 200 |
| 80004 | 进货数量必须大于 0 | 200 |
| 80005 | 领用数量必须大于 0 | 200 |
| 80006 | 物资类型不合法 | 200 |
| 80007 | 物资名称已存在 | 200 |
| 80008 | 库存已达预警值 | 200 |

### 6.9 销售财务错误码（90000-90999）

| 错误码 | 含义 | HTTP 状态 |
| --- | --- | --- |
| 90001 | 薪资已发放，无法修改 | 200 |
| 90002 | 畜禽已出栏，不可重复销售 | 200 |
| 90003 | 畜禽不存在或不属于本养殖场 | 200 |
| 90004 | 订单已结算，不可重复结算 | 200 |
| 90005 | 订单不存在 | 200 |
| 90006 | 单价必须大于 0 | 200 |
| 90007 | 重量必须大于 0 | 200 |
| 90008 | 销售明细不能为空 | 200 |
| 90009 | 客户名称不能为空 | 200 |
| 90010 | 成本支出金额必须大于 0 | 200 |
| 90011 | 利润核算失败 | 200 |
| 90012 | 耳标不存在 | 200 |

---

## 7. 附录

### 7.1 通用枚举对照表

#### 7.1.1 role 角色编码（RBAC）

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| admin | 超级管理员 | 系统超级管理员 |
| owner | 养殖场主 | 养殖场主管理员 |
| feeder | 饲喂员 | 负责日常饲喂 |
| vet | 兽医 | 负责防疫诊疗 |
| breeder | 繁育员 | 负责配种繁育 |
| keeper | 库管员 | 负责物资管理 |

#### 7.1.2 post 岗位类型

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| FEEDER | 饲喂员 | 负责日常饲喂 |
| VET | 兽医 | 负责防疫诊疗 |
| BREEDER | 繁育员 | 负责配种繁育 |
| KEEPER | 库管员 | 负责物资管理 |

#### 7.1.3 animal_type 养殖种类

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| CATTLE | 牛 | 牛类养殖 |
| SHEEP | 羊 | 羊类养殖 |
| PIG | 猪 | 猪类养殖 |

#### 7.1.4 pen_type 圈舍类型

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| A | 育雏舍 | 用于饲养幼崽 |
| B | 育成舍 | 用于饲养生长中畜禽 |
| C | 繁育舍 | 用于繁育期母畜 |
| D | 种畜圈舍 | 用于种畜饲养 |

#### 7.1.5 growth_stage 生长阶段（牛）

| 枚举值 | 中文名 | 日龄范围 |
| --- | --- | --- |
| 犊牛期 | 犊牛期 | 1-60 |
| 保育期 | 保育期 | 61-180 |
| 生长期 | 生长期 | 181-365 |
| 育肥期 | 育肥期 | 366-540 |
| 繁育期 | 繁育期 | 540 以上 |

#### 7.1.6 growth_stage 生长阶段（羊）

| 枚举值 | 中文名 | 日龄范围 |
| --- | --- | --- |
| 羔羊期 | 羔羊期 | 1-45 |
| 保育期 | 保育期 | 46-90 |
| 生长期 | 生长期 | 91-180 |
| 育肥期 | 育肥期 | 181-270 |
| 繁育期 | 繁育期 | 270 以上 |

#### 7.1.7 growth_stage 生长阶段（猪）

| 枚举值 | 中文名 | 日龄范围 |
| --- | --- | --- |
| 仔猪期 | 仔猪期 | 1-28 |
| 保育期 | 保育期 | 29-70 |
| 生长期 | 生长期 | 71-120 |
| 育肥期 | 育肥期 | 121-180 |
| 繁育期 | 繁育期 | 180 以上 |

- **备注**：妊娠不属于生长阶段，由母畜生理状态 `physio_status`（发情/妊娠/泌乳/休情/淘汰）表达，见 7.1.16。

#### 7.1.8 animal_status 畜禽状态

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| 在栏 | 在栏 | 当前在栏饲养 |
| 种用 | 种用 | 用于配种繁育 |
| 隔离 | 隔离 | 隔离观察 |
| 待出栏 | 待出栏 | 即将出栏销售 |
| 已出栏 | 已出栏 | 已销售出栏 |
| 死亡 | 死亡 | 已死亡 |

#### 7.1.9 material_type 物资类型

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| FEED | 饲料 | 各类饲料 |
| VACCINE | 疫苗 | 各类疫苗 |
| MEDICINE | 药品 | 各类药品 |
| OTHER | 其他 | 其他物资 |

#### 7.1.10 material_status 物资状态

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| NORMAL | 正常 | 库存正常 |
| LOW_STOCK | 低库存 | 库存低于预警值 |
| EXPIRED | 过期 | 已过保质期 |

#### 7.1.11 audit_status 审核状态

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| PENDING | 待审核 | 等待审核 |
| APPROVED | 已通过 | 审核通过 |
| REJECTED | 已驳回 | 审核驳回 |

#### 7.1.12 settle_status 结算状态

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| UNSETTLED | 未结算 | 订单未结算 |
| SETTLED | 已结算 | 订单已结算 |

#### 7.1.13 payment_method 付款方式

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| CASH | 现金 | 现金支付 |
| BANK_TRANSFER | 银行转账 | 银行转账 |
| WECHAT | 微信 | 微信支付 |
| ALIPAY | 支付宝 | 支付宝支付 |

#### 7.1.14 mating_method 配种方式

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| NATURE | 自然配种 | 自然交配 |
| ARTIFICIAL | 人工授精 | 人工授精 |

#### 7.1.15 birth_type 生产类型

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| NORMAL | 顺产 | 正常顺产 |
| DIFFICULT | 难产 | 难产 |
| CESAREAN | 剖腹产 | 剖腹产 |

#### 7.1.16 physio_status 母畜生理状态（仅母畜）

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| 发情 | 发情 | 处于发情期，可配种 |
| 妊娠 | 妊娠 | 已妊娠 |
| 泌乳 | 泌乳 | 哺乳泌乳期 |
| 休情 | 休情 | 休情期 |
| 淘汰 | 淘汰 | 已淘汰 |

#### 7.1.17 alert_type 预警类型

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| PREGNANCY_CHECK | 孕检提醒 | 配种后 60 天孕检 |
| PRE_BIRTH | 临产预警 | 临产前 15 天 |
| POST_BIRTH_ESTRUS | 产后发情预警 | 产后 60 天未发情 |

#### 7.1.18 cost_type 成本类型

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| PURCHASE | 进货 | 物资进货 |
| SALARY | 薪资 | 员工薪资 |
| MEDICAL | 医疗 | 医疗费用 |
| UTILITY | 水电 | 水电费用 |
| OTHER | 其他 | 其他支出 |

#### 7.1.19 delete_reason 删除原因

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| 死亡 | 死亡 | 畜禽死亡 |
| 出栏 | 出栏 | 出栏销售 |
| 其他 | 其他 | 其他原因 |

#### 7.1.20 salary_status 薪资状态

| 枚举值 | 中文名 | 说明 |
| --- | --- | --- |
| UNPAID | 未发放 | 薪资未发放 |
| PAID | 已发放 | 薪资已发放 |

---

### 7.2 接口调用示例（cURL）

#### 7.2.1 登录

```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json;charset=UTF-8" \
  -d '{
    "phone": "13800138000",
    "password": "123456"
  }'
```

#### 7.2.2 个体入栏

```bash
curl -X POST http://localhost:8080/api/v1/animal/individual \
  -H "Content-Type: application/json;charset=UTF-8" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiw..." \
  -d '{
    "animalType": "CATTLE",
    "penId": 1,
    "earTag": "0102",
    "gender": 1,
    "breed": "西门塔尔牛",
    "birthDate": "2026-06-01",
    "entryDate": "2026-08-10",
    "entryWeight": 95.0,
    "source": "自繁",
    "remark": "健康"
  }'
```

#### 7.2.3 批量入栏

```bash
curl -X POST http://localhost:8080/api/v1/animal/batch \
  -H "Content-Type: application/json;charset=UTF-8" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiw..." \
  -d '{
    "animalType": "CATTLE",
    "growthStage": "犊牛期",
    "entryDate": "2026-08-10",
    "commonInfo": {
      "breed": "西门塔尔牛",
      "source": "外购",
      "remark": "批量入栏"
    },
    "items": [
      {
        "penId": 1,
        "earTag": "0103",
        "gender": 1,
        "birthDate": "2026-06-01",
        "entryWeight": 90.0
      },
      {
        "penId": 1,
        "earTag": "0104",
        "gender": 0,
        "birthDate": "2026-06-01",
        "entryWeight": 88.0
      }
    ]
  }'
```

#### 7.2.4 提交饲喂记录

```bash
curl -X POST http://localhost:8080/api/v1/feeding/record/submit \
  -H "Content-Type: application/json;charset=UTF-8" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiw..." \
  -d '{
    "penId": 1,
    "planId": 1,
    "feedDate": "2026-08-10",
    "feedAmount": 212.5,
    "unit": "kg",
    "feedCount": 85,
    "remark": "正常饲喂"
  }'
```

#### 7.2.5 出栏销售

```bash
curl -X POST http://localhost:8080/api/v1/finance/sale/out \
  -H "Content-Type: application/json;charset=UTF-8" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiw..." \
  -d '{
    "saleItems": [
      {
        "earTag": "0100",
        "unitPrice": 20.0,
        "weight": 500.0
      },
      {
        "earTag": "0101",
        "unitPrice": 22.0,
        "weight": 480.0
      }
    ],
    "customerName": "XX肉业公司",
    "customerPhone": "13900139000",
    "saleDate": "2026-08-10",
    "paymentMethod": "BANK_TRANSFER",
    "remark": "批量销售"
  }'
```

#### 7.2.6 养殖场主注册

```bash
curl -X POST http://localhost:8080/api/v1/auth/register/owner \
  -H "Content-Type: application/json;charset=UTF-8" \
  -d '{
    "phone": "13800138001",
    "password": "123456",
    "nickname": "李四",
    "farmName": "阳光养殖场",
    "farmType": ["CATTLE", "SHEEP"],
    "address": "内蒙古呼和浩特市XX镇",
    "contactName": "李四",
    "contactPhone": "13800138001"
  }'
```

#### 7.2.7 自动分配圈舍预览

```bash
curl -X POST http://localhost:8080/api/v1/pen/auto-allocate \
  -H "Content-Type: application/json;charset=UTF-8" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiw..." \
  -d '{
    "animalType": "CATTLE",
    "growthStage": "犊牛期",
    "count": 20
  }'
```

#### 7.2.8 新增配种记录

```bash
curl -X POST http://localhost:8080/api/v1/breeding/mating/add \
  -H "Content-Type: application/json;charset=UTF-8" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiw..." \
  -d '{
    "femaleId": 5002,
    "maleId": 5100,
    "animalType": "CATTLE",
    "matingDate": "2026-08-01",
    "matingMethod": "ARTIFICIAL",
    "operator": "赵六",
    "remark": "首次配种"
  }'
```

#### 7.2.9 获取综合大屏数据

```bash
curl -X GET http://localhost:8080/api/v1/statistics/dashboard \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiw..."
```

#### 7.2.10 审批操作

```bash
curl -X PUT http://localhost:8080/api/v1/review/audit/1001 \
  -H "Content-Type: application/json;charset=UTF-8" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiw..." \
  -d '{
    "auditResult": "APPROVED",
    "remark": "审核通过"
  }'
```

---

### 7.3 Postman 集合说明

#### 7.3.1 集合结构

建议按以下结构组织 Postman 集合：

```
智能养殖信息管理系统 API
├── 环境变量
│   ├── base_url: http://localhost:8080/api/v1
│   ├── token: (登录后自动填充)
│   └── farm_id: (登录后自动填充)
├── 01-认证模块
│   ├── 登录
│   ├── 养殖场主注册
│   ├── 登出
│   ├── 获取当前用户信息
│   └── 刷新 Token
├── 02-养殖场模块
├── 03-圈舍模块
├── 04-档案模块
├── 05-饲喂模块
├── 06-繁育模块
├── 07-防疫诊疗模块
├── 08-物资模块
├── 09-销售财务模块
├── 10-统计模块
├── 11-审核模块
└── 12-系统模块
```

#### 7.3.2 全局请求头配置

在 Postman 集合级别配置以下请求头：

| Header | Value |
| --- | --- |
| Content-Type | application/json;charset=UTF-8 |
| Authorization | Bearer {{token}} |

#### 7.3.3 登录脚本示例

在登录接口的 Tests 脚本中自动保存 Token：

```javascript
var jsonData = pm.response.json();
if (jsonData.code === 200) {
    pm.environment.set("token", jsonData.data.token);
    pm.environment.set("refresh_token", jsonData.data.refreshToken);
    pm.environment.set("farm_id", jsonData.data.userInfo.farmId);
    console.log("Token 已保存");
}
```

#### 7.3.4 批量运行

- 建议先执行登录接口获取 Token
- 使用 Postman Runner 进行批量测试
- 每个模块的接口建议按顺序执行（如档案模块先创建圈舍再入栏）

---

### 7.4 版本管理策略

#### 7.4.1 版本号规则

采用语义化版本号（Semantic Versioning）：

```
MAJOR.MINOR.PATCH
```

| 版本段 | 说明 | 触发条件 |
| --- | --- | --- |
| MAJOR | 主版本号 | 不兼容的 API 修改 |
| MINOR | 次版本号 | 向下兼容的功能新增 |
| PATCH | 修订号 | 向下兼容的缺陷修复 |

#### 7.4.2 API 版本策略

| 策略 | 说明 |
| --- | --- |
| URL 路径版本 | 通过 URL 路径区分版本，如 /api/v1、/api/v2 |
| 向下兼容 | 新版本发布后，旧版本至少维护 6 个月 |
| 废弃通知 | 接口废弃前需在响应头添加 `X-Deprecated: true` |
| 强制升级 | 重大安全漏洞修复可强制升级，提前 7 天通知 |

#### 7.4.3 文档版本管理

| 项目 | 说明 |
| --- | --- |
| 文档仓库 | 与代码仓库统一管理，路径 docs/ |
| 变更记录 | 每次修改需更新文档头部修订记录表 |
| 评审机制 | 接口变更需经过研发组评审 |
| 发布渠道 | 文档随版本发布至内部文档平台 |

#### 7.4.4 接口废弃流程

1. 标记废弃：在接口文档中标注废弃标识和替代接口
2. 过渡期：保持废弃接口可用 6 个月
3. 通知用户：通过系统通知和邮件告知前端开发人员
4. 下线：过渡期结束后移除废弃接口

#### 7.4.5 兼容性原则

| 变更类型 | 是否兼容 | 说明 |
| --- | --- | --- |
| 新增接口 | 兼容 | 不影响现有接口 |
| 新增字段（请求） | 兼容 | 新字段需设置默认值 |
| 新增字段（响应） | 兼容 | 前端忽略未知字段 |
| 删除字段（请求） | 不兼容 | 需升级 MAJOR 版本 |
| 删除字段（响应） | 不兼容 | 需升级 MAJOR 版本 |
| 修改字段类型 | 不兼容 | 需升级 MAJOR 版本 |
| 修改字段含义 | 不兼容 | 需升级 MAJOR 版本 |

---

## 8. 文档结束

本 API 接口文档覆盖智能养殖信息管理系统 12 个模块的全部接口，包括认证、养殖场、圈舍、档案、饲喂、繁育、防疫诊疗、物资、销售财务、统计、审核、系统管理。

如需获取最新版本或反馈问题，请联系智能养殖研发组。

文档版本：v1.0.0
最后更新：2026-08-10
