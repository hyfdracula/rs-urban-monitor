<template>
  <div v-if="feature" class="feature-popup">
    <div class="popup-header">
      <span class="popup-city">{{ feature.city }}</span>
      <span class="popup-close" @click="$emit('close')">✕</span>
    </div>
    <div class="popup-body">
      <div class="popup-row">
        <span class="popup-label">类型</span>
        <span class="popup-value">{{ feature.category }}</span>
      </div>
      <div class="popup-row">
        <span class="popup-label">面积</span>
        <span class="popup-value highlight">{{ feature.area }} km²</span>
      </div>
      <div class="popup-row">
        <span class="popup-label">扩张模式</span>
        <span class="popup-value">
          <span class="mode-badge" :style="{ background: modeColor }">
            {{ feature.mode }}
          </span>
        </span>
      </div>
      <div class="popup-row">
        <span class="popup-label">年份</span>
        <span class="popup-value">{{ feature.year }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  feature: { type: Object, default: null },
  lngLat: { type: Object, default: null },
})

defineEmits(['close'])

const modeColors = {
  '边缘扩张': '#FF6B6B',
  '填充式扩张': '#FFD43B',
  '飞地式扩张': '#4DABF7',
}

const modeColor = computed(() => {
  return modeColors[props.feature?.mode] || '#888'
})
</script>

<style scoped>
.feature-popup {
  position: absolute;
  min-width: 200px;
  max-width: 260px;
  background: rgba(26, 26, 26, 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid #444;
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  pointer-events: auto;
  animation: popIn 0.15s ease;
}

@keyframes popIn {
  from { opacity: 0; transform: scale(0.95) translateY(4px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}

.popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px 6px;
}

.popup-city {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
}

.popup-close {
  font-size: 14px;
  color: #666;
  cursor: pointer;
  padding: 0 2px;
}

.popup-close:hover {
  color: #fff;
}

.popup-body {
  padding: 4px 12px 12px;
}

.popup-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.popup-label {
  font-size: 12px;
  color: #888;
}

.popup-value {
  font-size: 13px;
  color: #ddd;
  font-weight: 500;
}

.popup-value.highlight {
  color: #FFA94D;
  font-weight: 700;
}

.mode-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: #fff;
  font-weight: 600;
}
</style>
