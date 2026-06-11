# 🐳 RS Urban Monitor — Docker 部署小白教程

> 本教程面向**完全没接触过 Docker** 的同学。
> 跟着做，10 分钟内把整个系统跑起来。

---

## 📋 这个项目是什么

一个「遥感城市监测系统」，包含 4 个部分：

| 部分 | 作用 | 技术 |
|------|------|------|
| 前端 | 你在浏览器看到的页面 | Vue 3 |
| 后端 | 处理数据、API | Python FastAPI |
| GeoServer | 地图服务 | Java |
| 数据库 | 存数据 | PostgreSQL + PostGIS |

**好消息**：这 4 个部分全部打包进 Docker，你**不用单独装** Python、Node.js、Java、PostgreSQL。只要装一个 Docker 就行。

---

## 🚀 第一步：装 Docker（只需一次）

### Windows 用户

1. 打开浏览器，访问 **https://www.docker.com/products/docker-desktop/**
2. 点 **Download for Windows**，下载安装包（约 500MB）
3. 双击安装，一路「下一步」
4. 安装完会提示**重启电脑**，重启
5. 重启后 Docker Desktop 会自动启动，任务栏右下角出现一个 🐳 鲸鱼图标，变绿就说明好了

> ⚠️ 如果安装时提示「需要启用 WSL 2」，按提示操作即可（一般是再点一下安装按钮）。
> 如果你的电脑比较老，可能要在 BIOS 里开启「虚拟化」——百度搜「电脑型号 + 开启虚拟化」。

### Mac 用户

1. 访问同一个下载页，选 **Download for Mac**
2. 根据你的芯片选 **Apple Silicon**（M1/M2/M3）或 **Intel**
3. 下载后是个 `.dmg`，打开，把鲸鱼图标拖进 Applications
4. 从启动台打开 Docker，等鲸鱼图标变绿

### Linux 用户

百度搜「Docker 官方安装 + 你的发行版」，或者直接：
```bash
curl -fsSL https://get.docker.com | sh
```

### ✅ 验证安装成功

打开「命令行」（Windows 按 `Win+R` 输入 `cmd`；Mac 打开「终端」），输入：

```bash
docker --version
```

看到类似 `Docker version 24.x.x` 就成功了 ✅

---

## 📦 第二步：拿到项目代码

假设你已经拿到了项目文件夹（比如别人传给你的压缩包，或从 Git 拉取）。

**重要**：记住这个项目的**完整路径**，比如：
- Windows：`C:\Users\你的名字\Desktop\rs-urban-monitor`
- Mac：`/Users/你的名字/Desktop/rs-urban-monitor`

---

## 🔧 第三步：配置密码（可选但推荐）

在项目**根目录**找到 `.env.example` 文件，复制一份改名为 `.env`：

**Windows 命令行**（在项目根目录执行）：
```bash
copy .env.example .env
```

**Mac / Linux**：
```bash
cp .env.example .env
```

然后用记事本打开 `.env`，按需修改密码：

```env
POSTGRES_DB=ueea2601
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres          # ← 改成你自己的数据库密码

GEOSERVER_ADMIN_PASSWORD=geoserver  # ← 改成你自己的 GeoServer 密码
```

> 💡 如果只是本地试用，不改也行，保持默认就行。

---

## 🏃 第四步：一键启动！（激动人心的时刻）

### 1. 打开命令行，进入项目目录

```bash
cd 你的项目路径
```

例如：
```bash
cd C:\Users\小明\Desktop\rs-urban-monitor
```

### 2. 启动所有服务

```bash
docker compose up -d --build
```

**这条命令在干嘛？**
- `docker compose up` —— 启动所有服务
- `-d` —— 后台运行（不占着命令行）
- `--build` —— 第一次运行要构建镜像（**约 5~15 分钟**，取决于网速，主要在下载依赖）

**耐心等**。你会看到一堆下载和构建的日志，这是正常的。中途别关窗口。

### 3. 看到类似这样就成功了 ✅

```
✔ Container rs-urban-monitor-db-1         Started
✔ Container rs-urban-monitor-geoserver-1  Started
✔ Container rs-urban-monitor-backend-1    Started
✔ Container rs-urban-monitor-frontend-1   Started
```

---

## 🌐 第五步：打开浏览器访问

等 30 秒让 GeoServer 完全启动，然后打开浏览器：

| 功能 | 网址 | 说明 |
|------|------|------|
| 🖥️ **系统主页** | http://localhost | 前端页面 |
| 📊 **后端健康检查** | http://localhost/api/system/status | 看到 JSON 数据就说明后端正常 |
| 🗺️ **GeoServer 管理台** | http://localhost/geoserver/web | 地图服务（账号 `admin`，密码见你的 `.env`） |

**打开 http://localhost，能看到系统界面就大功告成啦！** 🎉

---

## 🛠️ 常用命令速查

**所有命令都要在项目根目录下执行。**

### 看运行状态
```bash
docker compose ps
```

### 查看日志（出问题时看这个）
```bash
docker compose logs -f backend      # 看后端日志
docker compose logs -f frontend     # 看前端日志
docker compose logs -f              # 看所有日志
```
> 按 `Ctrl + C` 退出日志查看（不会停止服务）。

### 停止服务
```bash
docker compose stop
```

### 重新启动（不重新构建）
```bash
docker compose up -d
```

### 改了代码后重新构建
```bash
docker compose up -d --build
```

### 彻底停止并删除容器（数据保留）
```bash
docker compose down
```

### 彻底清空（连数据库数据一起删！慎用）
```bash
docker compose down -v
```
> `-v` 会删除数据库里所有数据。**确定要重置才用**。

---

## ❓ 常见问题排查

### Q1：启动报错 `port is already allocated`

**原因**：80 端口被别的程序占了（比如 IIS、Skype、其他 nginx）。

**解决**：改一下端口。编辑 `docker-compose.yml`，找到这行：
```yaml
ports:
  - "80:80"
```
改成（比如用 8080）：
```yaml
ports:
  - "8080:80"
```
然后访问 `http://localhost:8080`。

### Q2：页面打不开，一直转圈

**排查步骤**：
```bash
# 1. 看服务是不是都起来了
docker compose ps

# 2. 看后端有没有报错
docker compose logs backend
```

如果 backend 报数据库连接错误，可能是 GeoServer 还没启动完。等 1 分钟再刷新页面。

### Q3：GeoServer 第一次启动特别慢（2~5 分钟）

**正常现象**。GeoServer 是个 Java 程序，第一次要初始化很多东西。看日志：
```bash
docker compose logs -f geoserver
```
等到日志出现 `GeoServer started` 或类似字样就好了。

### Q4：`docker compose` 命令不存在

旧版 Docker 用的是 `docker-compose`（中间有横杠）。两个都试一下：
```bash
docker compose up -d --build      # 新版
docker-compose up -d --build      # 旧版
```
建议升级到新版 Docker Desktop。

### Q5：构建时下载特别慢 / 超时

国内网络问题。配置 Docker 镜像加速：
1. 打开 Docker Desktop → 设置（齿轮图标）→ **Docker Engine**
2. 在 JSON 配置里加上：
```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
```
3. 点 **Apply & Restart**，再重新执行 `docker compose up -d --build`

### Q6：想彻底重来

```bash
docker compose down -v        # 删除容器和数据
docker system prune -a        # 清理所有未用的镜像（会问你确认）
```
然后从第四步重新开始。

---

## 📁 项目结构速览（感兴趣可以看）

```
rs-urban-monitor/
├── docker-compose.yml      ← 总指挥，定义 4 个服务怎么配合
├── .env                    ← 你的密码配置（别提交到 Git）
├── .env.example            ← 密码模板
├── .dockerignore           ← 告诉 Docker 哪些文件别打包
│
├── backend/                ← 后端代码
│   ├── Dockerfile          ← 后端镜像怎么构建
│   └── ...
│
├── frontend/               ← 前端相关
│   ├── Dockerfile          ← 前端镜像怎么构建
│   ├── nginx.docker.conf   ← Docker 里的 nginx 配置
│   └── ...
│
└── src/                    ← Vue 前端源码
```

---

## 🆘 还是不行？

1. 先看日志：`docker compose logs`
2. 把**完整报错信息**截图发给我
3. 说明你用的系统（Windows/Mac/Linux）和操作到第几步

祝顺利~ 🎈
