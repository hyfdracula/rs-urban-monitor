# RS Urban Monitor 前端部署指南

本文聚焦静态前端与 Nginx 反向代理。完整启动、后端、GeoServer 和验证说明见根目录 [README.md](../README.md)。

## 1. 部署结构

推荐生产结构：

```text
Browser
  -> Nginx :80/:443
      /          -> dist 静态文件
      /api       -> FastAPI 127.0.0.1:8001
      /geoserver -> GeoServer 127.0.0.1:8080
```

前端代码不直接暴露后端或 GeoServer 凭据。浏览器只访问同源 `/api` 和 `/geoserver`。

## 2. 构建

在项目根目录执行：

```powershell
cd C:\Users\19161\Desktop\rs-urban-monitor
npm ci
npm run build
```

产物输出到根目录 `dist/`。

如果部署在域名根路径，保持：

```dotenv
VITE_BASE=/
```

如果部署在子路径，例如 `https://example.com/rs-urban/`：

```powershell
$env:VITE_BASE = "/rs-urban/"
npm run build
```

## 3. Windows Nginx 部署

1. 下载并解压 Nginx for Windows，例如 `C:\nginx`。
2. 构建前端：`npm run build`。
3. 将 `dist/` 复制到目标目录，例如 `C:\nginx\html\rs-urban\dist`。
4. 参考 `frontend/nginx.conf` 修改 `root` 路径。
5. 启动或重载 Nginx：

```powershell
cd C:\nginx
start nginx
nginx -s reload
```

## 4. Linux / WSL Nginx 部署

示例路径为 `/var/www/rs-urban-monitor/dist`：

```bash
sudo mkdir -p /var/www/rs-urban-monitor
sudo cp -r dist /var/www/rs-urban-monitor/
sudo cp frontend/nginx.conf /etc/nginx/sites-available/rs-urban
sudo ln -s /etc/nginx/sites-available/rs-urban /etc/nginx/sites-enabled/rs-urban
sudo nginx -t
sudo systemctl reload nginx
```

如果系统仍启用默认站点，可按需移除：

```bash
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## 5. Docker Nginx 部署

```bash
docker run -d \
  --name rs-urban-web \
  -v "$(pwd)/dist:/var/www/rs-urban-monitor/dist:ro" \
  -v "$(pwd)/frontend/nginx.conf:/etc/nginx/conf.d/default.conf:ro" \
  -p 80:80 \
  nginx:alpine
```

## 6. Nginx 关键配置

静态文件：

```nginx
location / {
    root /var/www/rs-urban-monitor/dist;
    index index.html;
    try_files $uri $uri/ /index.html;
}
```

后端 API：

```nginx
location /api {
    proxy_pass http://127.0.0.1:8001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    client_max_body_size 500m;
    proxy_read_timeout 300s;
}
```

GeoServer：

```nginx
location /geoserver {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    client_max_body_size 500m;
    proxy_read_timeout 120s;
}
```

## 7. 后端与 GeoServer 前置要求

部署前确保：

- FastAPI 后端运行在 `127.0.0.1:8001`。
- GeoServer 运行在 `127.0.0.1:8080/geoserver`。
- PostgreSQL 可连接，`DATABASE_URL` 指向生产数据库。
- 生产环境显式设置 `APP_ENV=production`、`GEOSERVER_USER`、`GEOSERVER_PASS`、`ENCRYPTION_SECRET`。
- 如对外暴露 GeoServer REST 代理，设置 `GEOSERVER_PROXY_TOKEN`。

## 8. 部署后验证

```powershell
curl http://localhost/
curl http://localhost/api/system/status
curl http://localhost/geoserver
```

项目内 HTTP 端到端检查：

```powershell
$env:E2E_FRONTEND_URL = "http://localhost"
$env:E2E_BACKEND_URL = "http://127.0.0.1:8001"
$env:E2E_GEOSERVER_URL = "http://127.0.0.1:8080/geoserver"
npm run test:e2e
```

浏览器验证：

1. 打开前端首页。
2. 进入自定义研究区页面。
3. 打开任务列表。
4. 切换地图图层，确认 WMS 瓦片加载。
5. 打开 `http://localhost/api/system/status`，确认数据库、GeoServer、GEE 服务状态。

## 9. 常见问题

### 刷新页面 404

Nginx 缺少 Vue Router history fallback。确认：

```nginx
try_files $uri $uri/ /index.html;
```

### 接口 404 或跨域

推荐同源部署，浏览器访问 `/api`，由 Nginx 代理到后端。不要让前端直接访问另一个域名的后端，除非同步更新后端 CORS。

### GeoServer 页面能打开但瓦片失败

检查 `/geoserver` 代理、GeoServer workspace、图层名，以及浏览器网络面板中的 WMS URL。

### 上传或发布大文件失败

提高 Nginx 限制：

```nginx
client_max_body_size 500m;
proxy_request_buffering off;
proxy_read_timeout 300s;
```
