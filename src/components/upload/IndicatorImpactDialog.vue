<template>
  <el-dialog
    v-model="visible"
    title="指标影响确认"
    width="520px"
    :close-on-click-modal="false"
    class="impact-dialog"
    :append-to-body="true"
  >
    <div class="impact-content">
      <div class="impact-header">
        <span class="impact-icon">⚠️</span>
        <div>
          <h3 class="impact-title">以下展示功能将不可用</h3>
          <p class="impact-subtitle">未选指标的对应地图、图表、统计将无数据</p>
        </div>
      </div>

      <div class="impact-list">
        <div
          v-for="item in unselectedImpacts"
          :key="item.key"
          class="impact-card"
        >
          <div class="impact-card-header">
            <span class="impact-label-icon">{{ ICON_MAP[item.key] }}</span>
            <span class="impact-label">{{ item.label }}</span>
            <span class="impact-badge">{{ item.affects.length }} 项</span>
          </div>
          <ul class="impact-items">
            <li v-for="(a, i) in item.affects" :key="i">{{ a }}</li>
          </ul>
        </div>
      </div>

      <div class="impact-note">
        缺失的数据将在报告中标记为"数据暂缺"，不影响其他指标的计算。
      </div>
    </div>

    <template #footer>
      <div class="impact-footer">
        <el-button @click="handleCancel">返回调整</el-button>
        <el-button type="primary" @click="handleConfirm">
          我已了解，开始分析
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  selected: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const ICON_MAP = {
  rsei: '🌿',
  construction: '🏗️',
  expansion: '📈',
  nightLight: '🌙',
  population: '👥',
  gdp: '💰',
}

const IMPACT_MAP = {
  rsei: {
    label: 'RSEI 生态指数',
    affects: ['RSEI 地图图层', 'RSEI 等级分类图', '生态统计面板（均值/等级/趋势）', '扩张-生态耦合散点图'],
  },
  construction: {
    label: '建设用地',
    affects: ['建设用地分布图', '总面积/新增面积统计', '扩张分析数据（依赖此项）'],
  },
  expansion: {
    label: '扩张模式',
    affects: ['扩张模式地图（边缘/填充/飞地）', '扩张速率/斑块统计', '区县扩张排名'],
  },
  nightLight: {
    label: '夜间灯光',
    affects: ['夜灯分布地图', '夜灯概览数值'],
  },
  population: {
    label: '人口',
    affects: ['人口密度地图', '人口总量/增长率统计', '区县人口排名'],
  },
  gdp: {
    label: 'GDP',
    affects: ['GDP 分布地图', 'GDP 总量/人均/增量', '增长率 + 区县 GDP 排名'],
  },
}

const unselectedImpacts = computed(() => {
  return Object.keys(IMPACT_MAP)
    .filter(key => !props.selected.includes(key))
    .map(key => ({ key, ...IMPACT_MAP[key] }))
})

function handleCancel() {
  visible.value = false
  emit('cancel')
}

function handleConfirm() {
  visible.value = false
  emit('confirm')
}
</script>

<style scoped>
.impact-content { color: #ccc; }

.impact-header {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 18px; padding-bottom: 14px;
  border-bottom: 1px solid #2a2a2a;
}
.impact-icon { font-size: 28px; }
.impact-title { color: #eee; font-size: 16px; margin: 0 0 2px; }
.impact-subtitle { color: #888; font-size: 13px; margin: 0; }

.impact-list {
  display: flex; flex-direction: column; gap: 10px;
  max-height: 50vh; overflow-y: auto;
  padding-right: 4px;
}

.impact-card {
  background: #1e1e1e;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  padding: 12px 14px;
}

.impact-card-header {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 8px;
}

.impact-label-icon { font-size: 16px; }
.impact-label { color: #ddd; font-size: 13px; font-weight: 600; flex: 1; }
.impact-badge {
  font-size: 10px; font-weight: 500;
  background: rgba(255, 107, 107, 0.12);
  color: #FF6B6B;
  padding: 2px 8px; border-radius: 4px;
}

.impact-items {
  margin: 0; padding-left: 20px;
  list-style: disc;
}

.impact-items li {
  color: #999; font-size: 12px; line-height: 1.8;
}

.impact-note {
  color: #666; font-size: 12px; text-align: center;
  padding: 10px 0 0; margin-top: 14px;
  border-top: 1px solid #2a2a2a;
}

.impact-footer {
  display: flex; justify-content: flex-end; gap: 10px;
}
</style>
