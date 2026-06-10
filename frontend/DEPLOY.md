# RS Urban Monitor — 部署指南

## 一、构建

```bash
npm install
npm run build
```

产出 `dist/` 目录。

## 二、部署到 Nginx

### Linux / WSL

```bash
# 1. 建目录，扔文件
sudo mkdir -p /var/www/rs-urban-monitor
sudo cp -r dist/* /var/www/rs-urban-monitor/dist/

# 2. 装 Nginx
sudo apt install nginx

# 3. 拷贝配置
sudo cp nginx.conf /etc/nginx/sites-available/rs-urban
sudo ln -s /etc/nginx/sites-available/rs-urban /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default   # 去掉默认站点

# 4. 检查 & 重载
sudo nginx -t
sudo systemctl reload nginx
```

访问 `http://localhost`。

### Windows (Nginx for Windows)

```powershell
# 1. 下载 nginx Windows 版: https://nginx.org/en/download.html
# 2. 解压到 C:\nginx
# 3. 把 dist/ 放到 C:\nginx\html\rs-urban\
# 4. 替换 C:\nginx\conf\nginx.conf 为本项目的 nginx.conf
#    注意: 改 root 路径为 C:/nginx/html/rs-urban/dist
# 5. 启动:
cd C:\nginx
start nginx

# 重启:
nginx -s reload
```

访问 `http://localhost`。

### Docker (通用)

```bash
docker run -d \
  --name rs-urban-web \
  -v $(pwd)/dist:/usr/share/nginx/html:ro \
  -v $(pwd)/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
  -p 80:80 \
  nginx:alpine
```

## 三、前置条件

- **GeoServer** 必须运行在 `127.0.0.1:8080`，Nginx 通过 `/geoserver` 反向代理
- **Mapbox Token** 已在构建时打包到 JS 中，无需额外配置

## 四、验证

1. 浏览器打开 `http://localhost` → 能看到前端页面
2. 打开 `http://localhost/geoserver` → 能看到 GeoServer 管理页
3. 切换图层 → WMS 瓦片正常加载
