<template>
  <div class="step-export">
    <h4 class="step-title">导出设置</h4>
    <p class="step-desc">设置计算结果的导出方式</p>

    <div class="export-options">
      <div
        class="export-card"
        :class="{ active: exportFormat === 'drive' }"
        @click="exportFormat = 'drive'; emitUpdate()"
      >
        <span class="export-icon">📁</span>
        <div>
          <span class="export-name">导出到 Google Drive</span>
          <span class="export-desc">下载 GeoTIFF 到本地，再上传到 GeoServer</span>
        </div>
      </div>

      <div
        class="export-card"
        :class="{ active: exportFormat === 'asset' }"
        @click="exportFormat = 'asset'; emitUpdate()"
      >
        <span class="export-icon">☁️</span>
        <div>
          <span class="export-name">导出到 EE Asset</span>
          <span class="export-desc">保存到 GEE Asset 供后续在线分析使用</span>
        </div>
      </div>
    </div>

    <div class="prefix-section">
      <label>文件名前缀</label>
      <el-input
        v-model="exportPrefix"
        placeholder="如: rs_urban"
        @input="emitUpdate"
      />
    </div>

    <div class="summary-box">
      <h5>生成内容预览</h5>
      <div class="summary-items">
        <div class="summary-row">
          <span class="label">分析指标</span>
          <span class="value">{{ indicatorNames }}</span>
        </div>
        <div class="summary-row">
          <span class="label">时间范围</span>
          <span class="value">{{ timePeriods.join(', ') }} 年</span>
        </div>
        <div class="summary-row">
          <span class="label">导出文件</span>
          <span class="value">约 {{ fileCount }} 个 GeoTIFF</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:modelValue'])

const exportFormat = ref(props.modelValue.exportFormat || 'drive')
const exportPrefix = ref(props.modelValue.exportPrefix || 'rs_urban')

const timePeriods = computed(() => props.modelValue.timePeriods || [])
const indicators = computed(() => props.modelValue.indicators || [])

const indicatorNames = computed(() => {
  const names = {
    rsei: 'RSEI', construction: '建设用地', expansion: '扩张模式',
    nightLight: '夜灯', population: '人口', gdp: 'GDP',
  }
  return indicators.value.map(i => names[i] || i).join('、') || '未选择'
})

const fileCount = computed(() => {
  let count = 0
  const years = timePeriods.value.length
  for (const ind of indicators.value) {
    if (ind === 'expansion') count += Math.max(0, years - 1)
    else count += years
  }
  return count
})

function emitUpdate() {
  emit('update:modelValue', {
    ...props.modelValue,
    exportFormat: exportFormat.value,
    exportPrefix: exportPrefix.value,
  })
}
</script>

<style scoped>
.step-export { padding: 8px 0; }
.step-title { color: #ddd; margin: 0 0 6px; font-size: 15px; }
.step-desc { color: #888; font-size: 13px; margin: 0 0 16px; }

.export-options { display: flex; flex-direction: column; gap: 10px; }

.export-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.export-card:hover { border-color: #555; }
.export-card.active { border-color: #BE4BDB; background: rgba(190, 75, 219, 0.08); }

.export-icon { font-size: 24px; }
.export-name { color: #ddd; font-size: 13px; font-weight: 500; display: block; }
.export-card.active .export-name { color: #BE4BDB; }
.export-desc { color: #666; font-size: 11px; display: block; margin-top: 2px; }

.prefix-section {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.prefix-section label { color: #aaa; font-size: 13px; white-space: nowrap; }

.summary-box {
  margin-top: 16px;
  padding: 14px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 10px;
}
.summary-box h5 { color: #ccc; margin: 0 0 10px; font-size: 13px; }
.summary-items { display: flex; flex-direction: column; gap: 6px; }
.summary-row { display: flex; justify-content: space-between; }
.summary-row .label { color: #888; font-size: 12px; }
.summary-row .value { color: #bbb; font-size: 12px; }
</style>
