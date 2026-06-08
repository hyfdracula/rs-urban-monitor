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
        :class="{ active: selectedId === task.id }"
        @click="selectTask(task)"
      >
        <div class="task-top">
          <span class="task-name">{{ task.name || '未命名研究区' }}</span>
          <el-tag :type="statusType(task.status)" size="small" effect="dark">
            {{ statusLabel(task.status) }}
          </el-tag>
        </div>
        <div v-if="task.indicators?.length" class="task-tags">
          <span v-for="ind in task.indicators" :key="ind" class="tag-chip">{{ ind }}</span>
        </div>
        <div class="task-date">{{ formatDate(task.created_at) }}</div>
      </div>
    </div>

    <!-- Selected task detail -->
    <div v-if="selectedTask" class="task-detail">
      <div class="detail-head">
        <span class="detail-title">{{ selectedTask.name || '未命名研究区' }}</span>
        <el-button size="small" text @click="deselect">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
      <div class="detail-grid">
        <div class="detail-item">
          <span class="detail-label">状态</span>
          <span class="detail-value">{{ statusLabel(selectedTask.status) }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">创建时间</span>
          <span class="detail-value">{{ formatDate(selectedTask.created_at) }}</span>
        </div>
        <div v-if="selectedTask.indicators?.length" class="detail-item full">
          <span class="detail-label">分析指标</span>
          <span class="detail-value">{{ selectedTask.indicators.join('、') }}</span>
        </div>
        <div v-if="selectedTask.time_periods?.length" class="detail-item full">
          <span class="detail-label">时间节点</span>
          <span class="detail-value">{{ selectedTask.time_periods.join('、') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Loading, Refresh, Close } from '@element-plus/icons-vue'
import { getComputeTasks } from '../../api'

const emit = defineEmits(['select', 'deselect'])

const loading = ref(false)
const tasks = ref([])
const selectedId = ref('')
const selectedTask = ref(null)

const STATUS_MAP = {
  pending: { label: '排队中', type: 'info' },
  running: { label: '计算中', type: 'warning' },
  completed: { label: '已完成', type: 'success' },
  failed: { label: '失败', type: 'danger' },
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
    tasks.value = Array.isArray(data) ? data : data.tasks || []

    // Auto-select latest task if none selected
    if (tasks.value.length > 0 && !selectedId.value) {
      const latest = tasks.value[0]
      selectTask(latest)
    }
  } catch {
    tasks.value = []
  }
  loading.value = false
}

function selectTask(task) {
  selectedId.value = task.id
  selectedTask.value = task
  emit('select', task.id)
}

function deselect() {
  selectedId.value = ''
  selectedTask.value = null
  emit('deselect')
}

onMounted(() => {
  fetchTasks()
})
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

.task-tags {
  display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px;
}
.tag-chip {
  font-size: 11px; color: #999; background: #2a2a2a;
  padding: 1px 6px; border-radius: 4px;
}

.task-date { color: #555; font-size: 11px; margin-top: 4px; }

.task-detail {
  border-top: 1px solid #333; padding: 12px; flex-shrink: 0;
}
.detail-head {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;
}
.detail-title { color: #ddd; font-size: 13px; font-weight: 600; }

.detail-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 6px;
}
.detail-item { display: flex; flex-direction: column; gap: 2px; }
.detail-item.full { grid-column: 1 / -1; }
.detail-label { color: #666; font-size: 11px; }
.detail-value { color: #bbb; font-size: 12px; }
</style>
