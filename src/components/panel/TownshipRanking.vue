<template>
  <div class="ranking-panel">
    <h3 class="panel-title">乡镇生态质量排名</h3>
    <div class="table-wrap">
      <table>
        <thead><tr><th>#</th><th>乡镇</th><th>城市</th><th>RSEI</th><th>变化</th></tr></thead>
        <tbody>
          <tr v-for="r in sorted" :key="r.name" :class="r.trend">
            <td class="rank">{{ r.rank }}</td><td>{{ r.name }}</td><td>{{ r.city }}</td>
            <td :style="{color: r.rsei>0.6?'#69DB7C':r.rsei>0.4?'#FFD43B':'#FF6B6B'}">{{ r.rsei }}</td>
            <td :style="{color:r.trend==='up'?'#69DB7C':r.trend==='down'?'#FF6B6B':'#888'}">{{ r.change }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { getTownshipRanking } from '../../data/mockAnalysis'

const data = ref(getTownshipRanking())
const sorted = computed(() => [...data.value].sort((a, b) => a.rank - b.rank))
</script>

<style scoped>
.ranking-panel { padding: 12px; }
.panel-title { font-size: 14px; font-weight: 600; color: #ddd; margin: 0 0 12px 0; }
.table-wrap { max-height: 360px; overflow-y: auto; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th { text-align: left; padding: 8px; color: #666; font-weight: 600; border-bottom: 1px solid #333; font-size: 11px; }
td { padding: 7px 8px; color: #bbb; border-bottom: 1px solid #2a2a2a; }
tr:hover td { background: rgba(255,255,255,0.02); }
.rank { color: #666; font-size: 11px; width: 24px; }
tr.up td:first-child { border-left: 2px solid #69DB7C; }
tr.down td:first-child { border-left: 2px solid #FF6B6B; }
</style>
