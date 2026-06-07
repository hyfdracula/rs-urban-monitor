<template>
  <div class="app-layout">
    <header class="app-header">
      <div class="logo">
        <span>长三角城市扩张与生态响应可视化平台</span>
      </div>
      <nav class="nav-menu">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path }"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </router-link>
      </nav>
      <div class="header-actions">
        <el-button text @click="goUpload">
          <el-icon><Upload /></el-icon>
          <span>上传</span>
        </el-button>
        <el-button text @click="exportMap">
          <el-icon><Download /></el-icon>
          <span>导出</span>
        </el-button>
        <el-button type="primary" size="small" @click="publishMapService">
          <el-icon><Upload /></el-icon>
          <span>发布地图服务</span>
        </el-button>
      </div>
    </header>
    <main class="app-main">
      <router-view />
    </main>

    <!-- Dialogs -->
    <ExportReportDialog v-model="showExportDialog" />
    <PublishMapDialog v-model="showPublishDialog" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Location,
  DataAnalysis,
  TrendCharts,
  Document,
  Switch,
  Download,
  Upload,
} from '@element-plus/icons-vue'
import ExportReportDialog from './components/dialog/ExportReportDialog.vue'
import PublishMapDialog from './components/dialog/PublishMapDialog.vue'

const route = useRoute()
const router = useRouter()

const showExportDialog = ref(false)
const showPublishDialog = ref(false)

const navItems = [
  { path: '/', title: '总览', icon: 'Location' },
  { path: '/compare', title: '双期对比', icon: 'Switch' },
  { path: '/expansion', title: '扩张分析', icon: 'TrendCharts' },
  { path: '/ecology', title: '生态评估', icon: 'DataAnalysis' },
  { path: '/report', title: '分析报告', icon: 'Document' },
]

function exportMap() {
  showExportDialog.value = true
}

function goUpload() {
  router.push('/upload')
}

function publishMapService() {
  showPublishDialog.value = true
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

body {
  background: #0a0a0a;
  color: #e0e0e0;
}
</style>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.app-header {
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 24px;
  background: #1a1a1a;
  border-bottom: 1px solid #333;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.logo .el-icon {
  font-size: 24px;
  color: #fff;
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 48px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  color: #888;
  text-decoration: none;
  font-size: 14px;
  border-radius: 6px;
  position: relative;
  transition: color 0.3s cubic-bezier(0.4, 0, 0.2, 1),
              background 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.nav-item::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 2px;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 1px;
  transform: translateX(-50%);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.nav-item:hover {
  color: #ccc;
  background: #252525;
}

.nav-item.active {
  color: #fff;
  background: transparent;
}

.nav-item.active::after {
  width: 80%;
}

.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-actions .el-button span {
  font-size: 13px;
}

.header-actions .el-button--primary {
  background: #FF6B6B;
  border-color: #FF6B6B;
  border-radius: 6px;
}

.header-actions .el-button--primary:hover {
  background: #ff5252;
  border-color: #ff5252;
}

.app-main {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>
