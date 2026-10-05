-- ============================================================
-- 智能养殖信息管理系统 · 数据库初始化脚本
-- 适用：全新环境首次部署（MySQL 8.0，5.7 亦可）
--
-- 用法（Windows）：
--   mysql -u root -p < init_database.sql
-- 或登录后执行：
--   source D:/Code/system/docs/init_database.sql;
--
-- 说明：本脚本只负责建库（及可选的独立账号）。
-- 所有数据表由后端首次启动时自动创建（create_all），
-- 超管账号、字典、RBAC 角色菜单也由启动流程自动初始化，
-- 因此无需执行额外的建表语句。
-- ============================================================

-- 1. 创建数据库（utf8mb4 支持 emoji 及全字符集）
CREATE DATABASE IF NOT EXISTS livestock_db
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 2.（可选）为项目创建独立数据库账号，避免直接使用 root
--    密码请自行修改，并同步到 livestock_server/.env 的 DB_USER / DB_PASSWORD
CREATE USER IF NOT EXISTS 'livestock'@'localhost' IDENTIFIED BY 'livestock_123456';
CREATE USER IF NOT EXISTS 'livestock'@'%'         IDENTIFIED BY 'livestock_123456';
GRANT ALL PRIVILEGES ON livestock_db.* TO 'livestock'@'localhost';
GRANT ALL PRIVILEGES ON livestock_db.* TO 'livestock'@'%';
FLUSH PRIVILEGES;

-- 3. 验证
-- SHOW DATABASES LIKE 'livestock_db';
