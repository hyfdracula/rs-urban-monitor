<template>
  <div class="task-panel">
    <div class="panel-head">
      <h4>分析任务</h4>
      <el-button size="small" text @click="fetchTasks">
        <el-icon><Refresh /></el-icon>
      </el-button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="state-msg">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <!-- Empty -->
    <div v-else-if="tasks.length === 0" class="empty-state">
      <p>暂无分析任务</p>
      <p class="hint">通过顶部「上传」按钮提交研究区边界后，分析结果将显示在这里</p>
    </div>

    <!-- Task list -->
    <div v-else class="task-list">
      <div
        v-for="task in tasks"
        :key="task.id"
        class="task-card"
        :class="{ active: selectedId === (task.task_id || task.id) }"
        @click="selectTask(task)"
      >
        <div class="task-top">
          <span class="task-name">{{ task.name || '未命名研究区' }}</span>
          <div class="task-actions">
            <el-tag :type="statusType(task.status)" size="small" effect="dark">
              {{ statusLabel(task.status) }}
            </el-tag>
            <el-button
              v-if="task.status === 'processing' || task.status === 'pending' || task.status === 'running'"
              size="small"
              text
              type="warning"
              @click.stop="onCancelTask(task)"
            >
              取消
            </el-button>
            <el-button
              size="small"
              text
              type="info"
              class="task-action-btn"
              @click.stop="onRename(task)"
            >
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button
              size="small"
              text
              type="danger"
              class="task-action-btn"
              @click.stop="onDelete(task)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>

        <!-- 进度条（仅 processing 任务） -->
        <div
          v-if="taskProgress[task.task_id] && (task.status === 'processing' || task.status === 'running')"
          class="task-progress"
        >
          <div class="task-progress-bar">
            <div class="task-progress-fill" :style="{ width: taskProgress[task.task_id].percent + '%' }" />
          </div>
          <div class="task-progress-info">
            <span>{{ taskProgress[task.task_id].percent }}%</span>
            <span v-if="taskProgress[task.task_id].step" class="task-progress-step">
              {{ taskProgress[task.task_id].step }}
            </span>
          </div>
        </div>

        <!-- 年份标签 -->
        <div v-if="task.years?.length" class="task-tags">
          <span v-for="y in task.years" :key="y" class="tag-chip year-chip">{{ y }}</span>
        </div>
        <div v-if="task.indicators?.length" class="task-tags">
          <span v-for="ind in task.indicators" :key="ind" class="tag-chip">{{ ind }}</span>
        </div>
        <div class="task-date">{{ formatDate(task.created_at) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Loading, Refresh, Delete, Edit } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getComputeTasks, getComputeProgress, cancelCompute, deleteBoundary, renameBoundary } from '../../api'

const emit = defineEmits(['select', 'deselect'])

const loading = ref(false)
const tasks = ref([])
const selectedId = ref('')
const selectedTask = ref(null)
const taskProgress = ref({})   // taskId → { percent, step }
let refreshTimer = null

// 是否有正在计算的任务
const hasProcessing = computed(() =>
  tasks.value.some(t => t.status === 'processing' || t.status === 'pending' || t.status === 'running')
)

const STATUS_MAP = {
  pending: { label: '排队中', type: 'info' },
  processing: { label: '计算中', type: 'warning' },
  running: { label: '计算中', type: 'warning' },
  completed: { label: '已完成', type: 'success' },
  failed: { label: '失败', type: 'danger' },
  cancelled: { label: '已取消', type: 'info' },
}

function statusLabel(status) {
  return STATUS_MAP[status]?.label || status || '未知'
}

function statusType(status) {
  return STATUS_MAP[status]?.type || 'info'
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

async function fetchTasks() {
  loading.value = true
  try {
    const data = await getComputeTasks()
    const prevIds = new Set(tasks.value.map(t => t.task_id))
    tasks.value = Array.isArray(data) ? data : data.items || data.tasks || []

    // Auto-select: 优先 processing 任务，其次最新任务
    if (tasks.value.length > 0 && !selectedId.value) {
      const processing = tasks.value.find(t =>
        t.status === 'processing' || t.status === 'pending' || t.status === 'running'
      )
      selectTask(processing || tasks.value[0])
    }

    // 如果有 processing 任务，启动进度轮询
    if (hasProcessing.value) {
      startProgressPolling()
    } else {
      stopProgressPolling()
    }
  } catch {
    tasks.value = []
  }
  loading.value = false
}

// ─── 进度轮询 ───
let progressTimer = null

function startProgressPolling() {
  stopProgressPolling()
  async function poll() {
    for (const task of tasks.value) {
      if (task.status !== 'processing' && task.status !== 'pending' && task.status !== 'running') continue
      try {
        const data = await getComputeProgress(task.task_id)
        taskProgress.value[task.task_id] = {
          percent: data.progress || 0,
          step: data.current_step || '',
        }
        if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
          // 状态变了，刷新整个任务列表
          await fetchTasks()
          if (selectedId.value === task.task_id) {
            emit('select', task)
          }
          return
        }
      } catch { /* retry next cycle */ }
    }
  }
  poll()
  progressTimer = setInterval(poll, 5000)
}

function stopProgressPolling() {
  if (progressTimer) { clearInterval(progressTimer); progressTimer = null }
}

// ─── 自动刷新：有 processing 任务时每 15s 刷新列表 ───
function startAutoRefresh() {
  stopAutoRefresh()
  refreshTimer = setInterval(() => {
    if (hasProcessing.value) fetchTasks()
  }, 15000)
}
function stopAutoRefresh() {
  if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null }
}

function selectTask(task) {
  selectedId.value = task.task_id
  selectedTask.value = task
  emit('select', task)
}

function deselect() {
  selectedId.value = ''
  selectedTask.value = null
  emit('deselect')
}

async function onRename(task) {
  try {
    const { value } = await ElMessageBox.prompt('请输入新名称', '重命名', {
      inputValue: task.name || '',
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputValidator: (v) => (v && v.trim() ? true : '名称不能为空'),
    })
    const newName = value.trim()
    await renameBoundary(task.id, newName)
    ElMessage.success(`已更名为「${newName}」`)
    await fetchTasks()
    if (selectedId.value === task.task_id) {
      const updated = tasks.value.find(t => t.task_id === task.task_id)
      if (updated) emit('select', updated)
    }
  } catch {
    // 用户取消
  }
}

async function onDelete(task) {
  try {
    await ElMessageBox.confirm(
      `确定删除「${task.name || '未命名研究区'}」？`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await deleteBoundary(task.id)
    ElMessage.success(`已删除「${task.name || '未命名研究区'}」`)
    if (selectedId.value === (task.task_id || task.id)) {
      deselect()
    }
    tasks.value = tasks.value.filter(t => t.id !== task.id)
  } catch {
    ElMessage.error('删除失败')
  }
}

async function onCancelTask(task) {
  try {
    await cancelCompute(task.task_id)
    ElMessage.info('已发送取消请求')
    await fetchTasks()
  } catch {
    ElMessage.error('取消失败')
  }
}

onMounted(() => {
  fetchTasks()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
  stopProgressPolling()
})

defineExpose({ fetchTasks })
</script>

<style scoped>
.task-panel { height: 100%; display: flex; flex-direction: column; }

.panel-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 12px 8px; flex-shrink: 0;
}
.panel-head h4 { color: #ccc; margin: 0; font-size: 14px; }

.state-msg {
  display: flex; align-items: center; gap: 8px;
  color: #888; font-size: 13px; justify-content: center; padding: 40px;
}

.empty-state {
  display: flex; flex-direction: column; align-items: center;
  gap: 8px; padding: 40px 20px; text-align: center;
}
.empty-state p { color: #888; font-size: 13px; margin: 0; }
.empty-state .hint { color: #555; font-size: 12px; line-height: 1.5; }

.task-list {
  flex: 1; overflow-y: auto; padding: 0 12px;
}
.task-card {
  padding: 10px; border: 1px solid #333; border-radius: 8px;
  margin-bottom: 8px; cursor: pointer; transition: border-color 0.2s;
}
.task-card:hover { border-color: #555; }
.task-card.active { border-color: #FF9F43; background: #1f1a14; }

.task-top { display: flex; justify-content: space-between; align-items: center; }
.task-name { color: #ddd; font-size: 13px; font-weight: 500; }

.task-actions { display: flex; align-items: center; gap: 4px; }
.task-action-btn { opacity: 0; transition: opacity 0.2s; padding: 2px 4px; }
.task-card:hover .task-action-btn { opacity: 1; }

.task-tags {
  display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px;
}
.tag-chip {
  font-size: 11px; color: #999; background: #2a2a2a;
  padding: 1px 6px; border-radius: 4px;
}
.year-chip {
  color: #FF9F43; background: #2a2015;
}

.task-date { color: #555; font-size: 11px; margin-top: 4px; }

/* ── 任务卡片内进度条 ── */
.task-progress { margin-top: 6px; }
.task-progress-bar {
  height: 4px; background: #333; border-radius: 2px; overflow: hidden;
}
.task-progress-fill {
  height: 100%; background: #BE4BDB; border-radius: 2px;
  transition: width 0.5s;
}
.task-progress-info {
  display: flex; justify-content: space-between;
  color: #888; font-size: 11px; margin-top: 3px;
}
.task-progress-step { color: #666; }
</style>
