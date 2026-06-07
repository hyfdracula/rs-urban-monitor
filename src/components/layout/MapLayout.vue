<template>
  <div class="map-layout" :class="{ mobile: isMobile }">
    <div class="main-row">
      <div class="map-area">
        <slot name="map" />

        <!-- Left sidebar: LayerControl + Legend stacked -->
        <div class="overlay-left">
          <slot name="layer-control" />
          <LegendBar />
        </div>

        <!-- Mobile: panel toggle -->
        <button
          v-if="isMobile"
          class="mobile-panel-toggle"
          @click="showMobilePanel = !showMobilePanel"
        >
          {{ showMobilePanel ? '✕' : '☰' }}
        </button>

        <!-- Panel toggle button (always visible) -->
        <button
          class="panel-toggle-btn"
          :class="{ 'panel-open': !isFullscreen }"
          @click="toggleFullscreen"
          :title="isFullscreen ? '显示面板' : '隐藏面板'"
        >
          <span v-if="isFullscreen">◧</span>
          <span v-else>◨</span>
        </button>

        <!-- Right Panel (overlays the map) -->
        <div class="right-panel" :class="{ open: showMobilePanel, hidden: isFullscreen }">
          <div class="panel-tabs">
            <!-- 总览: spans 2 rows in column 1 -->
            <button
              class="tab-btn tab-overview"
              :class="{ active: activeTab === tabs[0].key }"
              @click="activeTab = tabs[0].key"
            >
              <span class="tab-dot" :style="{ background: tabs[0].color }" />
              <span>{{ tabs[0].label }}</span>
            </button>
            <!-- Remaining 6 tabs: 3 per row -->
            <button
              v-for="tab in tabs.slice(1)"
              :key="tab.key"
              class="tab-btn"
              :class="{ active: activeTab === tab.key }"
              @click="activeTab = tab.key"
            >
              <span class="tab-dot" :style="{ background: tab.color }" />
              <span>{{ tab.label }}</span>
            </button>
          </div>
          <div class="panel-body">
            <Transition name="slide" mode="out-in">
              <div :key="activeTab" class="panel-scroll">
                <slot :name="activeTab" />
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </div>

    <slot name="timeline" />
  </div>
</template>

<script setup>
import { ref, provide, onMounted, onUnmounted } from 'vue'
import LegendBar from '../map/LegendBar.vue'

const props = defineProps({
  tabs: { type: Array, required: true },
  defaultTab: { type: String, default: '' },
})

const activeTab = ref(props.defaultTab || props.tabs[0]?.key || '')
const isMobile = ref(false)
const showMobilePanel = ref(false)
const isFullscreen = ref(false)

provide('isFullscreen', isFullscreen)

function toggleFullscreen() { isFullscreen.value = !isFullscreen.value }
function checkMobile() {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) showMobilePanel.value = true
}
onMounted(() => { checkMobile(); window.addEventListener('resize', checkMobile) })
onUnmounted(() => { window.removeEventListener('resize', checkMobile) })
</script>

<style scoped>
.map-layout { display: flex; flex-direction: column; height: 100%; }
.main-row { flex: 1; position: relative; min-height: 0; }
.map-area { position: absolute; inset: 0; }

.overlay-left {
  position: absolute; top: 12px; left: 12px; width: 200px; z-index: 10;
  display: flex; flex-direction: column; gap: 8px;
}

.panel-toggle-btn {
  position: absolute; top: 8px; right: 12px; transform: none;
  width: 34px; height: 34px; background: rgba(26,26,26,0.9);
  border: 1px solid #444; border-radius: 8px; color: #aaa;
  font-size: 18px; cursor: pointer; z-index: 15;
  backdrop-filter: blur(8px); transition: right 0.3s ease;
  display: flex; align-items: center; justify-content: center;
}
.panel-toggle-btn:hover { color: #fff; border-color: #FFD43B; }
.panel-toggle-btn.panel-open { right: 328px; }

.mobile-panel-toggle {
  display: none; position: absolute; bottom: 60px; right: 12px;
  width: 40px; height: 40px; background: rgba(26,26,26,0.9);
  border: 1px solid #444; border-radius: 50%; color: #fff;
  font-size: 16px; cursor: pointer; z-index: 15;
}

.right-panel {
  position: absolute; top: 0; right: 0; bottom: 0;
  width: 320px; background: #1a1a1a;
  border-left: 1px solid #333; display: flex; flex-direction: column;
  z-index: 12; overflow: hidden;
  transition: transform 0.3s ease, opacity 0.3s ease;
}
.right-panel.hidden {
  transform: translateX(100%); opacity: 0;
  pointer-events: none;
}
.panel-tabs {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(2, 1fr);
  border-bottom: 1px solid #333;
  flex-shrink: 0;
}
.tab-btn {
  display: flex; align-items: center; justify-content: center;
  gap: 6px; padding: 10px 6px; background: none; border: none;
  color: #888; font-size: 12px; font-weight: 500; cursor: pointer;
  transition: all 0.2s; border-bottom: 2px solid transparent;
  position: relative;
}
.tab-btn:hover { color: #ccc; background: #222; }
.tab-btn.active { color: #fff; background: #222; }
/* Overview tab spans 2 rows */
.tab-overview { grid-row: 1 / 3; }
.tab-overview.active { border-bottom-color: #FFD43B; }
/* Active colors by position in grid */
.tab-btn:nth-child(2).active { border-bottom-color: #FF6B6B; }
.tab-btn:nth-child(3).active { border-bottom-color: #51CF66; }
.tab-btn:nth-child(4).active { border-bottom-color: #BE4BDB; }
.tab-btn:nth-child(5).active { border-bottom-color: #4DABF7; }
.tab-btn:nth-child(6).active { border-bottom-color: #FF922B; }
.tab-btn:nth-child(7).active { border-bottom-color: #20C997; }
.tab-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.panel-body { flex: 1; min-height: 0; overflow: hidden; }
.panel-scroll { height: 100%; overflow-y: auto; }
.panel-scroll::-webkit-scrollbar { width: 4px; }
.panel-scroll::-webkit-scrollbar-track { background: transparent; }
.panel-scroll::-webkit-scrollbar-thumb { background: #444; border-radius: 2px; }
.slide-enter-active,.slide-leave-active { transition: all 0.2s ease; }
.slide-enter-from { opacity: 0; transform: translateX(12px); }
.slide-leave-to { opacity: 0; transform: translateX(-12px); }

@media (max-width: 767px) {
  .overlay-left { width: 160px; left: 6px; }
  .right-panel {
    position: fixed; top: 56px; right: 0; bottom: 60px;
    width: 280px; z-index: 20; transform: translateX(100%);
    transition: transform 0.3s ease; box-shadow: -4px 0 20px rgba(0,0,0,0.4);
  }
  .right-panel.open { transform: translateX(0); }
  .mobile-panel-toggle { display: flex; align-items: center; justify-content: center; }
}
</style>
