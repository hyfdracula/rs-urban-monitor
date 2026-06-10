<template>
  <div v-if="items.length" class="bottom-bar">
    <button
      v-for="item in items"
      :key="item.key"
      class="bar-btn"
      @click="handleClick(item)"
    >
      <el-icon v-if="item.icon"><component :is="item.icon" /></el-icon>
      <span class="bar-label">{{ item.label }}</span>
      <span v-if="item.sub" class="bar-sub">{{ item.sub }}</span>
    </button>
  </div>
</template>

<script setup>
const props = defineProps({
  items: { type: Array, default: () => [] },
})

const emit = defineEmits(['item-click'])

function handleClick(item) {
  emit('item-click', item)
}
</script>

<style scoped>
.bottom-bar {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  background: rgba(26, 26, 26, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid #444;
  border-radius: 20px;
  z-index: 13;
}

.bar-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  background: none;
  border: none;
  border-radius: 16px;
  color: #bbb;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.bar-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

.bar-sub {
  font-size: 11px;
  color: #888;
  margin-left: 2px;
}

.bar-btn:hover .bar-sub {
  color: #aaa;
}

@media (max-width: 767px) {
  .bottom-bar {
    bottom: 10px;
    gap: 2px;
    padding: 3px;
  }
  .bar-btn {
    padding: 5px 10px;
    font-size: 12px;
  }
}
</style>
