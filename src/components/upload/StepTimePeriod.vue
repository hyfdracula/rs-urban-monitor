<template>
  <div class="step-time">
    <h4 class="step-title">选择分析时间范围</h4>
    <p class="step-desc">选择需要分析的年份（至少选一个）</p>

    <div class="year-grid">
      <div
        v-for="year in periods"
        :key="year"
        class="year-card"
        :class="{ active: selected.includes(year) }"
        @click="toggleYear(year)"
      >
        <span class="year-num">{{ year }}</span>
        <span class="year-label">年</span>
      </div>
    </div>

    <div class="quick-actions">
      <el-button size="small" text @click="selectAll">全选</el-button>
      <el-button size="small" text @click="selectNone">清空</el-button>
    </div>

    <div v-if="sentinelWarning" class="warning-tip">
      <el-icon><Warning /></el-icon>
      <span>Sentinel-2 仅支持 2015 年及以后，早期年份将使用 Landsat</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Warning } from '@element-plus/icons-vue'
import { TIME_PERIODS } from '../../config/map'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:modelValue'])

const periods = TIME_PERIODS
const selected = ref([...props.modelValue.timePeriods])

const sentinelWarning = computed(() =>
  props.modelValue.satellite === 'sentinel2' && selected.value.some(y => y < 2015)
)

function toggleYear(year) {
  const idx = selected.value.indexOf(year)
  if (idx >= 0) selected.value.splice(idx, 1)
  else selected.value.push(year)
  selected.value.sort()
  emitUpdate()
}

function selectAll() {
  selected.value = [...periods]
  emitUpdate()
}

function selectNone() {
  selected.value = []
  emitUpdate()
}

function emitUpdate() {
  emit('update:modelValue', { ...props.modelValue, timePeriods: [...selected.value] })
}

// Sync if parent changes
watch(() => props.modelValue.timePeriods, (val) => {
  if (JSON.stringify(val) !== JSON.stringify(selected.value)) {
    selected.value = [...(val || [])]
  }
})
</script>

<style scoped>
.step-time { padding: 8px 0; }
.step-title { color: #ddd; margin: 0 0 6px; font-size: 15px; }
.step-desc { color: #888; font-size: 13px; margin: 0 0 20px; }

.year-grid {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.year-card {
  width: 80px;
  height: 70px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  gap: 2px;
}

.year-card:hover { border-color: #555; }
.year-card.active {
  border-color: #4DABF7;
  background: rgba(77, 171, 247, 0.1);
}

.year-num { color: #ddd; font-size: 22px; font-weight: 600; }
.year-card.active .year-num { color: #4DABF7; }
.year-label { color: #666; font-size: 12px; }

.quick-actions { margin-top: 12px; text-align: center; }

.warning-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding: 8px 12px;
  background: rgba(255, 202, 40, 0.1);
  border: 1px solid rgba(255, 202, 40, 0.3);
  border-radius: 8px;
  color: #FFD43B;
  font-size: 12px;
}
</style>
