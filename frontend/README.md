# RS Urban Monitor 前端说明

前端采用 Vue 3 + Vite，源码实际位于项目根目录的 `src/`，Vite 配置位于 `frontend/vite.config.js`。

## 常用命令

在项目根目录执行：

```powershell
npm install
npm run dev
npm run build
npm test
npm run test:e2e
```

默认开发地址：

- 前端：`http://127.0.0.1:5173/`
- 后端代理：`/api -> http://127.0.0.1:8001`
- GeoServer 代理：`/geoserver -> http://127.0.0.1:8080`

## 一键启动

推荐直接使用根目录脚本：

```powershell
cd C:\Users\19161\Desktop\rs-urban-monitor
.\start-all.bat
```

前端目录下的 `start-all.bat` 只是转发到根目录启动器。

## 环境变量

前端变量从项目根目录 `.env` 读取：

```dotenv
VITE_MAPBOX_TOKEN=your_mapbox_public_token_here
VITE_USE_MAPBOX_STYLE=false
VITE_BASE=/
VITE_USE_API=true
```

`VITE_USE_MAPBOX_STYLE=false` 时使用本地离线深色底图；设置为 `true` 且提供 Mapbox token 后使用 Mapbox hosted style。

## 部署

构建产物输出到根目录 `dist/`：

```powershell
npm run build
```

部署说明见：

- 根目录主文档：[../README.md](../README.md)
- 前端/Nginx 专题：[DEPLOY.md](DEPLOY.md)
