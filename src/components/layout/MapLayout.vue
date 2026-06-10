<template>
  <div class="map-layout" :class="{ mobile: isMobile }">
    <div class="main-row">
      <div class="map-area">
        <slot name="map" />

        <!-- Layer control: fixed position, independent -->
        <div v-if="showLayerControl" class="layer-control-area" :class="{ collapsed: layerControlCollapsed }">
          <slot name="layer-control" />
        </div>
        <button
          v-if="showLayerControl"
          class="layer-control-toggle"
          :class="{ 'panel-open': !layerControlCollapsed }"
          @click="layerControlCollapsed = !layerControlCollapsed"
          :title="layerControlCollapsed ? '展开图层控制' : '收起图层控制'"
        >
          <span v-if="layerControlCollapsed">◧</span>
          <span v-else>◨</span>
        </button>

        <!-- Legend: fixed position, independent of layer control -->
        <div v-if="showLegend" class="legend-area" :class="{ collapsed: legendCollapsed }">
          <LegendBar />
        </div>
        <button
          v-if="showLegend"
          class="legend-toggle"
          :class="{ 'panel-open': !legendCollapsed }"
          @click="legendCollapsed = !legendCollapsed"
          :title="legendCollapsed ? '展开图例' : '收起图例'"
        >
          <span v-if="legendCollapsed">◧</span>
          <span v-else>◨</span>
        </button>

        <!-- Panel toggle button (always visible) -->
        <button
          class="panel-toggle-btn"
          :class="{ 'panel-open': isMobile ? showMobilePanel : !isFullscreen }"
          @click="toggleFullscreen"
          :title="isFullscreen ? '显示面板' : '隐藏面板'"
        >
          <span v-if="(isMobile && !showMobilePanel) || (!isMobile && isFullscreen)">◧</span>
          <span v-else>◨</span>
        </button>

        <!-- Right Panel (overlays the map) -->
        <div class="right-panel" :class="{ open: showMobilePanel, hidden: isFullscreen }">
          <div class="panel-tabs">
            <!-- 总览: spans 2 rows in column 1 -->
            <button
              class="tab-btn tab-overview"
              :class="{ active: activeTab === tabs[0].key }"
              @click="onTabClick(tabs[0].key)"
            >
              <span class="tab-dot" :style="{ background: tabs[0].color }" />
              <span class="tab-label">{{ tabs[0].label }}</span>
            </button>
            <!-- Remaining 6 tabs: 3 per row -->
            <button
              v-for="tab in tabs.slice(1)"
              :key="tab.key"
              class="tab-btn"
              :class="{ active: activeTab === tab.key }"
              @click="onTabClick(tab.key)"
            >
              <span class="tab-dot" :style="{ background: tab.color }" />
              <span class="tab-label">{{ tab.label }}</span>
            </button>
          </div>
          <div class="panel-body">
            <div
              v-for="tab in tabs"
              :key="tab.key"
              class="panel-scroll"
              :class="{ active: activeTab === tab.key }"
            >
              <slot :name="tab.key" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <slot name="timeline" />
  </div>
</template>

<script setup>
import { ref, provide, onMounted, onUnmounted, watch, nextTick } from 'vue'
import LegendBar from '../map/LegendBar.vue'

const props = defineProps({
  tabs: { type: Array, required: true },
  defaultTab: { type: String, default: '' },
  showLayerControl: { type: Boolean, default: true },
  showLegend: { type: Boolean, default: true },
})

const activeTab = ref(props.defaultTab || props.tabs[0]?.key || '')
const isMobile = ref(false)
const showMobilePanel = ref(false)
const isFullscreen = ref(false)
const layerControlCollapsed = ref(false)
const legendCollapsed = ref(false)

provide('isFullscreen', isFullscreen)

// Tab切换时触发resize + chart动画重播
watch(activeTab, (newKey) => {
  nextTick(() => {
    window.dispatchEvent(new Event('resize'))
    window.dispatchEvent(new CustomEvent('chart-replay', { detail: newKey }))
  })
})

// 点击已激活的 tab 也重播动画（watch 不触发，因为值未变）
function onTabClick(tabKey) {
  const isSame = activeTab.value === tabKey
  activeTab.value = tabKey
  if (isSame) {
    nextTick(() => {
      window.dispatchEvent(new CustomEvent('chart-replay', { detail: tabKey }))
    })
  }
}

function toggleFullscreen() {
  if (isMobile.value) {
    showMobilePanel.value = !showMobilePanel.value
  } else {
    isFullscreen.value = !isFullscreen.value
  }
}
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

/* ===== Left side: Layer Control ===== */
.layer-control-area {
  position: absolute; top: 12px; left: 12px; width: 200px; z-index: 10;
  transition: transform 0.3s ease, opacity 0.3s ease;
}
.layer-control-area.collapsed {
  transform: translateX(-100%); opacity: 0;
  pointer-events: none;
}

.layer-control-toggle {
  position: absolute; top: 12px; left: 220px;
  width: 34px; height: 34px; background: rgba(26,26,26,0.9);
  border: 1px solid #444; border-radius: 8px; color: #aaa;
  font-size: 18px; cursor: pointer; z-index: 11;
  backdrop-filter: blur(8px); transition: left 0.3s ease;
  display: flex; align-items: center; justify-content: center;
}
.layer-control-toggle:hover { color: #fff; border-color: #FFD43B; }
.layer-control-toggle.panel-open { left: 220px; }
/* When collapsed, button slides to where panel edge was */
.layer-control-toggle:not(.panel-open) { left: 12px; }

/* ===== Left side: Legend (fixed position, independent) ===== */
.legend-area {
  position: absolute; top: 410px; left: 12px; width: 200px; z-index: 10;
  transition: transform 0.3s ease, opacity 0.3s ease;
}
.legend-area.collapsed {
  transform: translateX(-100%); opacity: 0;
  pointer-events: none;
}

.legend-toggle {
  position: absolute; top: 410px; left: 220px;
  width: 34px; height: 34px; background: rgba(26,26,26,0.9);
  border: 1px solid #444; border-radius: 8px; color: #aaa;
  font-size: 18px; cursor: pointer; z-index: 11;
  backdrop-filter: blur(8px); transition: left 0.3s ease, top 0.3s ease;
  display: flex; align-items: center; justify-content: center;
}
.legend-toggle:hover { color: #fff; border-color: #FFD43B; }
.legend-toggle.panel-open { left: 220px; }
.legend-toggle:not(.panel-open) { left: 12px; }

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
.tab-btn:nth-child(3).active { border-bottom-color: #FF922B; }
.tab-btn:nth-child(4).active { border-bottom-color: #51CF66; }
.tab-btn:nth-child(5).active { border-bottom-color: #BE4BDB; }
.tab-btn:nth-child(6).active { border-bottom-color: #4DABF7; }
.tab-btn:nth-child(7).active { border-bottom-color: #20C997; }
/* Tab dot indicator — hidden on all devices */
.tab-dot { display: none; }
/* Tab text */
.tab-label { white-space: nowrap; }
.panel-body { flex: 1; min-height: 0; overflow: hidden; background: #1a1a1a; }
.panel-scroll {
  height: 100%;
  overflow-y: auto;
  background: #1a1a1a;
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  visibility: hidden;
  pointer-events: none;
}
.panel-scroll.active {
  position: relative;
  visibility: visible;
  pointer-events: auto;
}
.panel-scroll::-webkit-scrollbar { width: 4px; }
.panel-scroll::-webkit-scrollbar-track { background: transparent; }
.panel-scroll::-webkit-scrollbar-thumb { background: #444; border-radius: 2px; }

@media (max-width: 767px) {
  .layer-control-area { width: 160px; left: 6px; }
  .layer-control-toggle.panel-open { left: 174px; }
  .layer-control-toggle:not(.panel-open) { left: 6px; }
  .legend-area { width: 160px; left: 6px; top: 370px; }
  .legend-toggle { top: 370px; }
  .legend-toggle.panel-open { left: 174px; }
  .legend-toggle:not(.panel-open) { left: 6px; }
  .right-panel {
    position: fixed; top: 48px; right: 0; bottom: 0;
    width: min(85vw, 360px); z-index: 20; transform: translateX(100%);
    transition: transform 0.3s ease; box-shadow: -4px 0 20px rgba(0,0,0,0.4);
  }
  .right-panel.open { transform: translateX(0); }
  .tab-label { font-size: 11px; }
  .tab-btn { padding: 12px 6px; }
  .tab-overview { padding: 12px 6px; }
  /* Panel toggle button follows panel on mobile */
  .panel-toggle-btn.panel-open { right: calc(min(85vw, 360px) + 8px); }
}
</style>
