<template>
  <div class="step-boundary">
    <h4 class="step-title">设置研究区边界</h4>
    <p class="step-desc">上传 GeoJSON 文件或手动输入边界坐标</p>

    <el-radio-group v-model="boundarySource" class="source-group">
      <el-radio value="upload">上传 GeoJSON</el-radio>
      <el-radio value="coords">输入坐标</el-radio>
    </el-radio-group>

    <!-- Upload GeoJSON -->
    <div v-if="boundarySource === 'upload'" class="upload-section">
      <el-upload
        class="geojson-upload"
        drag
        :auto-upload="false"
        :on-change="onGeoJSONChange"
        accept=".geojson,.json"
        :limit="1"
        :file-list="geojsonFiles"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">拖拽 GeoJSON 文件到此处</div>
        <div class="upload-hint">支持 .geojson .json</div>
      </el-upload>

      <div v-if="parsedBoundary" class="boundary-info">
        <el-icon color="#69DB7C"><CircleCheck /></el-icon>
        <span>边界已加载: {{ boundaryName || '自定义区域' }}</span>
        <span class="coord-count">{{ coordCount }} 个坐标点</span>
      </div>
    </div>

    <!-- Manual Coords -->
    <div v-if="boundarySource === 'coords'" class="coords-section">
      <p class="coords-hint">输入矩形边界 (经度, 纬度)，用逗号分隔</p>
      <div class="coord-inputs">
        <div class="coord-row">
          <label>左下角 (西南)</label>
          <el-input v-model="swCoord" placeholder="经度, 纬度  如: 116.0, 27.5" />
        </div>
        <div class="coord-row">
          <label>右上角 (东北)</label>
          <el-input v-model="neCoord" placeholder="经度, 纬度  如: 123.0, 33.8" />
        </div>
      </div>
      <el-button size="small" @click="applyCoords" :disabled="!swCoord || !neCoord">
        应用边界
      </el-button>
      <div v-if="parsedBoundary" class="boundary-info">
        <el-icon color="#69DB7C"><CircleCheck /></el-icon>
        <span>矩形边界已设置</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { UploadFilled, CircleCheck } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:modelValue'])

const boundarySource = ref('upload')
const geojsonFiles = ref([])
const parsedBoundary = ref(null)
const boundaryName = ref('')
const coordCount = ref(0)
const swCoord = ref('')
const neCoord = ref('')

function onGeoJSONChange(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const geojson = JSON.parse(e.target.result)
      if (!geojson.type && !geojson.features) {
        ElMessage.error('无效的 GeoJSON 文件')
        return
      }
      parsedBoundary.value = geojson
      boundaryName.value = file.name.replace(/\.(geojson|json)$/i, '')
      // Count coordinates
      let coords = []
      if (geojson.type === 'FeatureCollection' && geojson.features?.[0]) {
        coords = geojson.features[0].geometry?.coordinates?.flat(2) || []
      } else if (geojson.type === 'Feature' && geojson.geometry) {
        coords = geojson.geometry.coordinates?.flat(2) || []
      } else if (geojson.coordinates) {
        coords = geojson.coordinates.flat(2)
      }
      coordCount.value = coords.length
      emitUpdate()
      ElMessage.success('GeoJSON 加载成功')
    } catch {
      ElMessage.error('JSON 解析失败，请检查文件格式')
    }
  }
  reader.readAsText(file.raw)
}

function applyCoords() {
  const sw = swCoord.value.split(',').map(s => parseFloat(s.trim()))
  const ne = neCoord.value.split(',').map(s => parseFloat(s.trim()))

  if (sw.length !== 2 || ne.length !== 2 || sw.some(isNaN) || ne.some(isNaN)) {
    ElMessage.error('坐标格式错误，请用 "经度, 纬度" 格式')
    return
  }

  parsedBoundary.value = {
    type: 'Polygon',
    coordinates: [[
      [sw[0], sw[1]],
      [ne[0], sw[1]],
      [ne[0], ne[1]],
      [sw[0], ne[1]],
      [sw[0], sw[1]],
    ]],
  }
  boundaryName.value = `矩形 (${sw[0]},${sw[1]}) - (${ne[0]},${ne[1]})`
  coordCount.value = 5
  emitUpdate()
  ElMessage.success('边界已设置')
}

function emitUpdate() {
  emit('update:modelValue', {
    ...props.modelValue,
    boundaryGeoJSON: parsedBoundary.value,
    boundaryName: boundaryName.value,
  })
}
</script>

<style scoped>
.step-boundary { padding: 8px 0; }

.step-title { color: #ddd; margin: 0 0 6px; font-size: 15px; }
.step-desc { color: #888; font-size: 13px; margin: 0 0 16px; }

.source-group { margin-bottom: 16px; }

.upload-section { margin-top: 12px; }

.geojson-upload {
  border: 1px dashed #444;
  border-radius: 8px;
  background: #222;
}
.geojson-upload:hover { border-color: #666; }
.upload-icon { font-size: 32px; color: #555; }
.upload-text { color: #aaa; margin-top: 6px; font-size: 13px; }
.upload-hint { color: #555; font-size: 12px; margin-top: 4px; }

.boundary-info {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding: 10px 14px;
  background: rgba(105, 219, 124, 0.1);
  border: 1px solid rgba(105, 219, 124, 0.3);
  border-radius: 8px;
  color: #bbb;
  font-size: 13px;
}
.coord-count { color: #666; margin-left: auto; font-size: 12px; }

.coords-section { margin-top: 12px; }
.coords-hint { color: #888; font-size: 12px; margin: 0 0 12px; }
.coord-inputs { display: flex; flex-direction: column; gap: 12px; margin-bottom: 12px; }
.coord-row { display: flex; align-items: center; gap: 10px; }
.coord-row label { color: #aaa; font-size: 13px; white-space: nowrap; min-width: 90px; }
</style>
