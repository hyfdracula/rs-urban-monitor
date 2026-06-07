# 城市扩张与生态环境遥感监测系统 — 技术方案

## 1. 开发技术栈

### 前端
| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 框架 | Vue 3 (Composition API) | 3.x | 组件化页面构建，响应式数据绑定 |
| 构建工具 | Vite | 8.x | 极速开发服务器，ESM 原生打包 |
| 路由 | Vue Router | 4.x | 单页应用多页面路由（总览/扩张/生态/报告） |
| UI 组件库 | Element Plus | 2.x | 暗色主题表格、开关、按钮、导航等 |
| 地图引擎 | Mapbox GL JS | 3.x | WebGL 高性能底图渲染，矢量/栅格图层叠加 |
| 图表库 | ECharts | 5.x | 饼图、柱状图、折线图、散点图、热力图 |
| HTTP 客户端 | Axios | 1.x | 请求 GeoServer REST API / WFS 数据 |

### 后端/数据服务
| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 地图服务器 | GeoServer | 2.25.x | 发布 GeoTIFF 为 WMS/WMTS 标准地图服务 |
| 瓦片缓存 | GeoWebCache | 内置 | 加速瓦片请求，减少重复渲染 |
| 遥感处理 | Python + GDAL | — | 辐射定标、大气校正、几何校正等预处理 |
| 空间分析 | ArcPy / QGIS | — | 叠置分析、空间统计、热点分析 |

### 开发环境
| 工具 | 说明 |
|------|------|
| 运行环境 | Node.js 24.15 + Java OpenJDK 17 |
| 包管理 | npm |
| 操作系统 | Windows 11 |
| 浏览器 | Chrome / Edge（需 WebGL 支持） |

---

## 2. 技术选型原则

**按优先级排序：**

1. **稳定性优先** — GeoServer 作为业界标准 OGC 地图服务器，WMS/WMTS 协议成熟稳定，全球 GIS 行业广泛使用
2. **低耦合架构** — 前后端通过标准 WMS 协议解耦，前端不直接处理 GeoTIFF，数据格式变更不影响前端
3. **国产生态友好** — Vue 3 中文文档完善，Element Plus 国内使用广泛，ECharts 百度开源，团队上手快
4. **展示效果好** — Mapbox GL 暗色底图 + WebGL 渲染，视觉效果优于 Leaflet
5. **免费可部署** — Mapbox 免费额度 5 万次/月，GeoServer 开源免费，无授权费用

**为什么不用其他方案：**

| 方案 | 拒绝原因 |
|------|----------|
| Leaflet | 不支持 WebGL，栅格瓦片性能不如 Mapbox |
| GeoTIFF.js 前端渲染 | 客户端算力要求高，大范围研究区加载慢 |
| ArcGIS Server | 商业授权费用高，部署复杂 |
| Cesium.js | 3D 地球对二维分析场景过重，学习成本高 |
| React | Vue 生态国内更友好，Element Plus 开箱即用 |

---

## 3. 总体技术架构

```
┌─────────────────────────────────────────────────────────┐
│                     用户浏览器                           │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Vue 3 单页应用                        │  │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────────────┐   │  │
│  │  │Mapbox GL│ │ ECharts  │ │ Element Plus     │   │  │
│  │  │地图渲染 │ │ 图表面板 │ │ UI 组件          │   │  │
│  │  └────┬────┘ └──────────┘ └──────────────────┘   │  │
│  └───────┼───────────────────────────────────────────┘  │
└──────────┼──────────────────────────────────────────────┘
           │ WMS 瓦片请求 / WFS 属性查询
           ▼
┌─────────────────────────────────────────────────────────┐
│                   GeoServer 地图服务                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐      │
│  │  WMS 服务 │  │ GeoWebCache│  │  REST API       │      │
│  │  动态出图 │  │  瓦片缓存  │  │  工作区/图层管理 │      │
│  └─────┬────┘  └──────────┘  └──────────────────┘      │
└────────┼───────────────────────────────────────────────┘
         │ 读取 GeoTIFF / Shapefile
         ▼
┌─────────────────────────────────────────────────────────┐
│                   数据存储层                              │
│  ┌──────────┐  ┌────────────┐  ┌──────────────────┐    │
│  │ GeoTIFF  │  │ Shapefile  │  │ 统计表格 (CSV)   │    │
│  │ 遥感栅格 │  │  矢量边界  │  │  多源统计数据     │    │
│  └──────────┘  └────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────┘
         ▲
         │ 数据预处理产出
         │
┌─────────────────────────────────────────────────────────┐
│                  遥感数据处理（Python）                    │
│  辐射定标 → 大气校正 → 几何精校正 → 研究区裁剪            │
│  NDVI/WET/NDBSI/LST 计算 → PCA → RSEI 合成              │
│  建设用地提取 → 叠加分析 → 扩张模式分类 → 空间统计         │
└─────────────────────────────────────────────────────────┘
```

---

## 4. 前端技术栈详解

### 4.1 页面结构

```
App.vue (主布局)
├── 顶部导航栏（Logo + 菜单路由）
└── <router-view>
    ├── HomeView.vue       总览 — 地图 + 图层控制 + 时间轴
    ├── ExpansionView.vue  扩张分析 — 地图 + 统计面板 + 图表
    ├── EcologyView.vue    生态评估 — 地图 + RSEI面板
    └── ReportView.vue     分析报告 — 图表汇总 + 表格 + 导出
```

### 4.2 组件树

```
App.vue
├── MapViewer.vue          地图核心，封装 Mapbox GL
│   └── 方法: addWmsLayer / removeLayer / flyTo / fitBounds
├── LayerControl.vue       图层开关面板（建设/RSEI/灯光/人口/GDP）
├── TimelineSelector.vue   2000-2020 时间轴选择器
├── ExpansionStats.vue     扩张统计卡片 + 模式饼图 + 区县排名柱状图
├── EcologyStats.vue       RSEI统计 + 等级柱状图 + 趋势折线图 + 变化饼图
└── (ReportView 内嵌图表)   5 个 ECharts 实例
```

### 4.3 数据流

```
GeoServer WMS (栅格瓦片)
  → MapViewer addWmsLayer()
  → Mapbox raster source → raster layer → Canvas 渲染

GeoServer WFS (属性数据)
  → axios 请求 → JSON 解析 → ECharts dataset
  → 图表渲染

用户交互
  → TimelineSelector emit('change') → 页面更新 year/comparYear
  → LayerControl emit('layer-toggle') → MapViewer 切换图层
```

### 4.4 关键配置

```javascript
// config/map.js
MAPBOX_TOKEN   → Mapbox 访问令牌
GEOSERVER_CONFIG → GeoServer WMS URL + workspace
TIME_PERIODS   → [2000, 2005, 2010, 2015, 2020]
LAYER_CONFIG   → 9 类图层定义（建设/RSEI/灯光/人口/GDP/扩张/模式/变化/热点）
RSEI_GRADES    → 优/良/中/较差/差 五级配色
```

---

## 5. 后端方案

### 5.1 数据处理管线（Python）

```
输入: Landsat/Sentinel 多光谱影像 L1 级产品

步骤:
1. 辐射定标 (Radiometric Calibration) → 表观反射率
2. 大气校正 (Atmospheric Correction)  → 地表反射率
3. 几何精校正 (Geometric Correction) → 精度 < 1 像元
4. 研究区裁剪 (Subset by ROI)        → 减少数据量

输出: 地表反射率产品 → GeoTIFF (EPSG:4326 / Web Mercator)

指标计算:
• NDVI  = (NIR - Red) / (NIR + Red)           → 绿度
• WET   = Tasseled Cap 湿度分量               → 湿度
• NDBSI = (SI + IBI) / 2                      → 干度
• LST   = 单窗/劈窗算法反演                    → 热度
• RSEI  = PCA(归一化 NDVI, WET, NDBSI, LST)   → 遥感生态指数

建设用地提取:
• Landsat → CART/SVM 分类
• 夜间灯光 → 阈值法提取建成区
• 叠加分析 → 新增斑块、扩张模式分类
```

### 5.2 GeoServer 配置

```
Workspace: rs_urban

图层命名规范:
├── construction_land_2000  (建设用地)
├── construction_land_2005
├── construction_land_2010
├── construction_land_2015
├── construction_land_2020
├── rsei_2000               (遥感生态指数)
├── rsei_2005 / 2010 / 2015 / 2020
├── ntl_2000                (夜间灯光)
├── ntl_2005 / 2010 / 2015 / 2020
├── population_2000         (人口密度)
├── population_2005 / 2010 / 2015 / 2020
├── gdp_2000                (GDP)
├── gdp_2005 / 2010 / 2015 / 2020
├── expansion_mode_edge      (边缘扩张)
├── expansion_mode_infill    (填充式扩张)
├── expansion_mode_leapfrog  (飞地式扩张)
└── hotspot_*                (热点/冷点)
```

### 5.3 迁移路径

| 阶段 | 部署方式 | GeoServer 地址 |
|------|----------|---------------|
| 开发 | 本地 Windows GeoServer | `http://127.0.0.1:8080/geoserver` |
| 展示 | 本地 + 局域网 | 同上 |
| 长期 | NAS Docker GeoServer | `http://NAS_IP:8080/geoserver` |
| 正式 | 云服务器 | `https://domain.com/geoserver` |

迁移只需修改前端 `config/map.js` 中一行 GeoServer URL。

---

## 6. 开发环境

| 项目 | 信息 |
|------|------|
| 项目路径 | `C:\Users\19161\Desktop\rs-urban-monitor\` |
| GeoServer 路径 | `C:\Users\19161\Desktop\geoserver-2.25.5-bin\` |
| Node.js | `D:\software\node\` (v24.15.0) |
| Java | `C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot\` (OpenJDK 17) |
| 前端端口 | 5173 |
| GeoServer 端口 | 8080 |
| 一键启动 | `start-all.bat` |

**启动命令：** 双击 `start-all.bat`

**登录信息：**
- GeoServer 管理页：`admin` / `geoserver`
