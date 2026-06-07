<template>
  <div class="range-timeline">
    <div class="slider-track" ref="trackRef" @click="onTrackClick">
      <!-- Track background -->
      <div class="track-bg" />

      <!-- Active range highlight -->
      <div class="track-range" :class="{ dragging: isDragging }" :style="rangeStyle" />

      <!-- Year marks -->
      <div
        v-for="year in years"
        :key="year"
        class="year-tick"
        :style="{ left: pct(year) + '%' }"
        :class="{ inRange: year >= modelValue[0] && year <= modelValue[1] }"
      >
        <div class="tick-line" />
        <span class="tick-label">{{ year }}</span>
      </div>

      <!-- Left thumb (start year) -->
      <div
        class="thumb thumb-start"
        :class="{ dragging: isDragging }"
        :style="{ left: startPct + '%' }"
        @mousedown.prevent="startDrag('start')"
        @touchstart.prevent="startDrag('start')"
      >
        <div class="thumb-handle">
          <span class="thumb-year">{{ modelValue[0] }}</span>
        </div>
      </div>

      <!-- Right thumb (end year) -->
      <div
        class="thumb thumb-end"
        :class="{ dragging: isDragging }"
        :style="{ left: endPct + '%' }"
        @mousedown.prevent="startDrag('end')"
        @touchstart.prevent="startDrag('end')"
      >
        <div class="thumb-handle">
          <span class="thumb-year">{{ modelValue[1] }}</span>
        </div>
      </div>
    </div>

    <div class="range-summary">
      <span class="sum-label start-color">{{ modelValue[0] }} 年</span>
      <span class="sum-arrow">⟷</span>
      <span class="sum-label end-color">{{ modelValue[1] }} 年</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { TIME_PERIODS } from '../../config/map'

const props = defineProps({
  modelValue: { type: Array, default: () => [2000, 2020] },
})

const emit = defineEmits(['update:modelValue', 'change'])

const years = TIME_PERIODS
const minYear = years[0]
const maxYear = years[years.length - 1]

const trackRef = ref(null)
const isDragging = ref(false)
// Visual thumb positions (raw %), decoupled from modelValue during drag
const visualStart = ref(null) // null = use modelValue
const visualEnd = ref(null)
let dragging = null

function pct(year) {
  return ((year - minYear) / (maxYear - minYear)) * 100
}

// Thumb positions: use visual position during drag, modelValue when idle
const startPct = computed(() => visualStart.value ?? pct(props.modelValue[0]))
const endPct = computed(() => visualEnd.value ?? pct(props.modelValue[1]))

const rangeStyle = computed(() => ({
  left: startPct.value + '%',
  width: (endPct.value - startPct.value) + '%',
}))

function nearestYear(value) {
  return years.reduce((prev, curr) =>
    Math.abs(curr - value) < Math.abs(prev - value) ? curr : prev
  )
}

function startDrag(which) {
  dragging = which
  isDragging.value = true
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.addEventListener('touchmove', onDrag, { passive: false })
  document.addEventListener('touchend', stopDrag)
}

function onDrag(e) {
  if (!dragging || !trackRef.value) return
  e.preventDefault()
  const rect = trackRef.value.getBoundingClientRect()
  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  let ratio = (clientX - rect.left) / rect.width
  ratio = Math.max(0, Math.min(1, ratio))
  const rawPct = ratio * 100

  if (dragging === 'start') {
    // Clamp: don't go past end thumb
    visualStart.value = Math.min(rawPct, endPct.value)
  } else {
    // Clamp: don't go past start thumb
    visualEnd.value = Math.max(rawPct, startPct.value)
  }
}

function stopDrag() {
  if (dragging) {
    // Snap to nearest year
    const rawStart = (visualStart.value ?? pct(props.modelValue[0])) / 100
    const rawEnd = (visualEnd.value ?? pct(props.modelValue[1])) / 100
    const yearStart = nearestYear(rawStart * (maxYear - minYear) + minYear)
    const yearEnd = nearestYear(rawEnd * (maxYear - minYear) + minYear)

    // Ensure start <= end
    const finalStart = Math.min(yearStart, yearEnd)
    const finalEnd = Math.max(yearStart, yearEnd)

    // Clear visual overrides so thumbs animate to snapped positions
    visualStart.value = null
    visualEnd.value = null

    emit('update:modelValue', [finalStart, finalEnd])
    emit('change', { start: finalStart, end: finalEnd })
  }
  dragging = null
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
}

function onTrackClick(e) {
  // Don't fire if we just finished dragging
  if (dragging) return
  if (!trackRef.value) return

  // Ignore clicks directly on thumbs (they handle their own mousedown)
  if (e.target.closest('.thumb')) return

  const rect = trackRef.value.getBoundingClientRect()
  let ratio = (e.clientX - rect.left) / rect.width
  ratio = Math.max(0, Math.min(1, ratio))
  const year = nearestYear(ratio * (maxYear - minYear) + minYear)

  const [start, end] = props.modelValue

  // Snap to whichever thumb is closer
  const distStart = Math.abs(year - start)
  const distEnd = Math.abs(year - end)

  // Don't move if clicking exactly on a thumb's current year
  if (year === start || year === end) return

  if (distStart <= distEnd && year < end) {
    emit('update:modelValue', [year, end])
  } else if (year > start) {
    emit('update:modelValue', [start, year])
  }
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
})
</script>

<style scoped>
.range-timeline {
  padding: 12px 32px 10px;
  background: #1a1a1a;
  border-top: 1px solid #2a2a2a;
}

.slider-track {
  position: relative;
  height: 56px;
  cursor: pointer;
}

/* Track lines */
.track-bg {
  position: absolute;
  top: 22px;
  left: 0;
  right: 0;
  height: 3px;
  background: #333;
  border-radius: 2px;
}

.track-range {
  position: absolute;
  top: 22px;
  height: 3px;
  background: linear-gradient(90deg, #FF6B6B, #4DABF7);
  border-radius: 2px;
  transition: left 0.25s cubic-bezier(0.4, 0, 0.2, 1), width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.track-range.dragging {
  transition: none;
}

/* Year tick marks */
.year-tick {
  position: absolute;
  top: 14px;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: none;
}

.tick-line {
  width: 1px;
  height: 8px;
  background: #444;
}

.year-tick.inRange .tick-line {
  background: rgba(255, 255, 255, 0.15);
}

.tick-label {
  margin-top: 16px;
  font-size: 11px;
  color: #555;
  transition: color 0.2s;
}

.year-tick.inRange .tick-label {
  color: #999;
}

/* Thumbs */
.thumb {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  z-index: 5;
  cursor: grab;
  touch-action: none;
  transition: left 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.thumb.dragging {
  transition: none;
}
.thumb:active {
  cursor: grabbing;
}

.thumb-handle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #fff;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.4);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.thumb:hover .thumb-handle {
  transform: scale(1.1);
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.5);
}

.thumb:active .thumb-handle {
  transform: scale(1.15);
}

.thumb-start .thumb-handle {
  background: #FF6B6B;
}

.thumb-end .thumb-handle {
  background: #4DABF7;
}

.thumb-year {
  font-size: 10px;
  font-weight: 800;
  color: #fff;
}

/* Summary */
.range-summary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 2px;
}

.sum-label {
  font-size: 13px;
  font-weight: 700;
}

.start-color { color: #FF6B6B; }
.end-color { color: #4DABF7; }

.sum-arrow {
  font-size: 14px;
  color: #444;
}
</style>
