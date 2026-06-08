<template>
  <MapLayout :tabs="tabs" default-tab="dashboard">
    <template #map>
      <MapViewer ref="mapRef" @map-loaded="onMapLoaded" @feature-click="onFeatureClick" />
      <BottomBar :items="bottomItems" />
    </template>
    <template #layer-control>
      <LayerControl ref="layerControlRef" @layer-toggle="onLayerToggle" @mode-toggle="onModeToggle" />
    </template>
    <template #dashboard><DashboardView /></template>
    <template #expansion><ExpansionStats :data="expansionData" @district-click="flyToDistrict" /></template>
    <template #hotspot><HotspotView :data="hotspotData" @district-click="flyToDistrict" /></template>
    <template #ecology><EcologyStats :data="ecologyData" /></template>
    <template #scatter><ScatterRadarView @district-click="flyToDistrict" /></template>
    <template #socio><SocioEconomicStats :data="socioData" @district-click="flyToDistrict" /></template>
    <template #ranking><TownshipRanking /></template>
    <template #timeline>
      <TimelineSelector v-model="selectedYear" @change="onYearChange" />
    </template>
  </MapLayout>
</template>

<script setup>
import { ref } from 'vue'
import { Switch } from '@element-plus/icons-vue'
import MapLayout from '../components/layout/MapLayout.vue'
import MapViewer from '../components/map/MapViewer.vue'
import BottomBar from '../components/layout/BottomBar.vue'
import LayerControl from '../components/map/LayerControl.vue'
import TimelineSelector from '../components/map/TimelineSelector.vue'
import ExpansionStats from '../components/panel/ExpansionStats.vue'
import EcologyStats from '../components/panel/EcologyStats.vue'
import SocioEconomicStats from '../components/panel/SocioEconomicStats.vue'
import DashboardView from '../components/panel/DashboardView.vue'
import HotspotView from '../components/panel/HotspotView.vue'
import ScatterRadarView from '../components/panel/ScatterRadarView.vue'
import TownshipRanking from '../components/panel/TownshipRanking.vue'
import { getExpansionData, getEcologyData, getHotspotData } from '../data/mockAnalysis'
import { getSocioEconomicData } from '../data/mockSocioEconomic'
import { activeYearLayerGroups, activeYearLayers, setActiveYearLayers } from '../stores/layerState'
import { buildYearLayerTransition, getYearLayerId } from '../utils/timelineLayers'

const mapRef = ref(null)
const layerControlRef = ref(null)
const selectedYear = ref(2020)
const expansionData = ref(getExpansionData())
const ecologyData = ref(getEcologyData())
const socioData = ref(getSocioEconomicData())
const hotspotData = ref(getHotspotData())

const bottomItems = [
  { key: 'compare', label: '双期对比', icon: Switch, to: '/compare' },
]

const tabs = [
  { key: 'dashboard', label: '总览', color: '#FFD43B' },
  { key: 'expansion', label: '建设用地', color: '#FF6B6B' },
  { key: 'hotspot', label: '热点分析', color: '#FF922B' },
  { key: 'ecology', label: '生态评估', color: '#51CF66' },
  { key: 'scatter', label: '耦合响应', color: '#BE4BDB' },
  { key: 'socio', label: '社会经济', color: '#4DABF7' },
  { key: 'ranking', label: '分区统计', color: '#20C997' },
]

function onMapLoaded(map) {}
function onFeatureClick(event) {}
function onLayerToggle({ groupId, layerName, year, visible }) {
  if (!mapRef.value) return
  const layerId = getYearLayerId(groupId, year)
  if (visible) mapRef.value.addWmsLayer(layerId, layerName)
  else mapRef.value.removeLayer(layerId)
}
function onModeToggle({ groupId, modeKey, visible }) {
  if (!mapRef.value) return
  const layerId = `${groupId}-${modeKey}`
  if (visible) mapRef.value.addWmsLayer(layerId, `expansion_mode_${modeKey}`)
  else mapRef.value.removeLayer(layerId)
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
