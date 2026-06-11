# RS Urban Monitor 启动与部署指南

本项目由前端 Vite/Vue、后端 FastAPI、GeoServer 和 PostgreSQL 组成。日常开发优先使用根目录的一键启动脚本；生产部署建议使用静态前端 + FastAPI 服务 + GeoServer + Nginx 反向代理。

## 服务与端口

| 服务 | 默认地址 | 说明 |
| --- | --- | --- |
| 前端开发服务 | `http://127.0.0.1:5173/` | Vite dev server，代理 `/api` 和 `/geoserver` |
| 后端 API | `http://127.0.0.1:8001` | FastAPI，接口文档在 `/docs` |
| 健康检查 | `http://127.0.0.1:8001/api/system/status` | 联调和端到端检查使用 |
| GeoServer | `http://127.0.0.1:8080/geoserver` | WMS/WFS/REST 服务 |
| ngrok 可选面板 | `http://127.0.0.1:4040` | 仅使用 `-WithNgrok` 时需要 |

## 环境要求

- Windows PowerShell 5+。
- Node.js 和 npm。当前验证环境为 Node `v24.15.0`、npm `11.12.1`。
- Python `3.10+`。后端脚本会依次尝试 `RS_URBAN_PYTHON`、`py -3`、`python`、内置/本机 Python 路径。
- Java/JDK 17。GeoServer 启动脚本会优先使用 `JAVA_HOME`，再扫描常见 JDK 安装目录。
- PostgreSQL。默认连接串为 `postgresql+psycopg2://postgres:postgres@localhost:5432/ueea2601`。
- GeoServer 解压目录：`geoserver-2.25.5-bin/`。

## 首次准备

```powershell
cd C:\Users\19161\Desktop\rs-urban-monitor
npm install

cd backend
python -m pip install -r requirements.txt
```

如果需要浏览器自动化检查：

```powershell
cd C:\Users\19161\Desktop\rs-urban-monitor
npx playwright install chromium
```

## 一键启动

推荐方式：

```powershell
cd C:\Users\19161\Desktop\rs-urban-monitor
.\start-all.bat
```

脚本会执行：

- 检查 8080、8001、5173 是否已有服务在监听；已启动则跳过。
- 启动 GeoServer、FastAPI 后端、Vite 前端。
- 将日志写入 `logs/startup/`。
- 检查前端页面、后端健康接口和 GeoServer 端口。

常用参数：

```powershell
.\start-all.bat -WithNgrok
.\start-all.bat -NoGeoServer
.\start-all.bat -NoBackend
.\start-all.bat -NoFrontend
.\start-all.bat -DryRun
.\start-all.bat -NoPause
```

可用环境变量：

```powershell
$env:RS_URBAN_PYTHON = "C:\Path\To\python.exe"
$env:RS_URBAN_WITH_NGROK = "true"
```

## 手动启动

分开调试时可以按下面顺序启动。

### 1. GeoServer

```powershell
cd C:\Users\19161\Desktop\rs-urban-monitor
.\frontend\start-geoserver.bat
```

访问 `http://127.0.0.1:8080/geoserver`。

### 2. 后端

```powershell
cd C:\Users\19161\Desktop\rs-urban-monitor\backend
.\start.bat
```

或：

```powershell
cd C:\Users\19161\Desktop\rs-urban-monitor\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

访问：

- API 文档：`http://127.0.0.1:8001/docs`
- 健康检查：`http://127.0.0.1:8001/api/system/status`

### 3. 前端

```powershell
cd C:\Users\19161\Desktop\rs-urban-monitor
npm run dev
```

访问 `http://127.0.0.1:5173/`。

## 环境变量

前端变量由 Vite 从根目录 `.env` 读取：

```dotenv
VITE_MAPBOX_TOKEN=your_mapbox_public_token_here
VITE_USE_MAPBOX_STYLE=false
VITE_BASE=/
VITE_USE_API=true
```

后端变量由 `python-dotenv` 和系统环境变量读取。生产环境中建议显式设置：

```dotenv
APP_ENV=production
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/ueea2601
GEOSERVER_URL=http://127.0.0.1:8080/geoserver
GEOSERVER_USER=admin
GEOSERVER_PASS=change-me
GEOSERVER_WORKSPACE=ueea2601
GEOSERVER_PROXY_TOKEN=change-me
ENCRYPTION_SECRET=change-me
GEE_KEY_PATH=C:\path\to\gee-service-account.json
GEE_SERVICE_ACCOUNT=your-service-account
GCS_BUCKET=ueea2601-results
COUNTY_ASSET_ID=users/your-user/china_counties
RESULTS_DIR=C:\rs-urban-results
```

当 `APP_ENV=production` 时，后端会拒绝使用部分开发默认值，例如 `DATABASE_URL`、`GEOSERVER_USER`、`GEOSERVER_PASS`、`ENCRYPTION_SECRET`。

## 验证命令

前端单测：

```powershell
npm test
```

生产构建：

```powershell
npm run build
```

HTTP 端到端检查。需要前端、后端、GeoServer 已启动：

```powershell
npm run test:e2e
```

可覆盖端到端检查地址：

```powershell
$env:E2E_FRONTEND_URL = "http://127.0.0.1:5173"
$env:E2E_BACKEND_URL = "http://127.0.0.1:8001"
$env:E2E_GEOSERVER_URL = "http://127.0.0.1:8080/geoserver"
npm run test:e2e
```

后端 unittest：

```powershell
cd backend
python -m unittest discover -s tests -v
```

Playwright 页面冒烟示例：

```powershell
node -e "const { chromium } = require('playwright'); (async () => { const browser = await chromium.launch({ headless: true }); const page = await browser.newPage(); const errors = []; page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); }); const response = await page.goto('http://127.0.0.1:5173/custom-area', { waitUntil: 'networkidle' }); console.log({ status: response.status(), title: await page.title(), errors }); await browser.close(); })();"
```

## 生产部署

### 推荐拓扑

```text
Browser
  -> Nginx :80/:443
      /              -> dist 静态文件
      /api           -> FastAPI 127.0.0.1:8001
      /geoserver     -> GeoServer 127.0.0.1:8080
```

### 构建前端

```powershell
cd C:\Users\19161\Desktop\rs-urban-monitor
npm ci
npm run build
```

产物位于 `dist/`。如果部署在子路径，例如 `/rs-urban/`，构建前设置：

```powershell
$env:VITE_BASE = "/rs-urban/"
npm run build
```

### 部署后端

开发命令可用于验证：

```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

生产环境建议用 Windows 服务、NSSM、Supervisor、systemd 或容器托管，并设置 `APP_ENV=production` 及生产环境变量。

### 配置 Nginx

可参考 [frontend/nginx.conf](frontend/nginx.conf)。核心要求：

- 静态文件根目录指向构建后的 `dist/`。
- Vue Router history 模式需要 `try_files $uri $uri/ /index.html;`。
- `/api` 反向代理到 `http://127.0.0.1:8001`。
- `/geoserver` 反向代理到 `http://127.0.0.1:8080`。
- 上传/栅格发布场景建议调高 `client_max_body_size` 和代理超时。

部署专题说明见 [frontend/DEPLOY.md](frontend/DEPLOY.md)。

## 常见问题

### 端口被占用

一键启动脚本会自动跳过已监听端口。如果服务异常但端口仍占用，先关闭对应窗口或进程，再重新运行 `.\start-all.bat`。

### 前端能打开但接口失败

检查：

- `http://127.0.0.1:8001/api/system/status`
- Vite 是否在 5173 运行。
- `frontend/vite.config.js` 中 `/api` 代理是否指向 8001。
- Nginx 部署时 `/api` 是否正确代理。

### 图层或瓦片失败

检查：

- `http://127.0.0.1:8080/geoserver`
- `GEOSERVER_URL`、`GEOSERVER_USER`、`GEOSERVER_PASS`、`GEOSERVER_WORKSPACE`
- Nginx 或 Vite 的 `/geoserver` 代理

### 后端启动但数据库显示离线

检查 `DATABASE_URL`、PostgreSQL 服务、数据库名和账号密码。后端会在数据库不可用时跳过建表，但依赖任务/边界持久化的功能会受影响。

### ngrok 外网访问

```powershell
.\start-all.bat -WithNgrok
```

Vite 已允许 `.ngrok-free.dev` host。生产或长期共享环境应使用正式域名和 Nginx/HTTPS。
