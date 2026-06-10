<template>
  <el-dialog
    v-model="visible"
    :title="`重新计算「${boundary?.name || ''}」`"
    width="480px"
    :close-on-click-modal="false"
    destroy-on-close
    class="recompute-dialog"
  >
    <!-- 名称 -->
    <div class="form-item">
      <label class="form-label">边界名称</label>
      <el-input v-model="inputName" placeholder="输入名称" maxlength="100" />
    </div>

    <!-- 年份选择 -->
    <div class="form-item">
      <label class="form-label">选择分析年份（最多5个）</label>

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

      <div class="quick-picks">
        <span class="quick-label">快捷：</span>
        <el-button size="small" text @click="quickPick([2000, 2005, 2010, 2015, 2020])">2000-2020</el-button>
        <el-button size="small" text @click="quickPick([1990, 2000, 2010, 2020])">1990-2020</el-button>
        <el-button size="small" text @click="quickPick([2010, 2015, 2020])">2010-2020</el-button>
      </div>

      <el-alert
        v-if="gdpWarning"
        type="warning"
        :closable="false"
        style="margin-top: 8px;"
      >
        {{ gdpWarning }}
      </el-alert>
    </div>

    <!-- 指标选择 -->
    <div class="form-item">
      <StepIndicators v-model="indicatorConfig" />
    </div>

    <!-- 底部按钮 -->
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button
        type="primary"
        :loading="submitting"
        :disabled="!selectedYears.length"
        @click="startCompute"
      >
        开始计算
      </el-button>
    </template>

    <!-- 影响确认弹窗 -->
    <IndicatorImpactDialog
      v-model="showImpactDialog"
      :selected="indicatorConfig.indicators"
      @confirm="onImpactConfirm"
      @cancel="showImpactDialog = false"
    />
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { recomputeBoundary } from '../../api'
import StepIndicators from './StepIndicators.vue'
import IndicatorImpactDialog from './IndicatorImpactDialog.vue'

const ALL_INDICATORS = ['rsei', 'construction', 'expansion', 'nightLight', 'population', 'gdp']

const props = defineProps({
  visible: { type: Boolean, default: false },
  boundary: { type: Object, default: null },
})
const emit = defineEmits(['update:visible', 'done'])

const visible = computed({
  get: () => props.visible,
  set: (v) => emit('update:visible', v),
})

const currentYear = new Date().getFullYear()
const submitting = ref(false)
const inputName = ref('')
const selectedYears = ref([])
const pickerValue = ref(null)
const indicatorConfig = ref({ indicators: [...ALL_INDICATORS] })
const showImpactDialog = ref(false)

watch(() => props.boundary, (b) => {
  if (b) {
    inputName.value = b.name || ''
    selectedYears.value = []
    pickerValue.value = null
    indicatorConfig.value = { indicators: b.indicators?.length ? [...b.indicators] : [...ALL_INDICATORS] }
  }
}, { immediate: true })

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

  // 有未选指标 → 弹影响确认
  const unselected = ALL_INDICATORS.filter(k => !indicators.includes(k))
  if (unselected.length > 0) {
    showImpactDialog.value = true
    return
  }

  // 全选 → 直接提交
  doSubmit()
}

function onImpactConfirm() {
  doSubmit()
}

async function doSubmit() {
  submitting.value = true
  try {
    const data = await recomputeBoundary(props.boundary.id, {
      years: selectedYears.value,
      computeMode: 'online',
      name: inputName.value.trim() || null,
      indicators: indicatorConfig.value.indicators || [],
    })
    ElMessage.success('计算已启动')
    emit('done', { taskId: data.task_id })
  } catch (err) {
    const detail = err.response?.data?.detail
    ElMessage.error(detail || '启动失败，请重试')
  }
  submitting.value = false
}
</script>

<style scoped>
.form-item {
  margin-bottom: 16px;
}
.form-label {
  display: block;
  color: #ccc;
  font-size: 13px;
  margin-bottom: 6px;
}
.year-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.year-count {
  color: #888;
  font-size: 12px;
}
.year-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 6px;
}
.no-years {
  color: #666;
  font-size: 12px;
}
.quick-picks {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}
.quick-label {
  color: #666;
}
</style>
