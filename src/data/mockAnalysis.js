import { STUDY_AREA } from './districts.js'

const expansionData = {
  totalArea: 1285.6,
  patches: 2340,
  patchesDesc: '基于建设用地面积与平均斑块尺度（0.5 km²）的比值计算',
  avgPatchSize: 0.55,
  expansionRate: 3.42,
  modeDistribution: [
    { name: '边缘扩张', value: 44.8, color: '#FF6B6B' },
    { name: '填充式扩张', value: 32.5, color: '#FFD43B' },
    { name: '飞地式扩张', value: 22.7, color: '#4DABF7' },
  ],
  // Pick representative cities from each province
  districtRanking: [
    { name: '上海市', value: 85.3, center: [121.47, 31.23] },
    { name: '苏州市', value: 62.4, center: [120.59, 31.30] },
    { name: '杭州市', value: 54.8, center: [120.15, 30.28] },
    { name: '南京市', value: 46.2, center: [118.80, 32.06] },
    { name: '宁波市', value: 38.6, center: [121.54, 29.87] },
    { name: '合肥市', value: 32.5, center: [117.23, 31.82] },
    { name: '无锡市', value: 28.7, center: [120.30, 31.57] },
    { name: '南通市', value: 24.1, center: [120.89, 31.98] },
  ],
}

const ecologyData = {
  rseiMean: 0.55,
  rseiChange: -0.08,
  gradeDistribution: [
    { grade: '优', area: 820, color: '#2B8A3E' },
    { grade: '良', area: 1480, color: '#69DB7C' },
    { grade: '中', area: 1100, color: '#FFD43B' },
    { grade: '较差', area: 580, color: '#FF922B' },
    { grade: '差', area: 260, color: '#FF6B6B' },
  ],
  trendData: [
    { year: 2000, value: 0.66 },
    { year: 2005, value: 0.63 },
    { year: 2010, value: 0.60 },
    { year: 2015, value: 0.57 },
    { year: 2020, value: 0.55 },
  ],
  changeDistribution: [
    { name: '明显改善', area: 180, color: '#2B8A3E' },
    { name: '轻微改善', area: 450, color: '#69DB7C' },
    { name: '基本不变', area: 1900, color: '#FFD43B' },
    { name: '轻微退化', area: 720, color: '#FF922B' },
    { name: '明显退化', area: 320, color: '#FF6B6B' },
  ],
}

const reportData = {
  studyArea: STUDY_AREA.name,
  timeRange: '2000-2020',
  expansionTable: [
    { district: '上海市', newArea: 85.3, rate: 4.5, intensity: 0.94, mode: '边缘扩张' },
    { district: '苏州市', newArea: 62.4, rate: 4.0, intensity: 0.88, mode: '边缘扩张' },
    { district: '杭州市', newArea: 54.8, rate: 3.8, intensity: 0.82, mode: '填充式' },
    { district: '南京市', newArea: 46.2, rate: 3.4, intensity: 0.75, mode: '填充式' },
    { district: '宁波市', newArea: 38.6, rate: 3.1, intensity: 0.70, mode: '边缘扩张' },
    { district: '合肥市', newArea: 32.5, rate: 2.9, intensity: 0.65, mode: '边缘扩张' },
    { district: '无锡市', newArea: 28.7, rate: 2.6, intensity: 0.60, mode: '填充式' },
    { district: '南通市', newArea: 24.1, rate: 2.3, intensity: 0.55, mode: '飞地式' },
  ],
  ecologyTable: [
    { grade: '优', area: 820, percent: 19.3, change: '-3.2%' },
    { grade: '良', area: 1480, percent: 34.8, change: '-2.8%' },
    { grade: '中', area: 1100, percent: 25.9, change: '+0.5%' },
    { grade: '较差', area: 580, percent: 13.6, change: '+2.1%' },
    { grade: '差', area: 260, percent: 6.1, change: '+1.9%' },
  ],
  modeDistribution: expansionData.modeDistribution,
  districtRanking: expansionData.districtRanking,
  rseiTrend: ecologyData.trendData,
  ecologyGradeDistribution: ecologyData.gradeDistribution,
  scatterData: [
    [4.5, -0.12, '上海市'],
    [4.0, -0.09, '苏州市'],
    [3.8, -0.08, '杭州市'],
    [3.4, -0.06, '南京市'],
    [3.1, -0.07, '宁波市'],
    [2.9, -0.05, '合肥市'],
    [2.6, -0.03, '无锡市'],
    [2.3, -0.02, '南通市'],
  ],
}

// ========== 热点乡镇数据 (2.2.2-4) ==========
const hotspotData = [
  { name: '松江区', city: '上海市', center: [121.23, 31.03], value: 4.2, type: 'hot' },
  { name: '昆山市', city: '苏州市', center: [120.98, 31.38], value: 3.8, type: 'hot' },
  { name: '余杭区', city: '杭州市', center: [120.30, 30.42], value: 3.5, type: 'hot' },
  { name: '嘉定区', city: '上海市', center: [121.27, 31.38], value: 3.3, type: 'hot' },
  { name: '江宁区', city: '南京市', center: [118.84, 31.95], value: 3.1, type: 'hot' },
  { name: '慈溪市', city: '宁波市', center: [121.24, 30.17], value: 2.8, type: 'hot' },
  { name: '江阴市', city: '无锡市', center: [120.26, 31.91], value: 2.6, type: 'hot' },
  { name: '肥西县', city: '合肥市', center: [117.17, 31.72], value: 2.4, type: 'hot' },
  { name: '浦口区', city: '南京市', center: [118.63, 32.06], value: -1.2, type: 'cold' },
  { name: '崇明区', city: '上海市', center: [121.40, 31.62], value: -1.8, type: 'cold' },
  { name: '临安区', city: '杭州市', center: [119.72, 30.23], value: -2.1, type: 'cold' },
  { name: '高淳区', city: '南京市', center: [118.87, 31.32], value: -2.5, type: 'cold' },
  { name: '安吉县', city: '湖州市', center: [119.68, 30.63], value: -2.8, type: 'cold' },
  { name: '建德市', city: '杭州市', center: [119.28, 29.48], value: -3.1, type: 'cold' },
]

// ========== RSEI 雷达图数据 (2.2.3-1) ==========
const radarData = [
  { city: '上海市', ndvi: 0.52, wet: 0.48, ndbsi: 0.65, lst: 0.72 },
  { city: '南京市', ndvi: 0.68, wet: 0.55, ndbsi: 0.45, lst: 0.58 },
  { city: '杭州市', ndvi: 0.75, wet: 0.62, ndbsi: 0.35, lst: 0.50 },
  { city: '苏州市', ndvi: 0.55, wet: 0.58, ndbsi: 0.60, lst: 0.68 },
  { city: '宁波市', ndvi: 0.62, wet: 0.53, ndbsi: 0.50, lst: 0.55 },
  { city: '合肥市', ndvi: 0.58, wet: 0.45, ndbsi: 0.55, lst: 0.65 },
  { city: '无锡市', ndvi: 0.60, wet: 0.52, ndbsi: 0.52, lst: 0.60 },
  { city: '南通市', ndvi: 0.50, wet: 0.55, ndbsi: 0.58, lst: 0.62 },
]

// ========== 乡镇排名表 (2.2.3-4) ==========
const townshipRanking = [
  { rank: 1, name: '临安区', city: '杭州市', rsei: 0.82, change: '↑ 0.05', trend: 'up' },
  { rank: 2, name: '安吉县', city: '湖州市', rsei: 0.78, change: '↑ 0.03', trend: 'up' },
  { rank: 3, name: '高淳区', city: '南京市', rsei: 0.76, change: '↑ 0.04', trend: 'up' },
  { rank: 4, name: '建德市', city: '杭州市', rsei: 0.74, change: '↑ 0.02', trend: 'up' },
  { rank: 5, name: '浦口区', city: '南京市', rsei: 0.72, change: '→ 0.00', trend: 'flat' },
  { rank: 24, name: '浦东新区', city: '上海市', rsei: 0.38, change: '↓ -0.06', trend: 'down' },
  { rank: 25, name: '昆山市', city: '苏州市', rsei: 0.35, change: '↓ -0.08', trend: 'down' },
  { rank: 26, name: '慈溪市', city: '宁波市', rsei: 0.32, change: '↓ -0.09', trend: 'down' },
  { rank: 27, name: '松江区', city: '上海市', rsei: 0.28, change: '↓ -0.11', trend: 'down' },
  { rank: 28, name: '嘉定区', city: '上海市', rsei: 0.24, change: '↓ -0.12', trend: 'down' },
]

// ========== 城市指标总览 (Dashboard) ==========
const overviewData = {
  totalCities: 27,
  totalConstruction: 1285.6,
  avgExpansionRate: 3.42,
  avgRSEI: 0.55,
  hotspotCount: 8,
  coldspotCount: 6,
  improvedArea: 630,
  degradedArea: 1040,
}

// ========== 城市完整数据表 (2.2.2-2) ==========
const cityTableData = [
  { name: '上海市', province: '上海', newArea: 85.3, rate: 4.5, intensity: 0.94, mode: '边缘扩张', rsei: 0.48, rseiChange: -0.10, pop: 2487, gdp: 47200 },
  { name: '南京市', province: '江苏', newArea: 46.2, rate: 3.4, intensity: 0.75, mode: '填充式', rsei: 0.62, rseiChange: -0.05, pop: 949, gdp: 17400 },
  { name: '无锡市', province: '江苏', newArea: 28.7, rate: 2.6, intensity: 0.60, mode: '填充式', rsei: 0.58, rseiChange: -0.03, pop: 748, gdp: 15500 },
  { name: '常州市', province: '江苏', newArea: 15.3, rate: 1.8, intensity: 0.48, mode: '边缘扩张', rsei: 0.65, rseiChange: -0.01, pop: 536, gdp: 10100 },
  { name: '苏州市', province: '江苏', newArea: 62.4, rate: 4.0, intensity: 0.88, mode: '边缘扩张', rsei: 0.52, rseiChange: -0.08, pop: 1284, gdp: 24600 },
  { name: '南通市', province: '江苏', newArea: 24.1, rate: 2.3, intensity: 0.55, mode: '飞地式', rsei: 0.60, rseiChange: -0.02, pop: 774, gdp: 11800 },
  { name: '杭州市', province: '浙江', newArea: 54.8, rate: 3.8, intensity: 0.82, mode: '填充式', rsei: 0.68, rseiChange: -0.07, pop: 1220, gdp: 21800 },
  { name: '宁波市', province: '浙江', newArea: 38.6, rate: 3.1, intensity: 0.70, mode: '边缘扩张', rsei: 0.55, rseiChange: -0.06, pop: 954, gdp: 16400 },
  { name: '温州市', province: '浙江', newArea: 22.3, rate: 2.2, intensity: 0.52, mode: '边缘扩张', rsei: 0.70, rseiChange: -0.02, pop: 967, gdp: 8700 },
  { name: '合肥市', province: '安徽', newArea: 32.5, rate: 2.9, intensity: 0.65, mode: '边缘扩张', rsei: 0.56, rseiChange: -0.05, pop: 963, gdp: 13500 },
  { name: '芜湖市', province: '安徽', newArea: 18.2, rate: 2.0, intensity: 0.50, mode: '填充式', rsei: 0.63, rseiChange: -0.03, pop: 367, gdp: 4800 },
]

function clone(data) {
  return JSON.parse(JSON.stringify(data))
}

export function getExpansionData() { return clone(expansionData) }
export function getEcologyData() { return clone(ecologyData) }
export function getReportData() { return clone(reportData) }
export function getHotspotData() { return clone(hotspotData) }
export function getRadarData() { return clone(radarData) }
export function getTownshipRanking() { return clone(townshipRanking) }
export function getOverviewData() { return clone(overviewData) }
export function getCityTableData() { return clone(cityTableData) }
