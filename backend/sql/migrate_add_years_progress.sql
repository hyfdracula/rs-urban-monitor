-- ============================================================
-- 迁移：为旧版 user_boundaries 表补充缺失列
-- ============================================================
-- 背景：
--   ORM (app/models.py) 在 user_boundaries 上新增了 4 列：
--     - area_km2       (DOUBLE PRECISION, nullable)  — 研究区面积
--     - years          (TEXT, nullable)        — JSON 年份数组
--     - progress_info  (TEXT, nullable)        — JSON 进度信息
--     - cancelled      (BOOLEAN, default FALSE)
--
--   SQLAlchemy 的 create_all() 对已存在的表不会自动加列，
--   所以按旧 SQL 建过表的数据库需要执行本脚本补列。
--
-- 执行方式（任选其一）：
--   1. psql -U postgres -d ueea2601 -f sql/migrate_add_years_progress.sql
--   2. 在 pgAdmin / DBeaver 里直接粘贴执行
--
-- 幂等：ADD COLUMN IF NOT EXISTS 可重复执行，不会报错。
-- ============================================================

ALTER TABLE user_boundaries ADD COLUMN IF NOT EXISTS area_km2 DOUBLE PRECISION;
ALTER TABLE user_boundaries ADD COLUMN IF NOT EXISTS years TEXT;
ALTER TABLE user_boundaries ADD COLUMN IF NOT EXISTS progress_info TEXT;
ALTER TABLE user_boundaries ADD COLUMN IF NOT EXISTS cancelled BOOLEAN DEFAULT FALSE;
