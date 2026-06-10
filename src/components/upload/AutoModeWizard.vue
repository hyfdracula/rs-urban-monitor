<template>
  <div class="auto-wizard">
    <div class="wizard-header">
      <el-button text size="small" @click="$emit('back')">
        <el-icon><ArrowLeft /></el-icon>
        返回模式选择
      </el-button>
      <h3 class="wizard-title">自动模式 — 一键分析</h3>
    </div>

    <!-- Step 1: Upload boundary + year selection -->
    <div v-if="step === 'upload'" class="step-content">
      <h4 class="step-title">上传研究区边界</h4>
      <p class="step-desc">上传 GeoJSON / Shapefile / GeoTIFF 边界文件</p>

      <el-input
        v-model="boundaryName"
        placeholder="请填写边界名称，如：上海市"
        class="name-input"
        :class="{ 'name-error': nameError }"
        @input="nameError = false"
      />

      <el-upload
        drag
        :auto-upload="false"
        :on-change="onFileChange"
        accept=".geojson,.json,.zip,.tif,.tiff"
        :limit="1"
        :show-file-list="false"
        class="boundary-upload"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">{{ selectedFile ? selectedFile.name : '拖拽文件到此处 / 点击此处上传文件' }}</div>
        <div class="upload-hint">支持 .geojson .json .zip .tif</div>
      </el-upload>

      <!-- 年份选择器 -->
      <div class="year-section">
        <h5 class="section-label">选择分析年份（最多5个）</h5>

        <div class="year-input-row">
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
          <el-tag
            v-for="y in selectedYears"
            :key="y"
            closable
            type="primary"
            effect="plain"
            @close="removeYear(y)"
          >
            {{ y }}
          </el-tag>
          <span v-if="!selectedYears.length" class="no-years">请选择至少1个年份</span>
        </div>

        <!-- 快捷选择 -->
        <div class="quick-picks">
          <span class="quick-label">快捷：</span>
          <el-button size="small" text @click="quickPick([2000, 2005, 2010, 2015, 2020])">2000-2020</el-button>
          <el-button size="small" text @click="quickPick([1990, 2000, 2010, 2020])">1990-2020</el-button>
          <el-button size="small" text @click="quickPick([2010, 2015, 2020])">2010-2020</el-button>
        </div>

      <!-- 指标选择 -->
      <StepIndicators v-model="indicatorConfig" />

      <!-- GDP 数据可用性警告 -->
      <el-alert
        v-if="gdpWarning"
        type="warning"
        :closable="false"
        style="margin-top: 8px;"
      >
        {{ gdpWarning }}
      </el-alert>
      </div>

      <div class="start-btn-wrapper">
        <el-button
          type="primary"
          class="start-btn"
          :loading="uploading"
          :disabled="!selectedFile || !selectedYears.length"
          @click="startCompute"
        >
          {{ uploading ? '上传中...' : '开始一键分析' }}
        </el-button>
      </div>

      <!-- 数据可用性确认弹窗 -->
      <el-dialog
        v-model="showConfirmDialog"
        title="数据可用性提示"
        width="480px"
        :close-on-click-modal="false"
        class="confirm-dialog"
        destroy-on-close
      >
        <div class="confirm-content">
          <!-- 传感器概览 -->
          <div class="sensor-overview">
            <h4>本次分析数据源</h4>
            <div class="sensor-table">
              <div v-for="y in selectedYears" :key="y" class="sensor-row">
                <span class="year-label">{{ y }} 年</span>
                <span class="sensor-label">{{ dataWarnings.sensorMap[y] || '未知' }}</span>
                <span class="data-tags">
                  <el-tag size="small" :type="(y >= 1990 && y <= 2022) ? 'success' : 'danger'" effect="plain">
                    GDP{{ (y >= 1990 && y <= 2022) ? '✓' : '✗' }}
                  </el-tag>
                  <el-tag size="small" :type="(y >= 2000 && y <= 2020) ? 'success' : 'danger'" effect="plain">
                    人口{{ (y >= 2000 && y <= 2020) ? '✓' : '✗' }}
                  </el-tag>
                </span>
              </div>
            </div>
          </div>

          <!-- 警告列表 -->
          <div v-if="dataWarnings.warnings.length" class="warning-list">
            <h4>需要注意的问题</h4>
            <div
              v-for="(w, i) in dataWarnings.warnings"
              :key="i"
              class="warning-item"
              :class="'warning-' + w.type"
            >
              <el-icon :size="16">
                <component :is="w.icon" />
              </el-icon>
              <div class="warning-text">
                <span class="warning-title">{{ w.title }}</span>
                <span class="warning-detail">{{ w.detail }}</span>
              </div>
            </div>
          </div>

          <div class="confirm-note">
            缺失的数据指标将在报告中标记为"数据暂缺"，不影响其他指标的计算。
          </div>
        </div>

        <template #footer>
          <el-button @click="showConfirmDialog = false">取消</el-button>
          <el-button type="primary" @click="doUpload">
            <el-icon><VideoPlay /></el-icon>
            我已了解，开始分析
          </el-button>
        </template>
      </el-dialog>

      <!-- 指标影响确认弹窗 -->
      <IndicatorImpactDialog
        v-model="showImpactDialog"
        :selected="indicatorConfig.indicators || []"
        @cancel="showImpactDialog = false"
        @confirm="onImpactConfirm"
      />
    </div>

    <!-- Error -->
    <div v-else-if="step === 'error'" class="step-content">
      <div class="done-box error">
        <el-icon color="#FF6B6B" :size="48"><CircleClose /></el-icon>
        <h4>分析失败</h4>
        <p>{{ errorMsg }}</p>
      </div>
      <el-button @click="reset">重试</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  ArrowLeft, UploadFilled, CircleClose,
  WarningFilled, Warning, InfoFilled, User, VideoPlay,
} from '@element-plus/icons-vue'
import { ElMessage, ElNotification } from 'element-plus'
import { uploadBoundary } from '../../api'
import StepIndicators from './StepIndicators.vue'
import IndicatorImpactDialog from './IndicatorImpactDialog.vue'

// All 6 indicator keys (used for default and impact check)
const ALL_INDICATORS = ['rsei', 'construction', 'expansion', 'nightLight', 'population', 'gdp']

const emit = defineEmits(['back', 'done'])

const step = ref('upload')
const boundaryName = ref('')
const selectedFile = ref(null)
const selectedYears = ref([2020])
const uploading = ref(false)
const taskId = ref('')
const errorMsg = ref('')
const nameError = ref(false)
const showConfirmDialog = ref(false)
const showImpactDialog = ref(false)
const pickerValue = ref(null)
const indicatorConfig = ref({ indicators: [...ALL_INDICATORS] })

const currentYear = new Date().getFullYear()

// ─── 数据可用性分析 ───
const dataWarnings = computed(() => {
  const years = selectedYears.value
  const warnings = []
  const sensorMap = {}

  years.forEach(y => {
    if (y >= 2021) sensorMap[y] = 'Landsat 9 OLI-2'
    else if (y >= 2013) sensorMap[y] = 'Landsat 8 OLI'
    else if (y >= 1999 && y <= 2003) sensorMap[y] = 'Landsat 7 ETM+'
    else sensorMap[y] = 'Landsat 5 TM'
  })

  // 1. GDP 数据缺失（Kummu et al. 2025 仅覆盖 1990-2022）
  const noGDP = years.filter(y => y < 1990 || y > 2022)
  if (noGDP.length > 0) {
    warnings.push({
      type: 'error',
      icon: 'WarningFilled',
      title: 'GDP 数据缺失',
      detail: `年份 ${noGDP.join('、')} 无 GDP 数据（Kummu 数据集仅覆盖 1990-2022），GDP 相关指标将显示为"数据暂缺"`,
    })
  }

  // 2. 人口数据缺失（WorldPop 仅 2000-2020）
  const noPop = years.filter(y => y < 2000 || y > 2020)
  if (noPop.length > 0) {
    warnings.push({
      type: 'warning',
      icon: 'User',
      title: '人口数据缺失',
      detail: `年份 ${noPop.join('、')} 无 WorldPop 人口数据（仅 2000-2020 可用），人口指标将显示为 0`,
    })
  }

  // 3. Landsat 5 后期数据质量风险
  const lt5Late = years.filter(y => y >= 2011 && y <= 2012)
  if (lt5Late.length > 0) {
    warnings.push({
      type: 'warning',
      icon: 'Warning',
      title: 'Landsat 5 数据质量风险',
      detail: `年份 ${lt5Late.join('、')} 使用 Landsat 5 TM，该卫星在 2011-2012 年出现放大器漂移，数据质量可能下降`,
    })
  }

  // 4. 跨传感器对比
  const sensors = [...new Set(Object.values(sensorMap))]
  if (sensors.length >= 2) {
    warnings.push({
      type: 'info',
      icon: 'InfoFilled',
      title: '跨传感器对比',
      detail: `所选年份涉及 ${sensors.length} 种传感器（${sensors.join('、')}），不同传感器的波段响应差异可能影响年际对比的一致性`,
    })
  }

  // 5. Landsat 7 SLC-off 说明
  const le07 = years.filter(y => y >= 1999 && y <= 2003)
  if (le07.length > 0) {
    warnings.push({
      type: 'info',
      icon: 'InfoFilled',
      title: 'Landsat 7 ETM+ 说明',
      detail: `年份 ${le07.join('、')} 使用 Landsat 7 ETM+，2003年5月后存在 SLC-off 条纹，代码已用中值合成缓解`,
    })
  }

  // 6. VIIRS/DMSP 交叉年份
  const overlap = years.filter(y => y === 2012 || y === 2013)
  if (overlap.length > 0) {
    warnings.push({
      type: 'info',
      icon: 'InfoFilled',
      title: '夜灯数据源切换',
      detail: `年份 ${overlap.join('、')} 处于 DMSP-OLS → VIIRS 数据源切换期，夜灯指标可能存在断档`,
    })
  }

  return {
    warnings,
    sensorMap,
    hasBlocker: warnings.some(w => w.type === 'error'),
  }
})

// 年份选择区域的内联 GDP 警告
const gdpWarning = computed(() => {
  const noGDP = selectedYears.value.filter(y => y < 1990 || y > 2022)
  if (noGDP.length > 0) {
    return `年份 ${noGDP.join('、')} 无 GDP 数据，经济指标将显示为"数据暂缺"`
  }
  return ''
})

function disableDate(date) {
  const y = date.getFullYear()
  return y < 1984 || y > currentYear
}

function addYear(val) {
  if (!val) return
  const y = new Date(val).getFullYear()
  // 选完立即清空 picker，允许连续选不同年份
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

function onFileChange(file) {
  selectedFile.value = file
}

async function startCompute() {
  if (!selectedFile.value) return
  if (!boundaryName.value.trim()) {
    nameError.value = true
    return
  }
  if (!selectedYears.value.length) {
    ElMessage.warning('请至少选择1个年份')
    return
  }

  // Validate at least 1 indicator selected
  const selected = indicatorConfig.value.indicators || []
  if (!selected.length) {
    ElMessage.warning('请至少选择一个分析指标')
    return
  }

  // Check if any indicators are unselected → show impact dialog first
  const unselected = ALL_INDICATORS.filter(k => !selected.includes(k))
  if (unselected.length > 0) {
    showImpactDialog.value = true
    return
  }

  // All selected → skip impact dialog, go straight to confirm
  showConfirmDialog.value = true
}

function onImpactConfirm() {
  // User confirmed after seeing impact → proceed to data availability dialog
  showConfirmDialog.value = true
}

async function doUpload() {
  showConfirmDialog.value = false
  uploading.value = true
  try {
    const config = { indicators: indicatorConfig.value.indicators || [] }
    const data = await uploadBoundary(
      selectedFile.value.raw,
      boundaryName.value,
      selectedYears.value,
      'online',
      (e) => { /* upload progress */ },
      config,
    )
    taskId.value = data.task_id

    ElMessage.success('边界已上传，计算已启动')
    // 立即通知父组件，进度交给右侧任务面板
    emit('done', { taskId: data.task_id })
  } catch (err) {
    // 区分：网络超时（后端可能已收到并创建了任务）vs 后端明确拒绝
    const isNetworkError = !err.response // timeout / CORS / 连接断开
    if (isNetworkError) {
      ElMessage.warning('网络响应超时，任务可能已提交，请到任务面板确认')
      emit('done', { taskId: null })
    } else {
      const detail = err.response?.data?.detail
      if (detail) {
        ElMessage.error(detail)
      } else {
        ElMessage.error('上传失败')
      }
      step.value = 'error'
      errorMsg.value = detail || '上传失败，请检查网络连接'
    }
  }
  uploading.value = false
}

function reset() {
  step.value = 'upload'
  selectedFile.value = null
  boundaryName.value = ''
  selectedYears.value = [2020]
  nameError.value = false
  taskId.value = ''
}
</script>

<style scoped>
.auto-wizard { max-width: 560px; margin: 0 auto; }

.wizard-header {
  display: flex; align-items: center; gap: 12px; margin-bottom: 20px;
}
.wizard-title { color: #ddd; margin: 0; font-size: 15px; }

.step-content { padding: 8px 0; }
.step-title { color: #ddd; margin: 0 0 6px; font-size: 15px; }
.step-desc { color: #888; font-size: 13px; margin: 0 0 16px; }

.name-input { margin-bottom: 14px; }
.name-input.name-error :deep(.el-input__wrapper) {
  border-color: #FF6B6B;
  box-shadow: 0 0 0 1px #FF6B6B inset;
}

.boundary-upload {
  border: 1px dashed #444; border-radius: 8px; background: #222; width: 100%;
  margin-bottom: 16px;
}
.boundary-upload :deep(.el-upload-dragger) {
  padding: 10px 16px;
  display: flex; align-items: center; gap: 10px;
  background: transparent; border: none; border-radius: 8px;
}
.boundary-upload:hover { border-color: #666; }
.upload-icon { font-size: 20px; color: #555; }
.upload-text { color: #aaa; font-size: 13px; }
.upload-hint { color: #555; font-size: 11px; }

/* Year selector */
.year-section {
  background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px;
  padding: 12px; margin-bottom: 16px;
}
.section-label { color: #aaa; margin: 0 0 10px; font-size: 13px; font-weight: 500; }

.year-input-row {
  display: flex; align-items: center; gap: 10px; margin-bottom: 8px;
}
.year-count { color: #666; font-size: 12px; }

.year-chips {
  display: flex; flex-wrap: wrap; gap: 6px; min-height: 28px;
  align-items: center;
}
.no-years { color: #555; font-size: 12px; font-style: italic; }

.quick-picks {
  display: flex; align-items: center; gap: 4px; margin-top: 8px;
}
.quick-label { color: #666; font-size: 11px; }

.start-btn-wrapper {
  position: sticky;
  bottom: 0;
  z-index: 2;
  padding: 10px 0 0;
  background: linear-gradient(to bottom, transparent, var(--el-dialog-bg-color, #1a1a1a) 40%);
}
.start-btn { width: 100%; }

/* Error */
.done-box {
  text-align: center; padding: 24px;
  border-radius: 12px; margin-bottom: 16px;
}
.done-box.error {
  background: rgba(255, 107, 107, 0.06); border: 1px solid rgba(255, 107, 107, 0.2);
}
.done-box h4 { color: #ddd; margin: 12px 0 4px; }
.done-box p { color: #888; font-size: 13px; margin: 0; }

/* ── 数据可用性确认弹窗 ── */
.confirm-content { color: #ccc; }

.sensor-overview h4,
.warning-list h4 {
  color: #ddd; font-size: 14px; margin: 0 0 10px;
}

.sensor-table {
  background: #1a1a1a; border: 1px solid #2a2a2a;
  border-radius: 8px; padding: 8px; margin-bottom: 16px;
}

.sensor-row {
  display: flex; align-items: center; gap: 12px;
  padding: 6px 8px; border-bottom: 1px solid #222;
}
.sensor-row:last-child { border-bottom: none; }

.year-label {
  color: #4DABF7; font-weight: 600; font-size: 13px; min-width: 60px;
}
.sensor-label { color: #aaa; font-size: 12px; flex: 1; }
.data-tags { display: flex; gap: 4px; }

.warning-list { margin-bottom: 12px; }

.warning-item {
  display: flex; gap: 10px; padding: 10px 12px;
  border-radius: 8px; margin-bottom: 8px; align-items: flex-start;
}
.warning-error {
  background: rgba(255, 107, 107, 0.08); border: 1px solid rgba(255, 107, 107, 0.2);
  color: #FF6B6B;
}
.warning-warning {
  background: rgba(255, 146, 43, 0.08); border: 1px solid rgba(255, 146, 43, 0.2);
  color: #FF922B;
}
.warning-info {
  background: rgba(77, 171, 247, 0.08); border: 1px solid rgba(77, 171, 247, 0.2);
  color: #4DABF7;
}
.warning-text { display: flex; flex-direction: column; gap: 2px; }
.warning-title { font-weight: 600; font-size: 13px; }
.warning-detail { font-size: 12px; opacity: 0.85; line-height: 1.5; }

.confirm-note {
  color: #666; font-size: 12px; text-align: center;
  padding: 8px; border-top: 1px solid #222;
}
</style>
