/**
 * GDP distribution template.
 * Uses Kummu et al. (2025) gridded GDP per capita dataset.
 * Asset: projects/sat-io/open-datasets/GRIDDED_HDI_GDP/adm2_gdp_perCapita_1990_2022
 * Band: PPP_YYYY (PPP, constant 2021 USD, 30 arc-sec ~1km)
 */

export function gdpTemplate(params) {
  const { timePeriods } = params

  let code = `
// ========== GDP 分布数据提取 ==========
// 使用 Kummu et al. (2025) Gridded GDP per capita (PPP, constant 2021 USD)
// 数据源: projects/sat-io/open-datasets/GRIDDED_HDI_GDP/adm2_gdp_perCapita_1990_2022
// 波段: PPP_YYYY (覆盖 1990-2022)

function extractGDP(year, boundary) {
  if (year < 1990 || year > 2022) {
    print('GDP 数据仅覆盖 1990-2022，年份 ' + year + ' 不可用');
    return ee.Image.constant(0).rename('GDP_per_capita');
  }
  var gdpImg = ee.Image(
    'projects/sat-io/open-datasets/GRIDDED_HDI_GDP/adm2_gdp_perCapita_1990_2022'
  );
  return gdpImg.select('PPP_' + year).clip(boundary).rename('GDP_per_capita');
}
`

  const yearCalls = timePeriods.map(year =>
    `var gdp_${year} = extractGDP(${year}, boundary);`
  ).join('\n')

  code += `\n// 生成 GDP 影像\n${yearCalls}\n`

  return code
}
