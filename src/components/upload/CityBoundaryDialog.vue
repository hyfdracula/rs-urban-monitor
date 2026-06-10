<template>
  <el-dialog
    v-model="dialogVisible"
    title="获取城市边界"
    width="540px"
    top="5vh"
    :close-on-click-modal="false"
    class="city-dialog"
    destroy-on-close
  >
    <div class="dialog-body-scroll">
    <!-- Mode tabs -->
    <div class="mode-tabs">
      <button :class="{ active: mode === 'search' }" @click="mode = 'search'">🔍 搜索</button>
      <button :class="{ active: mode === 'browse' }" @click="mode = 'browse'">🗺️ 按省份</button>
      <button :class="{ active: mode === 'adcode' }" @click="mode = 'adcode'">📋 区划代码</button>
    </div>

    <!-- ═══ Search mode ═══ -->
    <div v-if="mode === 'search'" class="panel">
      <el-autocomplete
        v-model="keyword"
        :fetch-suggestions="queryCity"
        placeholder="输入城市名，如：成都、深圳、拉萨"
        :trigger-on-focus="true"
        highlight-first-item
        @select="onSelect"
        clearable
        style="width: 100%"
      >
        <template #default="{ item }">
          <div class="sg-row">
            <span class="sg-name">{{ item.name }}</span>
            <span v-if="item.parent" class="sg-sub">{{ item.parent }}</span>
            <span v-if="item.level === 'province'" class="sg-badge">省级</span>
          </div>
        </template>
      </el-autocomplete>
      <div class="load-hint done-hint">
        <span>已收录 {{ citiesCount }} 个城市 / {{ provincesCount }} 个省级行政区</span>
      </div>
    </div>

    <!-- ═══ Browse mode ═══ -->
    <div v-if="mode === 'browse'" class="panel">
      <template v-if="!browsingProv">
        <p class="browse-hint">选择省份查看下属城市</p>
        <div class="prov-grid">
          <div v-for="p in PROVINCES" :key="p.adcode" class="prov-chip" @click="clickProvince(p)">
            {{ p.name }}
          </div>
        </div>
      </template>
      <template v-else>
        <div class="browse-head">
          <el-button text size="small" @click="browsingProv = null">← 返回</el-button>
          <span class="browse-title">{{ browsingProv.name }}</span>
        </div>
        <div class="city-grid">
          <div
            v-for="c in citiesOf(browsingProv.adcode)"
            :key="c.adcode"
            class="city-chip"
            @click="onSelect(c)"
          >
            {{ c.name }}
          </div>
          <div v-if="!citiesOf(browsingProv.adcode).length" class="load-hint">
            该区域为直辖市，直接点击上方省份名即可
          </div>
        </div>
      </template>
    </div>

    <!-- ═══ Adcode mode ═══ -->
    <div v-if="mode === 'adcode'" class="panel">
      <p class="browse-hint">直接输入6位行政区划代码获取边界</p>
      <el-input v-model="adcodeInput" placeholder="如：320100（南京）、540100（拉萨）" maxlength="6" clearable />
      <el-button
        style="margin-top: 10px; width: 100%"
        :disabled="!/^\d{6}$/.test(adcodeInput)"
        @click="fetchByAdcode"
      >
        获取边界
      </el-button>
    </div>

    <!-- ═══ Shared status ═══ -->
    <div v-if="boundaryLoading" class="status-box loading-box">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>正在获取「{{ selectedCity?.name || adcodeInput }}」的边界...</span>
    </div>
    <div v-if="geojsonData && !boundaryLoading" class="status-box success-box">
      <el-icon color="#69DB7C"><CircleCheckFilled /></el-icon>
      <span>已获取「{{ selectedCity?.name }}」边界（{{ featureCount }} 个区域）</span>
    </div>
    <div v-if="errorMsg" class="status-box error-box">
      <el-icon color="#FF6B6B"><CircleCloseFilled /></el-icon>
      <span>{{ errorMsg }}</span>
    </div>

    <!-- ═══ 分析配置区（获取成功后展开） ═══ -->
    <div v-if="showAnalysisPanel" class="analysis-panel">
      <div class="panel-divider"></div>

      <!-- 年份 -->
      <div class="form-item">
        <label class="form-label">选择分析年份（最多5个）</label>
        <div class="year-row">
          <el-date-picker
            v-model="pickerValue"
            type="year"
            placeholder="添加年份"
            :disabled-date="disableDate"
            :disabled="selectedYears.length >= 5"
            :clearable="true"
            size="small"
            style="width: 140px;"
            @change="addYear"
          />
          <span class="year-count">{{ selectedYears.length }} / 5</span>
        </div>
        <div class="year-chips">
          <el-tag v-for="y in selectedYears" :key="y" closable type="primary" effect="plain" @close="removeYear(y)">
            {{ y }}
          </el-tag>
          <span v-if="!selectedYears.length" class="no-years">请选择至少1个年份</span>
        </div>
        <div class="quick-picks">
          <span class="quick-label">快捷：</span>
          <el-button size="small" text @click="quickPick([2000, 2005, 2010, 2015, 2020])">2000-2020</el-button>
          <el-button size="small" text @click="quickPick([2010, 2015, 2020])">2010-2020</el-button>
        </div>
      </div>

      <!-- 指标 -->
      <StepIndicators v-model="indicatorConfig" />
    </div>

    </div>
    <!-- ╔════ dialog-body-scroll END ════╝ -->

    <!-- ═══ Footer (must be direct child of el-dialog) ═══ -->
    <template #footer>
      <div class="city-footer">
        <el-button @click="handleDownload" :disabled="!geojsonData" :loading="downloading">
          <el-icon><Download /></el-icon> 下载 GeoJSON
        </el-button>
        <el-button
          v-if="geojsonData && !showAnalysisPanel"
          type="primary"
          @click="showAnalysisPanel = true"
        >
          <el-icon><VideoPlay /></el-icon> 进入分析
        </el-button>
        <el-button
          v-if="showAnalysisPanel"
          type="primary"
          :loading="submitting"
          :disabled="!selectedYears.length"
          @click="startCompute"
        >
          开始计算
        </el-button>
      </div>
    </template>

    <!-- 影响确认弹窗 -->
    <IndicatorImpactDialog
      v-model="showImpactDialog"
      :selected="indicatorConfig.indicators || []"
      @confirm="onImpactConfirm"
      @cancel="showImpactDialog = false"
    />
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  Loading, CircleCheckFilled, CircleCloseFilled,
  Download, VideoPlay,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { PROVINCES, CITIES, ALL_AREAS, MUNICIPALITIES } from '../../data/chinaCities'
import { uploadBoundary } from '../../api'
import StepIndicators from './StepIndicators.vue'
import IndicatorImpactDialog from './IndicatorImpactDialog.vue'

const ALL_INDICATORS = ['rsei', 'construction', 'expansion', 'nightLight', 'population', 'gdp']

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['update:visible', 'done'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val),
})

const citiesCount = CITIES.length
const provincesCount = PROVINCES.length

// ─── City selection state ───
const mode = ref('search')
const keyword = ref('')
const selectedCity = ref(null)
const geojsonData = ref(null)
const boundaryLoading = ref(false)
const downloading = ref(false)
const errorMsg = ref('')

// Browse
const browsingProv = ref(null)

// Adcode
const adcodeInput = ref('')

// ─── Analysis config state ───
const showAnalysisPanel = ref(false)
const currentYear = new Date().getFullYear()
const selectedYears = ref([])
const pickerValue = ref(null)
const indicatorConfig = ref({ indicators: [...ALL_INDICATORS] })
const showImpactDialog = ref(false)
const submitting = ref(false)

const featureCount = computed(() => geojsonData.value?.features?.length || 0)

// ─── DataV 边界接口 ───
const DATAV = 'https://geo.datav.aliyun.com/areas_v3'

function citiesOf(provAdcode) {
  return CITIES.filter(c => c.parentAdcode === provAdcode)
}

// ─── Search ───
function queryCity(qs, cb) {
  const q = (qs || '').trim()
  if (!q) {
    cb(ALL_AREAS.slice(0, 15).map(c => ({ value: c.name, ...c })))
    return
  }
  if (/^\d{6}$/.test(q)) {
    cb([{ value: `区划代码: ${q}`, name: q, adcode: q, level: 'adcode' }])
    return
  }
  const hits = ALL_AREAS.filter(c => c.name.includes(q)).map(c => ({ value: c.name, ...c }))
  cb(hits.slice(0, 20))
}

// ─── Browse ───
function clickProvince(prov) {
  if (MUNICIPALITIES.has(prov.adcode) || !citiesOf(prov.adcode).length) {
    onSelect(prov)
    return
  }
  browsingProv.value = prov
}

// ─── Fetch boundary ───
function onSelect(item) {
  selectedCity.value = item
  keyword.value = item.name
  // 重置分析配置
  showAnalysisPanel.value = false
  selectedYears.value = []
  pickerValue.value = null
  indicatorConfig.value = { indicators: [...ALL_INDICATORS] }
  fetchBoundary(item.adcode)
}

function fetchByAdcode() {
  selectedCity.value = { name: adcodeInput.value, adcode: adcodeInput.value }
  showAnalysisPanel.value = false
  selectedYears.value = []
  pickerValue.value = null
  indicatorConfig.value = { indicators: [...ALL_INDICATORS] }
  fetchBoundary(adcodeInput.value)
}

async function fetchBoundary(adcode) {
  boundaryLoading.value = true
  geojsonData.value = null
  errorMsg.value = ''
  try {
    const resp = await fetch(`${DATAV}/bound/${adcode}.json`)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const data = await resp.json()
    if (!data.features?.length) throw new Error('无边界数据')
    geojsonData.value = data
  } catch (err) {
    errorMsg.value = `获取边界失败：${err.message}`
  } finally {
    boundaryLoading.value = false
  }
}

// ─── Download ───
function handleDownload() {
  if (!geojsonData.value || !selectedCity.value) return
  downloading.value = true
  try {
    const name = selectedCity.value.name
    const blob = new Blob([JSON.stringify(geojsonData.value, null, 2)], { type: 'application/geo+json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `${name}.geojson`
    document.body.appendChild(a); a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success(`${name}.geojson 已下载`)
  } finally { downloading.value = false }
}

// ─── Year helpers ───
function disableDate(date) {
  const y = date.getFullYear()
  return y < 1984 || y > currentYear
}

function addYear(val) {
  if (!val) return
  const y = new Date(val).getFullYear()
  pickerValue.value = null
  if (y < 1984 || y > currentYear) return
  if (selectedYears.value.includes(y)) return
  if (selectedYears.value.length >= 5) {
    ElMessage.warning('最多选择5个年份')
    return
  }
  selectedYears.value.push(y)
  selectedYears.value.sort()
}

function removeYear(y) {
  selectedYears.value = selectedYears.value.filter(v => v !== y)
}

function quickPick(years) {
  selectedYears.value = [...years]
}

// ─── Compute ───
function startCompute() {
  if (!selectedYears.value.length) {
    ElMessage.warning('请至少选择1个年份')
    return
  }

  const indicators = indicatorConfig.value.indicators || []
  if (!indicators.length) {
    ElMessage.warning('请至少选择一个分析指标')
    return
  }

  const unselected = ALL_INDICATORS.filter(k => !indicators.includes(k))
  if (unselected.length > 0) {
    showImpactDialog.value = true
    return
  }

  doUpload()
}

function onImpactConfirm() {
  doUpload()
}

async function doUpload() {
  if (!geojsonData.value || !selectedCity.value) return
  submitting.value = true

  try {
    // GeoJSON → File → 复用 uploadBoundary
    const cityName = selectedCity.value.name
    const blob = new Blob([JSON.stringify(geojsonData.value)], { type: 'application/geo+json' })
    const file = new File([blob], `${cityName}.geojson`, { type: 'application/geo+json' })
    const config = { indicators: indicatorConfig.value.indicators || [] }

    const data = await uploadBoundary(file, cityName, selectedYears.value, 'online', null, config)

    ElMessage.success('边界已上传，计算已启动')
    dialogVisible.value = false
    emit('done', { taskId: data.task_id, url: data.url })
  } catch (err) {
    const isNetworkError = !err.response
    if (isNetworkError) {
      ElMessage.warning('网络响应超时，任务可能已提交，请到任务面板确认')
      dialogVisible.value = false
      emit('done', { taskId: null, url: null })
    } else {
      const detail = err.response?.data?.detail
      ElMessage.error(detail || '上传失败，请重试')
    }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.dialog-body-scroll {
  max-height: 70vh;
  overflow-y: auto;
}

.mode-tabs {
  display: flex; gap: 4px; margin-bottom: 14px;
  background: #222; border-radius: 8px; padding: 3px;
}
.mode-tabs button {
  flex: 1; padding: 7px; border: none; border-radius: 6px;
  background: none; color: #888; font-size: 13px; cursor: pointer; transition: all .2s;
}
.mode-tabs button:hover { color: #ccc; }
.mode-tabs button.active { background: #333; color: #fff; }

.panel { min-height: 100px; }

/* Search suggestions */
.sg-row { display: flex; align-items: center; gap: 8px; }
.sg-name { color: #ddd; }
.sg-sub { color: #666; font-size: 12px; }
.sg-badge { font-size: 10px; background: #333; color: #aaa; padding: 1px 5px; border-radius: 3px; }

/* Load hint */
.load-hint {
  display: flex; align-items: center; gap: 6px;
  color: #888; font-size: 12px; margin-top: 10px;
}
.done-hint { color: #69DB7C; }

/* Browse */
.browse-hint { color: #888; font-size: 13px; margin: 0 0 10px; }
.browse-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.browse-title { color: #ccc; font-size: 14px; font-weight: 500; }

.prov-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(72px, 1fr));
  gap: 6px; max-height: 260px; overflow-y: auto;
}
.prov-chip {
  padding: 6px 4px; text-align: center; font-size: 12px;
  background: #252525; border: 1px solid #333; border-radius: 6px;
  color: #ccc; cursor: pointer; transition: all .2s;
}
.prov-chip:hover { border-color: #4DABF7; color: #4DABF7; }

.city-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  gap: 6px; max-height: 260px; overflow-y: auto;
}
.city-chip {
  padding: 8px 6px; text-align: center; font-size: 13px;
  background: #1a1a1a; border: 1px solid #333; border-radius: 6px;
  color: #ddd; cursor: pointer; transition: all .2s;
}
.city-chip:hover { border-color: #69DB7C; color: #69DB7C; }

/* Status boxes */
.status-box {
  display: flex; align-items: center; gap: 8px;
  margin-top: 14px; padding: 10px 14px; border-radius: 8px; font-size: 13px;
}
.loading-box { background: rgba(77,171,247,.08); border: 1px solid rgba(77,171,247,.2); color: #4DABF7; }
.success-box { background: rgba(105,219,124,.08); border: 1px solid rgba(105,219,124,.2); color: #69DB7C; }
.error-box   { background: rgba(255,107,107,.08); border: 1px solid rgba(255,107,107,.2); color: #FF6B6B; }

/* Analysis panel */
.panel-divider {
  border-top: 1px solid #2a2a2a;
  margin: 14px 0 12px;
}

.form-item { margin-bottom: 12px; }
.form-label {
  display: block; color: #ccc; font-size: 13px; margin-bottom: 6px;
}

.year-row {
  display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
}
.year-count { color: #888; font-size: 12px; }

.year-chips {
  display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px;
}
.no-years { color: #666; font-size: 12px; }

.quick-picks {
  display: flex; align-items: center; gap: 4px; font-size: 12px;
}
.quick-label { color: #666; }

.city-footer {
  display: flex; justify-content: flex-end; gap: 10px;
}
</style>
