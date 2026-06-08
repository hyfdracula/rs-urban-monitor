<template>
  <div class="step-indicators">
    <h4 class="step-title">选择分析指标</h4>
    <p class="step-desc">至少选择一个分析指标</p>

    <div class="indicator-grid">
      <div
        v-for="ind in indicatorList"
        :key="ind.key"
        class="indicator-card"
        :class="{ active: selected.includes(ind.key) }"
        @click="toggleIndicator(ind.key)"
      >
        <span class="ind-icon">{{ ind.icon }}</span>
        <div class="ind-info">
          <span class="ind-name">{{ ind.name }}</span>
          <span class="ind-desc">{{ ind.desc }}</span>
        </div>
      </div>
    </div>

    <div class="quick-actions">
      <el-button size="small" text @click="selectAll">全选</el-button>
      <el-button size="small" text @click="selectNone">清空</el-button>
    </div>

    <!-- Dependency hint -->
    <div v-if="selected.includes('expansion') && !selected.includes('construction')" class="warning-tip">
      <el-icon><Warning /></el-icon>
      <span>扩张模式分析依赖建设用地提取，已自动勾选</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Warning } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:modelValue'])

const indicatorList = [
  { key: 'rsei', name: '遥感生态指数', desc: 'NDVI + WET + NDBSI + LST → PCA', icon: '🌿' },
  { key: 'construction', name: '建设用地提取', desc: '基于不透水面分类', icon: '🏗️' },
  { key: 'expansion', name: '扩张模式分类', desc: '边缘/填充/飞地三种模式', icon: '📈' },
  { key: 'nightLight', name: '夜间灯光', desc: 'DMSP-OLS + VIIRS', icon: '🌙' },
  { key: 'population', name: '人口密度', desc: 'WorldPop 100m 栅格', icon: '👥' },
  { key: 'gdp', name: 'GDP 分布', desc: 'GDP 空间化代理', icon: '💰' },
]

const selected = ref([...(props.modelValue.indicators || [])])

function toggleIndicator(key) {
  const idx = selected.value.indexOf(key)
  if (idx >= 0) selected.value.splice(idx, 1)
  else selected.value.push(key)

  // Auto-add construction dependency for expansion
  if (key === 'expansion' && selected.value.includes('expansion') && !selected.value.includes('construction')) {
    selected.value.push('construction')
  }

  emitUpdate()
}

function selectAll() {
  selected.value = indicatorList.map(i => i.key)
  emitUpdate()
}

function selectNone() {
  selected.value = []
  emitUpdate()
}

function emitUpdate() {
  emit('update:modelValue', { ...props.modelValue, indicators: [...selected.value] })
}

watch(() => props.modelValue.indicators, (val) => {
  if (JSON.stringify(val) !== JSON.stringify(selected.value)) {
    selected.value = [...(val || [])]
  }
})
</script>

<style scoped>
.step-indicators { padding: 8px 0; }
.step-title { color: #ddd; margin: 0 0 6px; font-size: 15px; }
.step-desc { color: #888; font-size: 13px; margin: 0 0 16px; }

.indicator-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.indicator-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.indicator-card:hover { border-color: #555; }
.indicator-card.active {
  border-color: #69DB7C;
  background: rgba(105, 219, 124, 0.08);
}

.ind-icon { font-size: 22px; }

.ind-info { display: flex; flex-direction: column; gap: 2px; }
.ind-name { color: #ddd; font-size: 13px; font-weight: 500; }
.indicator-card.active .ind-name { color: #69DB7C; }
.ind-desc { color: #666; font-size: 11px; }

.quick-actions { margin-top: 10px; text-align: center; }

.warning-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  padding: 8px 12px;
  background: rgba(255, 202, 40, 0.1);
  border: 1px solid rgba(255, 202, 40, 0.3);
  border-radius: 8px;
  color: #FFD43B;
  font-size: 12px;
}

@media (max-width: 500px) {
  .indicator-grid { grid-template-columns: 1fr; }
}
</style>
