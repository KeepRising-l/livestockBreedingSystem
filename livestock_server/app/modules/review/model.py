"""
审核 review 模块

不新建业务表：审核状态已存在各业务表（feeding_record / material_purchase /
material_consume / vaccine_record / medical_record 的 audit_status 字段）。
本模块提供统一审核入口：聚合查询待审核列表 + 转发审核到各模块，避免冗余建表导致状态不同步。
"""
