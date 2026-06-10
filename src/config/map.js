// GeoServer and Mapbox configuration
export const MAPBOX_TOKEN = (import.meta.env?.VITE_MAPBOX_TOKEN) || 'pk.eyJ1IjoiaHlmZHJhY3VsYSIsImEiOiJjbXEwaW1md2cwc2V5MnFwd2o3b2R3czB3In0.35FykW5Oi8riNHyvxAgqqQ'

// Vite proxy /geoserver → 127.0.0.1:8080 — 支持 ngrok/本地/LAN
const APP_ORIGIN = typeof window === 'undefined' ? 'http://127.0.0.1:5173' : window.location.origin

export const GEOSERVER_CONFIG = {
  baseUrl: APP_ORIGIN + '/geoserver',
  workspace: 'ueea2601',
  wmsUrl: APP_ORIGIN + '/geoserver/ueea2601/wms',
  tmsUrl: APP_ORIGIN + '/geoserver/gwc/service/tms/1.0.0',
}

// Study area center — 长三角城市群核心区27市
export const MAP_CENTER = [119.0, 30.8]
export const MAP_ZOOM = 7
export const MAP_BOUNDS = [
  [116.0, 27.5], // SW
  [123.0, 33.8], // NE
]

// Time periods for analysis (2000-2020, 5-year intervals)
export const TIME_PERIODS = [2000, 2005, 2010, 2015, 2020]

// Layer definitions for GeoServer WMS layers
export const LAYER_CONFIG = {
  // Construction land layers
  constructionLand: {
    id: 'construction-land',
    name: '建设用地分布',
    layers: TIME_PERIODS.map(year => ({
      year,
      layerName: year === 2020 ? 'test_construction_2020' : `construction_land_${year}`,
      visible: false,
    })),
    color: '#FF6B6B',
    icon: 'OfficeBuilding',
  },
  // Urban expansion layers
  urbanExpansion: {
    id: 'urban-expansion',
    name: '新增建设用地',
    layers: [],
    color: '#FFA94D',
    icon: 'Expand',
  },
  // Expansion mode layers (edge/infill/leapfrog)
  expansionMode: {
    id: 'expansion-mode',
    name: '扩张模式',
    layers: [],
    color: '#69DB7C',
    icon: 'Share',
    modes: [
      { key: 'edge', name: '边缘扩张', color: '#FF6B6B' },
      { key: 'infill', name: '填充式扩张', color: '#FFD43B' },
      { key: 'leapfrog', name: '飞地式扩张', color: '#4DABF7' },
    ],
  },
  // RSEI layers
  rsei: {
    id: 'rsei',
    name: '遥感生态指数',
    layers: TIME_PERIODS.map(year => ({
      year,
      layerName: year === 2020 ? 'test_rsei_2020' : `rsei_${year}`,
      visible: false,
    })),
    color: '#51CF66',
    icon: 'Sunny',
  },
  // RSEI change detection
  rseiChange: {
    id: 'rsei-change',
    name: '生态变化检测',
    layers: [],
    color: '#20C997',
    icon: 'Switch',
  },
  // Hotspot analysis
  hotspot: {
    id: 'hotspot',
    name: '扩张热点',
    layers: [],
    color: '#FF922B',
    icon: 'Position',
  },
  // Nighttime light
  nightLight: {
    id: 'night-light',
    name: '夜间灯光',
    layers: TIME_PERIODS.map(year => ({
      year,
      layerName: `ntl_${year}`,
      visible: false,
    })),
    color: '#BE4BDB',
    icon: 'MoonNight',
  },
  // Population density
  population: {
    id: 'population',
    name: '人口密度',
    layers: TIME_PERIODS.map(year => ({
      year,
      layerName: `population_${year}`,
      visible: false,
    })),
    color: '#748FFC',
    icon: 'User',
  },
  // GDP
  gdp: {
    id: 'gdp',
    name: 'GDP分布',
    layers: TIME_PERIODS.map(year => ({
      year,
      layerName: `gdp_${year}`,
      visible: false,
    })),
    color: '#F783AC',
    icon: 'TrendCharts',
  },
}

// RSEI grade classification
export const RSEI_GRADES = [
  { key: 'excellent', name: '优', color: '#2B8A3E', range: [0.8, 1.0] },
  { key: 'good', name: '良', color: '#69DB7C', range: [0.6, 0.8] },
  { key: 'moderate', name: '中', color: '#FFD43B', range: [0.4, 0.6] },
  { key: 'poor', name: '较差', color: '#FF922B', range: [0.2, 0.4] },
  { key: 'bad', name: '差', color: '#FF6B6B', range: [0.0, 0.2] },
]

// Ecological change classification
export const ECO_CHANGE_CLASSES = [
  { key: 'significant_improve', name: '明显改善', color: '#2B8A3E' },
  { key: 'slight_improve', name: '轻微改善', color: '#69DB7C' },
  { key: 'stable', name: '基本不变', color: '#FFD43B' },
  { key: 'slight_degrade', name: '轻微退化', color: '#FF922B' },
  { key: 'significant_degrade', name: '明显退化', color: '#FF6B6B' },
]
