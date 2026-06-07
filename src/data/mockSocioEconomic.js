const socioEconomicData = {
  population: {
    total: 16850,
    growth: 2.5,
    density: 470,
    urbanRate: 68.2,
  },
  gdp: {
    total: 32.8,
    growth: 6.8,
    perCapita: 19.5,
    structure: [
      { name: '第一产业', value: 3.2, color: '#69DB7C' },
      { name: '第二产业', value: 41.5, color: '#4DABF7' },
      { name: '第三产业', value: 55.3, color: '#FF6B6B' },
    ],
  },
  districtPopulation: [
    { name: '上海市', value: 2487, center: [121.47, 31.23] },
    { name: '杭州市', value: 1220, center: [120.15, 30.28] },
    { name: '苏州市', value: 1284, center: [120.59, 31.30] },
    { name: '南京市', value: 949, center: [118.80, 32.06] },
    { name: '合肥市', value: 963, center: [117.23, 31.82] },
    { name: '宁波市', value: 954, center: [121.54, 29.87] },
    { name: '温州市', value: 967, center: [120.70, 28.00] },
    { name: '南通市', value: 774, center: [120.89, 31.98] },
  ],
  districtGdp: [
    { name: '上海市', value: 47200, center: [121.47, 31.23] },
    { name: '苏州市', value: 24600, center: [120.59, 31.30] },
    { name: '杭州市', value: 21800, center: [120.15, 30.28] },
    { name: '南京市', value: 17400, center: [118.80, 32.06] },
    { name: '宁波市', value: 16400, center: [121.54, 29.87] },
    { name: '合肥市', value: 13500, center: [117.23, 31.82] },
    { name: '无锡市', value: 15500, center: [120.30, 31.57] },
    { name: '南通市', value: 11800, center: [120.89, 31.98] },
  ],
  correlationData: [
    { expansionRate: 4.5, gdpGrowth: 8.2, populationGrowth: 3.8, name: '上海市', center: [121.47, 31.23] },
    { expansionRate: 4.0, gdpGrowth: 7.5, populationGrowth: 3.5, name: '苏州市', center: [120.59, 31.30] },
    { expansionRate: 3.8, gdpGrowth: 7.8, populationGrowth: 3.2, name: '杭州市', center: [120.15, 30.28] },
    { expansionRate: 3.4, gdpGrowth: 6.5, populationGrowth: 2.8, name: '南京市', center: [118.80, 32.06] },
    { expansionRate: 3.1, gdpGrowth: 7.0, populationGrowth: 2.5, name: '宁波市', center: [121.54, 29.87] },
    { expansionRate: 2.9, gdpGrowth: 6.8, populationGrowth: 3.0, name: '合肥市', center: [117.23, 31.82] },
    { expansionRate: 2.6, gdpGrowth: 5.8, populationGrowth: 2.2, name: '无锡市', center: [120.30, 31.57] },
    { expansionRate: 2.3, gdpGrowth: 5.5, populationGrowth: 1.9, name: '南通市', center: [120.89, 31.98] },
  ],
}

function clone(data) {
  return JSON.parse(JSON.stringify(data))
}

export function getSocioEconomicData() {
  return clone(socioEconomicData)
}
