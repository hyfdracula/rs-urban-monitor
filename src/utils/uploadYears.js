export const ALL_INDICATORS = ['rsei', 'construction', 'expansion', 'nightLight', 'population', 'gdp']

export function getLandsatSensor(year) {
  if (year >= 2021) return 'Landsat 9 OLI-2'
  if (year >= 2013) return 'Landsat 8 OLI'
  if (year >= 1999 && year <= 2003) return 'Landsat 7 ETM+'
  return 'Landsat 5 TM'
}

export function analyzeDataAvailability(years) {
  const warnings = []
  const sensorMap = {}

  years.forEach((year) => {
    sensorMap[year] = getLandsatSensor(year)
  })

  const noGDP = years.filter(year => year < 1990 || year > 2022)
  if (noGDP.length > 0) {
    warnings.push({
      type: 'error',
      icon: 'WarningFilled',
      title: 'GDP 数据缺失',
      detail: `年份 ${noGDP.join('、')} 无 GDP 数据（Kummu 数据集仅覆盖 1990-2022），GDP 相关指标将显示为"数据暂缺"`,
    })
  }

  const noPop = years.filter(year => year < 2000 || year > 2020)
  if (noPop.length > 0) {
    warnings.push({
      type: 'warning',
      icon: 'User',
      title: '人口数据缺失',
      detail: `年份 ${noPop.join('、')} 无 WorldPop 人口数据（仅 2000-2020 可用），人口指标将显示为 0`,
    })
  }

  const lt5Late = years.filter(year => year >= 2011 && year <= 2012)
  if (lt5Late.length > 0) {
    warnings.push({
      type: 'warning',
      icon: 'Warning',
      title: 'Landsat 5 数据质量风险',
      detail: `年份 ${lt5Late.join('、')} 使用 Landsat 5 TM，该卫星在 2011-2012 年出现放大器漂移，数据质量可能下降`,
    })
  }

  const sensors = [...new Set(Object.values(sensorMap))]
  if (sensors.length >= 2) {
    warnings.push({
      type: 'info',
      icon: 'InfoFilled',
      title: '跨传感器对比',
      detail: `所选年份涉及 ${sensors.length} 种传感器（${sensors.join('、')}），不同传感器的波段响应差异可能影响年际对比的一致性`,
    })
  }

  const le07 = years.filter(year => year >= 1999 && year <= 2003)
  if (le07.length > 0) {
    warnings.push({
      type: 'info',
      icon: 'InfoFilled',
      title: 'Landsat 7 ETM+ 说明',
      detail: `年份 ${le07.join('、')} 使用 Landsat 7 ETM+，2003年5月后存在 SLC-off 条纹，代码已用中值合成缓解`,
    })
  }

  const overlap = years.filter(year => year === 2012 || year === 2013)
  if (overlap.length > 0) {
    warnings.push({
      type: 'info',
      icon: 'InfoFilled',
      title: '夜灯数据源切换',
      detail: `年份 ${overlap.join('、')} 处于 DMSP-OLS → VIIRS 数据源切换期，夜灯指标可能存在断档`,
    })
  }

  return {
    warnings,
    sensorMap,
    hasBlocker: warnings.some(warning => warning.type === 'error'),
  }
}

export function getGdpWarning(years) {
  const noGDP = years.filter(year => year < 1990 || year > 2022)
  if (noGDP.length === 0) return ''
  return `年份 ${noGDP.join('、')} 无 GDP 数据，经济指标将显示为"数据暂缺"`
}

export function isDisabledYearDate(date, currentYear = new Date().getFullYear()) {
  const year = date.getFullYear()
  return year < 1984 || year > currentYear
}

export function addYearToSelection(years, value, currentYear = new Date().getFullYear(), maxYears = 5) {
  if (!value) return { years, warning: '' }

  const year = new Date(value).getFullYear()
  if (year < 1984 || year > currentYear) return { years, warning: '' }
  if (years.includes(year)) return { years, warning: '' }
  if (years.length >= maxYears) return { years, warning: `最多选择${maxYears}个年份` }

  return { years: [...years, year].sort(), warning: '' }
}

export function removeYearFromSelection(years, year) {
  return years.filter(value => value !== year)
}

export function quickPickYears(years) {
  return [...years]
}
