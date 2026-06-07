<template>
  <div class="timeline">
    <div class="timeline-row">
      <div
        v-for="year in years"
        :key="year"
        class="year-chip"
        :class="{ active: year === modelValue }"
        @click="select(year)"
      >
        <span class="chip-text">{{ year }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { TIME_PERIODS } from '../../config/map'

const props = defineProps({
  modelValue: { type: Number, default: 2020 },
})

const emit = defineEmits(['update:modelValue', 'change'])

const years = TIME_PERIODS

function select(year) {
  if (year === props.modelValue) return
  emit('update:modelValue', year)
  emit('change', { year })
}
</script>

<style scoped>
.timeline {
  padding: 10px 16px 12px;
  background: #1a1a1a;
  border-top: 1px solid #2a2a2a;
}

.timeline-row {
  display: flex;
  gap: 6px;
  justify-content: center;
}

.year-chip {
  padding: 6px 14px;
  background: #222;
  border: 1px solid #333;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.year-chip:hover {
  background: #2a2a2a;
  border-color: #555;
}

.chip-text {
  font-size: 13px;
  font-weight: 500;
  color: #666;
  transition: color 0.2s;
}

.year-chip:hover .chip-text { color: #aaa; }

.year-chip.active {
  background: rgba(255, 107, 107, 0.15);
  border-color: #FF6B6B;
}

.year-chip.active .chip-text {
  color: #fff;
  font-weight: 700;
}
</style>
