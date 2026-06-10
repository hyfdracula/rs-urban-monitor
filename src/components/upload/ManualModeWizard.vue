<template>
  <div class="manual-wizard">
    <!-- Back button -->
    <div class="wizard-header">
      <el-button text size="small" @click="$emit('back')">
        <el-icon><ArrowLeft /></el-icon>
        返回模式选择
      </el-button>
      <h3 class="wizard-title">手动模式 — GEE 代码生成</h3>
    </div>

    <!-- Steps indicator -->
    <el-steps :active="currentStep - 1" align-center class="wizard-steps" :class="{ mobile: isMobile }">
      <el-step title="边界" />
      <el-step title="时间" />
      <el-step title="指标" />
      <el-step title="数据源" />
      <el-step title="导出" />
      <el-step title="代码" />
    </el-steps>

    <!-- Step content -->
    <div class="step-content">
      <StepBoundary v-if="currentStep === 1" v-model="formData" />
      <StepTimePeriod v-if="currentStep === 2" v-model="formData" />
      <StepIndicators v-if="currentStep === 3" v-model="formData" />
      <StepSatellite v-if="currentStep === 4" v-model="formData" />
      <StepExport v-if="currentStep === 5" v-model="formData" />
      <StepCodePreview v-if="currentStep === 6" :code="generatedCode" @generate="generateCode" />
    </div>

    <!-- Navigation -->
    <div class="wizard-footer">
      <el-button v-if="currentStep > 1" @click="currentStep--">上一步</el-button>
      <el-button
        v-if="currentStep < 6"
        type="primary"
        :disabled="!canProceed"
        @click="currentStep++"
      >
        下一步
      </el-button>
      <el-button
        v-if="currentStep === 6 && !generatedCode"
        type="primary"
        @click="generateCode"
      >
        生成代码
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { generateGEECode } from '../../utils/geeTemplates'
import { uploadBoundary, getComputeCode } from '../../api'
import StepBoundary from './StepBoundary.vue'
import StepTimePeriod from './StepTimePeriod.vue'
import StepIndicators from './StepIndicators.vue'
import StepSatellite from './StepSatellite.vue'
import StepExport from './StepExport.vue'
import StepCodePreview from './StepCodePreview.vue'

defineEmits(['back'])

const currentStep = ref(1)
const generatedCode = ref('')
const isMobile = ref(false)
const generating = ref(false)

const formData = reactive({
  boundaryGeoJSON: null,
  boundaryName: '',
  timePeriods: [2000, 2005, 2010, 2015, 2020],
  indicators: ['rsei', 'construction'],
  satellite: 'landsat-auto',
  exportFormat: 'drive',
  exportPrefix: 'rs_urban',
})

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 1: return !!formData.boundaryGeoJSON
    case 2: return formData.timePeriods.length > 0
    case 3: return formData.indicators.length > 0
    case 4: return !!formData.satellite
    case 5: return !!formData.exportPrefix
    default: return true
  }
})

async function generateCode() {
  if (!formData.boundaryGeoJSON) {
    ElMessage.warning('请先设置研究区边界')
    currentStep.value = 1
    return
  }
  if (formData.timePeriods.length === 0) {
    ElMessage.warning('请至少选择一个时间节点')
    currentStep.value = 2
    return
  }
  if (formData.indicators.length === 0) {
    ElMessage.warning('请至少选择一个分析指标')
    currentStep.value = 3
    return
  }

  generating.value = true

  // Try backend first, fallback to local template
  try {
    // Upload boundary to backend
    const geojsonBlob = new Blob(
      [JSON.stringify(formData.boundaryGeoJSON)],
      { type: 'application/json' }
    )
    const file = new File([geojsonBlob], `${formData.boundaryName || 'boundary'}.geojson`, { type: 'application/json' })

    const uploadResult = await uploadBoundary(
      file,
      formData.boundaryName || '未命名',
      formData.timePeriods,
      'manual',
      null,
      {
        indicators: formData.indicators,
        satellite: formData.satellite,
        exportFormat: formData.exportFormat,
        exportPrefix: formData.exportPrefix,
      },
    )

    // Get generated code from backend
    const codeResult = await getComputeCode(uploadResult.task_id)
    generatedCode.value = codeResult.code
    ElMessage.success('后端代码生成成功！')
  } catch {
    // Backend unavailable, use local template
    generatedCode.value = generateGEECode(formData)
    ElMessage.success('本地模板代码已生成')
  }

  generating.value = false
}

function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})
</script>

<style scoped>
.manual-wizard {
  max-width: 640px;
  margin: 0 auto;
}

.wizard-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.wizard-title {
  color: #ddd;
  margin: 0;
  font-size: 15px;
}

.wizard-steps {
  margin-bottom: 20px;
}

.step-content {
  min-height: 200px;
  padding: 8px 0;
}

.wizard-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #2a2a2a;
}
</style>
