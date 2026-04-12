-- CodeGuard 数据库初始化脚本
-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS codeguard
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 授权（确保root用户有完整权限）
GRANT ALL PRIVILEGES ON codeguard.* TO 'root'@'%';
FLUSH PRIVILEGES;

-- 使用数据库
USE codeguard;

-- 设置时区
SET GLOBAL time_zone = '+8:00';