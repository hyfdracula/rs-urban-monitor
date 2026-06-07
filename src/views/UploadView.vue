<template>
  <div class="upload-page">
    <div class="upload-card">
      <h2>数据上传</h2>
      <p class="desc">上传 GeoTIFF 或 Shapefile 至 GeoServer 发布为 WMS 服务</p>

      <el-upload
        class="upload-area"
        drag
        multiple
        :auto-upload="false"
        :on-change="onFileChange"
        :file-list="files"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">拖拽文件到此处 或 点击选择</div>
        <div class="upload-hint">支持 .tif .tiff .shp .zip (含 .shp)</div>
      </el-upload>

      <div class="file-list" v-if="files.length">
        <div v-for="f in files" :key="f.uid" class="file-item">
          <span>{{ f.name }}</span>
          <span class="file-size">{{ formatSize(f.size) }}</span>
        </div>
      </div>

      <el-button type="primary" :loading="uploading" @click="doUpload" class="upload-btn">
        上传并发布
      </el-button>

      <div v-if="uploading" class="progress-bar">
        <div class="progress-fill" :style="{ width: progress + '%' }" />
        <span class="progress-text">{{ progress }}%</span>
      </div>
    </div>

    <div class="task-list" v-if="tasks.length">
      <h3>任务列表</h3>
      <div v-for="t in tasks" :key="t.id" class="task-item">
        <span :class="statusClass(t.status)">{{ statusIcon(t.status) }}</span>
        <span class="task-name">{{ t.name }}</span>
        <span class="task-status">{{ t.status }}</span>
        <span class="task-time">{{ t.time }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'

const files = ref([])
const uploading = ref(false)
const progress = ref(0)
const tasks = ref([
  { id: 1, name: 'construction_2020.tif', status: 'done', time: '2分钟前' },
  { id: 2, name: 'rsei_2015.tif', status: 'done', time: '5分钟前' },
])

function onFileChange(file) { files.value.push(file) }
function formatSize(bytes) { return bytes ? (bytes / 1024 / 1024).toFixed(1) + ' MB' : '' }

function doUpload() {
  uploading.value = true; progress.value = 0
  const timer = setInterval(() => {
    progress.value += Math.random() * 20
    if (progress.value >= 100) { progress.value = 100; uploading.value = false; clearInterval(timer) }
  }, 500)
}

function statusClass(s) { return { done: 'green', processing: 'orange', failed: 'red' }[s] || '' }
function statusIcon(s) { return { done: '✓', processing: '◎', failed: '✕' }[s] || '' }
</script>

<style scoped>
.upload-page { height: 100%; overflow-y: auto; padding: 40px; background: #0d0d0d; display: flex; flex-direction: column; align-items: center; gap: 24px; }
.upload-card { background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 32px; max-width: 520px; width: 100%; }
.upload-card h2 { color: #ddd; margin: 0 0 8px; }
.desc { color: #888; font-size: 13px; margin: 0 0 20px; }
.upload-icon { font-size: 40px; color: #555; }
.upload-text { color: #aaa; margin-top: 8px; }
.upload-hint { color: #555; font-size: 12px; margin-top: 4px; }
.file-list { margin-top: 12px; }
.file-item { display: flex; justify-content: space-between; padding: 6px 0; color: #bbb; font-size: 13px; border-bottom: 1px solid #2a2a2a; }
.file-size { color: #666; }
.upload-btn { margin-top: 16px; width: 100%; }
.progress-bar { margin-top: 12px; height: 6px; background: #333; border-radius: 3px; position: relative; }
.progress-fill { height: 100%; background: #4DABF7; border-radius: 3px; transition: width 0.3s; }
.progress-text { position: absolute; right: 0; top: -18px; font-size: 11px; color: #888; }
.task-list { background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 20px; max-width: 520px; width: 100%; }
.task-list h3 { color: #ccc; margin: 0 0 12px; }
.task-item { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #2a2a2a; font-size: 13px; color: #bbb; }
.task-status { margin-left: auto; font-size: 12px; }
.task-time { font-size: 11px; color: #666; }
.green { color: #69DB7C; }
.orange { color: #FF922B; }
.red { color: #FF6B6B; }
</style>
