<template>
  <div class="step-satellite">
    <h4 class="step-title">选择遥感数据源</h4>
    <p class="step-desc">不同数据源影响空间分辨率和时间覆盖范围</p>

    <div class="satellite-options">
      <div
        class="sat-card"
        :class="{ active: selected === 'landsat-auto' }"
        @click="selectSat('landsat-auto')"
      >
        <div class="sat-header">
          <span class="sat-icon">🛰️</span>
          <span class="sat-name">Landsat 自动选择</span>
        </div>
        <div class="sat-details">
          <span>• Landsat 5 (2000-2011) · 30m</span>
          <span>• Landsat 7 (2012-2013) · 30m</span>
          <span>• Landsat 8 (2014+) · 30m</span>
        </div>
        <el-tag size="small" type="success">推荐</el-tag>
      </div>

      <div
        class="sat-card"
        :class="{ active: selected === 'sentinel2' }"
        @click="selectSat('sentinel2')"
      >
        <div class="sat-header">
          <span class="sat-icon">🛰️</span>
          <span class="sat-name">Sentinel-2</span>
        </div>
        <div class="sat-details">
          <span>• 10m 分辨率，更精细</span>
          <span>• 仅支持 2015 年及以后</span>
          <span>• 多光谱 13 个波段</span>
        </div>
        <el-tag size="small" type="warning">高分辨率</el-tag>
      </div>
    </div>

    <div v-if="selected === 'sentinel2'" class="info-tip">
      <el-icon><InfoFilled /></el-icon>
      <span>2015 年以前的年份将自动回退到 Landsat 数据源</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:modelValue'])

const selected = ref(props.modelValue.satellite || 'landsat-auto')

function selectSat(sat) {
  selected.value = sat
  emit('update:modelValue', { ...props.modelValue, satellite: sat })
}

watch(() => props.modelValue.satellite, (val) => {
  if (val && val !== selected.value) selected.value = val
})
</script>

<style scoped>
.step-satellite { padding: 8px 0; }
.step-title { color: #ddd; margin: 0 0 6px; font-size: 15px; }
.step-desc { color: #888; font-size: 13px; margin: 0 0 16px; }

.satellite-options { display: flex; flex-direction: column; gap: 12px; }

.sat-card {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 10px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}
.sat-card:hover { border-color: #555; }
.sat-card.active {
  border-color: #4DABF7;
  background: rgba(77, 171, 247, 0.08);
}

.sat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.sat-icon { font-size: 20px; }
.sat-name { color: #ddd; font-size: 14px; font-weight: 500; }
.sat-card.active .sat-name { color: #4DABF7; }

.sat-details {
  display: flex;
  flex-direction: column;
  gap: 3px;
  color: #888;
  font-size: 12px;
  margin-bottom: 8px;
}

.info-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding: 8px 12px;
  background: rgba(77, 171, 247, 0.1);
  border: 1px solid rgba(77, 171, 247, 0.3);
  border-radius: 8px;
  color: #4DABF7;
  font-size: 12px;
}
</style>
