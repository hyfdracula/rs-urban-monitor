<template>
  <div class="dashboard">
    <h3 class="title">关键指标总览</h3>
    <div class="cards">
      <div class="card"><div class="val">{{ d.totalCities }}</div><div class="lbl">研究城市</div></div>
      <div class="card"><div class="val accent">{{ d.totalConstruction }}</div><div class="unit">km²</div><div class="lbl">新增建设用地</div></div>
      <div class="card"><div class="val accent">{{ d.avgExpansionRate }}</div><div class="unit">%</div><div class="lbl">年均扩张速率</div></div>
      <div class="card"><div class="val green">{{ d.avgRSEI }}</div><div class="lbl">RSEI 均值</div></div>
      <div class="card"><div class="val red">{{ d.hotspotCount }}</div><div class="lbl">热点乡镇</div></div>
      <div class="card"><div class="val blue">{{ d.coldspotCount }}</div><div class="lbl">冷点乡镇</div></div>
      <div class="card"><div class="val green">{{ d.improvedArea }}</div><div class="unit">km²</div><div class="lbl">生态改善面积</div></div>
      <div class="card"><div class="val red">{{ d.degradedArea }}</div><div class="unit">km²</div><div class="lbl">生态退化面积</div></div>
    </div>

    <!-- 长三角平台报告下载 -->
    <div class="dl-section">
      <div class="dl-card" @click="$emit('open-report')">
        <span class="dl-icon">🏙️</span>
        <div class="dl-info">
          <span class="dl-name">长三角平台分析报告</span>
          <span class="dl-desc">27城扩张与生态响应分析</span>
        </div>
        <span class="dl-arrow">›</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

defineEmits(['open-report'])

const EMPTY_OVERVIEW = {
  totalCities: 0,
  totalConstruction: 0,
  avgExpansionRate: 0,
  avgRSEI: 0,
  hotspotCount: 0,
  coldspotCount: 0,
  improvedArea: 0,
  degradedArea: 0,
}

const props = defineProps({
  data: {
    type: Object,
    default: null,
  },
})

const d = computed(() => ({ ...EMPTY_OVERVIEW, ...(props.data || {}) }))
</script>

<style scoped>
.dashboard { padding: 14px; background: #1a1a1a; display: flex; flex-direction: column; flex: 1; }
.title { font-size: 14px; font-weight: 600; color: #ddd; margin: 0 0 14px 0; }
.cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.card { background: #252525; border-radius: 8px; padding: 14px; text-align: center; }
.val { font-size: 24px; font-weight: 700; color: #fff; }
.val.accent, .val.green, .val.red, .val.blue { color: #fff; }
.unit { font-size: 11px; color: #888; margin-top: 2px; }
.lbl { font-size: 11px; color: #aaa; margin-top: 4px; }

/* Download card */
.dl-section { margin-top: auto; }
.dl-card {
  display: flex; align-items: center; gap: 10px;
  background: #252525; border: 1px solid #333; border-radius: 8px;
  padding: 12px; cursor: pointer; transition: all 0.2s;
}
.dl-card:hover { border-color: #555; background: #2a2a2a; }
.dl-icon { font-size: 24px; flex-shrink: 0; }
.dl-info { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.dl-name { color: #ddd; font-size: 13px; font-weight: 600; }
.dl-desc { color: #666; font-size: 11px; }
.dl-arrow { color: #555; font-size: 18px; flex-shrink: 0; }
</style>
