# RS Urban Monitor 前端镜像（两阶段构建）
# build context = 项目根目录（vite root 在根目录，见 vite.config.js）
#
# 阶段 1：node 编译出 dist/
# 阶段 2：nginx 托管静态文件 + 反代后端

# ==================== 阶段 1：构建 ====================
FROM node:20-alpine AS build
WORKDIR /app

# 先复制依赖清单（利用 layer 缓存）
COPY package.json ./
COPY package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# vite root = 项目根，需要 index.html + src/ + frontend/vite.config.js
COPY index.html ./
COPY src/ src/
COPY frontend/ frontend/

# 注入 Vite 构建时环境变量（Mapbox token 等），envDir = 项目根（/app）
COPY frontend/.env .env

# 构建 → /app/dist
RUN npm run build

# ==================== 阶段 2：nginx 托管 ====================
# nginx-unprivileged 默认以非 root 的 nginx 用户运行，监听 8080（非特权端口）
FROM nginxinc/nginx-unprivileged:alpine

# 清除 nginx 默认配置
RUN rm /etc/nginx/conf.d/default.conf

# 拷贝构建产物
COPY --from=build /app/dist /usr/share/nginx/html

# 拷贝 Docker 专用 nginx 配置
COPY frontend/nginx.docker.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
# nginx-unprivileged 镜像自带 entrypoint，无需手动 CMD
