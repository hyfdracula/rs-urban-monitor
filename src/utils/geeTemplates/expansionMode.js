/**
 * Urban expansion mode classification template.
 * Classifies new construction land into: edge, infill, leapfrog.
 */

export function expansionTemplate(params) {
  const { timePeriods } = params

  if (timePeriods.length < 2) {
    return '// 扩张模式分析需要至少 2 个时间节点，已跳过'
  }

  let code = `
// ========== 城市扩张模式分类 ==========
// 边缘扩张(Edge) / 填充式(Infill) / 飞地式(Leapfrog)

function classifyExpansionMode(earlyConstruction, lateConstruction, bufferDist) {
  bufferDist = bufferDist || 500; // 默认缓冲区 500m

  var newLand = lateConstruction.and(earlyConstruction.not())
    .rename('new_construction');

  // 已有建成区的缓冲区
  var existingBuffer = earlyConstruction.reduceNeighborhood({
    reducer: ee.Reducer.max(),
    kernel: ee.Kernel.circle(bufferDist, 'meters')
  });

  // 边缘扩张: 新增紧邻已有建成区
  var edge = newLand.and(existingBuffer);

  // 飞地式: 新增远离已有建成区
  var leapfrog = newLand.and(existingBuffer.not());

  // 填充式: 新增在已有建成区内部 (简化判断)
  var existingExpand = earlyConstruction.reduceNeighborhood({
    reducer: ee.Reducer.min(),
    kernel: ee.Kernel.circle(bufferDist * 0.5, 'meters')
  });
  var infill = newLand.and(existingExpand);

  // 合并为分类图: 1=边缘 2=填充 3=飞地
  var mode = edge.multiply(1)
    .add(infill.multiply(2))
    .add(leapfrog.multiply(3))
    .rename('expansion_mode');

  return mode.selfMask();
}
`

  // Generate pairwise comparisons
  const sorted = [...timePeriods].sort((a, b) => a - b)
  const comparisons = []
  for (let i = 0; i < sorted.length - 1; i++) {
    comparisons.push(`// ${sorted[i]} → ${sorted[i + 1]} 扩张模式
var expansion_mode_${sorted[i]}_${sorted[i + 1]} = classifyExpansionMode(
  construction_${sorted[i]}, construction_${sorted[i + 1]}
);`)
  }

  code += `\n// 逐期扩张模式分类\n${comparisons.join('\n\n')}\n`

  return code
}
