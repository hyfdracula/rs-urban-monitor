<template>
  <div class="step-preview">
    <div class="preview-header">
      <h4 class="step-title">生成 GEE 代码</h4>
      <div class="preview-actions">
        <el-button size="small" type="primary" @click="copyCode" :icon="CopyDocument">
          {{ copied ? '已复制 ✓' : '复制代码' }}
        </el-button>
        <el-button size="small" @click="openGEE">
          打开 GEE
        </el-button>
      </div>
    </div>

    <div v-if="!code" class="empty-state">
      <el-button type="primary" @click="$emit('generate')">
        生成代码
      </el-button>
    </div>

    <div v-else class="code-container">
      <div class="code-stats">
        <span>{{ lineCount }} 行</span>
        <span>{{ charCount }} 字符</span>
      </div>
      <pre class="code-block"><code>{{ code }}</code></pre>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { CopyDocument } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  code: { type: String, default: '' },
})

defineEmits(['generate'])

const copied = ref(false)

const lineCount = computed(() => props.code.split('\n').length)
const charCount = computed(() => props.code.length)

async function copyCode() {
  try {
    await navigator.clipboard.writeText(props.code)
    copied.value = true
    ElMessage.success('代码已复制到剪贴板')
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // Fallback
    const textarea = document.createElement('textarea')
    textarea.value = props.code
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    copied.value = true
    ElMessage.success('代码已复制')
    setTimeout(() => { copied.value = false }, 2000)
  }
}

function openGEE() {
  window.open('https://code.earthengine.google.com/', '_blank')
}
</script>

<style scoped>
.step-preview { padding: 8px 0; }
.step-title { color: #ddd; margin: 0; font-size: 15px; }

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.preview-actions { display: flex; gap: 8px; }

.empty-state {
  padding: 40px;
  text-align: center;
}

.code-container {
  background: #0d0d0d;
  border: 1px solid #333;
  border-radius: 8px;
  overflow: hidden;
}

.code-stats {
  display: flex;
  gap: 12px;
  padding: 8px 14px;
  background: #1a1a1a;
  border-bottom: 1px solid #333;
  color: #666;
  font-size: 12px;
  font-family: monospace;
}

.code-block {
  margin: 0;
  padding: 14px;
  max-height: 400px;
  overflow-y: auto;
  color: #bbb;
  font-size: 12px;
  line-height: 1.6;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  white-space: pre;
  tab-size: 2;
}

.code-block::-webkit-scrollbar { width: 6px; }
.code-block::-webkit-scrollbar-track { background: #0d0d0d; }
.code-block::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
</style>
