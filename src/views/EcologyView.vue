<template>
  <MapLayout :tabs="tabs" default-tab="ecology">
    <template #map><MapViewer ref="mapRef" @map-loaded="onMapLoaded" @feature-click="onFeatureClick" /></template>
    <template #layer-control><LayerControl ref="layerControlRef" @layer-toggle="onLayerToggle" @mode-toggle="onModeToggle" /></template>
    <template #dashboard><DashboardView :data="overviewData" /></template>
    <template #expansion><ExpansionStats :data="expansionData" @district-click="flyToDistrict" /></template>
    <template #ecology><EcologyStats :data="ecologyData" /></template>
    <template #socio><SocioEconomicStats :data="socioData" @district-click="flyToDistrict" /></template>
    <template #hotspot><HotspotView :data="hotspotData" @district-click="flyToDistrict" /></template>
    <template #scatter><ScatterRadarView @district-click="flyToDistrict" /></template>
    <template #ranking><TownshipRanking /></template>
    <template #timeline><TimelineSelector v-model="selectedYear" @change="onYearChange" /></template>
  </MapLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MapLayout from '../components/layout/MapLayout.vue'
import MapViewer from '../components/map/MapViewer.vue'
import LayerControl from '../components/map/LayerControl.vue'
import TimelineSelector from '../components/map/TimelineSelector.vue'
import ExpansionStats from '../components/panel/ExpansionStats.vue'
import EcologyStats from '../components/panel/EcologyStats.vue'
import SocioEconomicStats from '../components/panel/SocioEconomicStats.vue'
import DashboardView from '../components/panel/DashboardView.vue'
import HotspotView from '../components/panel/HotspotView.vue'
import ScatterRadarView from '../components/panel/ScatterRadarView.vue'
import TownshipRanking from '../components/panel/TownshipRanking.vue'
import {
  fetchEcologyData,
  fetchExpansionData,
  fetchHotspotData,
  fetchOverviewData,
  fetchSocioEconomicData,
} from '../services/dataService'
import { activeYearLayerGroups, activeYearLayers, setActiveYearLayers } from '../stores/layerState'
import { buildYearLayerTransition, getYearLayerId } from '../utils/timelineLayers'

const mapRef = ref(null), layerControlRef = ref(null), selectedYear = ref(2020)
const overviewData = ref(), expansionData = ref(), ecologyData = ref()
const socioData = ref(), hotspotData = ref()

onMounted(loadPanelData)

async function loadPanelData() {
  const [overview, expansion, ecology, socio, hotspots] = await Promise.all([
    fetchOverviewData(),
    fetchExpansionData(),
    fetchEcologyData(),
    fetchSocioEconomicData(),
    fetchHotspotData(),
  ])
  overviewData.value = overview
  expansionData.value = expansion
  ecologyData.value = ecology
  socioData.value = socio
  hotspotData.value = hotspots
}

const tabs = [
  { key: 'dashboard', label: '总览', color: '#FFD43B' },
  { key: 'expansion', label: '建设扩张', color: '#FF6B6B' },
  { key: 'ecology', label: '生态环境', color: '#51CF66' },
  { key: 'scatter', label: '关联分析', color: '#BE4BDB' },
  { key: 'socio', label: '社会经济', color: '#4DABF7' },
  { key: 'hotspot', label: '热点乡镇', color: '#FF922B' },
  { key: 'ranking', label: '乡镇排名', color: '#20C997' },
]

function onMapLoaded() {}
function onFeatureClick() {}
function onLayerToggle({ groupId, layerName, year, visible }) {
  if (!mapRef.value) return
  const layerId = getYearLayerId(groupId, year)
  if (visible) mapRef.value.addWmsLayer(layerId, layerName)
  else mapRef.value.removeLayer(layerId)
}
function onModeToggle({ groupId, modeKey, visible }) {
  if (!mapRef.value) return
  const id = `${groupId}-${modeKey}`
  if (visible) mapRef.value.addWmsLayer(id, `expansion_mode_${modeKey}`)
  else mapRef.value.removeLayer(id)
}
function onYearChange({ year }) {
  for (const groupId of [...activeYearLayerGroups]) {
    const transition = buildYearLayerTransition({
      groupId,
      fromYear: selectedYear.value,
      toYear: year,
      activeYears: activeYearLayers[groupId] || [],
    })

    for (const layerId of transition.removeLayerIds) {
      mapRef.value?.removeLayer(layerId)
    }

    if (transition.addLayer) {
      mapRef.value?.addWmsLayer(transition.addLayer.id, transition.addLayer.layerName)
      setActiveYearLayers(groupId, [transition.addLayer.year])
      layerControlRef.value?.syncGroupYear(groupId, transition.addLayer.year)
    }
  }
}
function flyToDistrict({ name, center }) { if (mapRef.value) mapRef.value.flyTo(center, 11) }
</script>
