/**
 * Population density template.
 * WorldPop 1km gridded population.
 */

export function populationTemplate(params) {
  const { timePeriods } = params

  let code = `
// ========== 人口密度数据提取 ==========
// WorldPop 1km 栅格人口数据

function extractPopulation(year, boundary) {
  var pop = ee.ImageCollection("WorldPop/GP/100m/pop")
    .filterDate(ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year, 12, 31))
    .filterBounds(boundary)
    .mosaic()
    .clip(boundary);

  return pop.rename('population');
}
`

  const yearCalls = timePeriods.map(year =>
    `var population_${year} = extractPopulation(${year}, boundary);`
  ).join('\n')

  code += `\n// 生成人口密度影像\n${yearCalls}\n`

  return code
}
