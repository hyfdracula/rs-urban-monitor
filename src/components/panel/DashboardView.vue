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
  </div>
</template>

<script setup>
import { getOverviewData } from '../../data/mockAnalysis'
const d = getOverviewData()
</script>

<style scoped>
.dashboard { padding: 14px; }
.title { font-size: 14px; font-weight: 600; color: #ddd; margin: 0 0 14px 0; }
.cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.card { background: #252525; border-radius: 8px; padding: 14px; text-align: center; }
.val { font-size: 24px; font-weight: 700; color: #fff; }
.val.accent, .val.green, .val.red, .val.blue { color: #fff; }
.unit { font-size: 11px; color: #888; margin-top: 2px; }
.lbl { font-size: 11px; color: #aaa; margin-top: 4px; }
</style>
