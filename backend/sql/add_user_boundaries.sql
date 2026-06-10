-- ============================================================
-- UEEA2601 用户上传边界 + GEE 密钥表
-- ============================================================

-- 用户上传的边界
CREATE TABLE IF NOT EXISTS user_boundaries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    compute_mode VARCHAR(20) NOT NULL,
    task_id VARCHAR(12) NOT NULL UNIQUE,
    geom GEOMETRY(MultiPolygon, 4326),
    geojson_text TEXT,
    gee_code TEXT,
    gee_tasks TEXT,
    wms_urls TEXT,
    report_data TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'processing',
    area_km2 DOUBLE PRECISION,
    years TEXT,                           -- JSON: [1990, 2000, 2010, 2020]
    progress_info TEXT,                   -- JSON: {"year": 2010, "step": "...", "percent": 40}
    cancelled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_boundaries_task_id ON user_boundaries(task_id);
CREATE INDEX IF NOT EXISTS idx_boundaries_geom ON user_boundaries USING GIST(geom);

-- 用户 GEE 密钥（方案A：用户自备账号）
CREATE TABLE IF NOT EXISTS user_gee_keys (
    id SERIAL PRIMARY KEY,
    user_token VARCHAR(255) NOT NULL UNIQUE,
    service_account VARCHAR(255) NOT NULL,
    encrypted_key TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'unverified',
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
