/**
 * 长三角城市群 — 统一区划定义（27市）
 * 依据：《长江三角洲城市群发展规划》《长江三角洲地区区域规划》
 * 所有 mock 数据、图表、地图联动都引用这个文件
 * 换研究区只需改这一个文件
 */
export const STUDY_AREA = {
  name: '长三角城市群',
  fullName: '长三角城市群（核心区27市）',
  area: '35.8万平方公里',
  center: [119.0, 30.8],
  zoom: 7,
  bounds: [
    [116.0, 27.5], // SW
    [123.0, 33.8], // NE
  ],
}

export const DISTRICTS = [
  // 上海市
  { name: '上海市', center: [121.47, 31.23], province: '上海' },
  // 江苏省 9 市
  { name: '南京市', center: [118.80, 32.06], province: '江苏' },
  { name: '无锡市', center: [120.30, 31.57], province: '江苏' },
  { name: '常州市', center: [119.97, 31.81], province: '江苏' },
  { name: '苏州市', center: [120.59, 31.30], province: '江苏' },
  { name: '南通市', center: [120.89, 31.98], province: '江苏' },
  { name: '盐城市', center: [120.16, 33.35], province: '江苏' },
  { name: '扬州市', center: [119.42, 32.39], province: '江苏' },
  { name: '镇江市', center: [119.43, 32.19], province: '江苏' },
  { name: '泰州市', center: [119.92, 32.46], province: '江苏' },
  // 浙江省 9 市
  { name: '杭州市', center: [120.15, 30.28], province: '浙江' },
  { name: '宁波市', center: [121.54, 29.87], province: '浙江' },
  { name: '温州市', center: [120.70, 28.00], province: '浙江' },
  { name: '嘉兴市', center: [120.76, 30.75], province: '浙江' },
  { name: '湖州市', center: [120.09, 30.89], province: '浙江' },
  { name: '绍兴市', center: [120.58, 30.03], province: '浙江' },
  { name: '金华市', center: [119.65, 29.08], province: '浙江' },
  { name: '舟山市', center: [122.21, 30.02], province: '浙江' },
  { name: '台州市', center: [121.42, 28.66], province: '浙江' },
  // 安徽省 8 市
  { name: '合肥市', center: [117.23, 31.82], province: '安徽' },
  { name: '芜湖市', center: [118.43, 31.35], province: '安徽' },
  { name: '马鞍山市', center: [118.51, 31.67], province: '安徽' },
  { name: '铜陵市', center: [117.81, 30.93], province: '安徽' },
  { name: '安庆市', center: [117.05, 30.53], province: '安徽' },
  { name: '滁州市', center: [118.33, 32.30], province: '安徽' },
  { name: '池州市', center: [117.49, 30.66], province: '安徽' },
  { name: '宣城市', center: [118.76, 30.94], province: '安徽' },
]

/**
 * 根据名称获取城市坐标
 */
export function getDistrictCenter(name) {
  const d = DISTRICTS.find(d => d.name === name)
  return d ? d.center : STUDY_AREA.center
}
