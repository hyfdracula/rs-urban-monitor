<template>
  <div class="app-layout">
    <header class="app-header">
      <div class="logo">
        <span class="logo-full">长三角城市扩张与生态响应可视化平台</span>
        <span class="logo-short">长三角可视化平台</span>
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
        <el-button text @click="exportMap">
          <el-icon><Download /></el-icon>
          <span>导出</span>
        </el-button>
        <el-button type="primary" size="small" @click="publishMapService">
          <el-icon><Upload /></el-icon>
          <span>发布地图服务</span>
        </el-button>
      </div>

      <!-- Mobile hamburger -->
      <button class="hamburger" @click="drawerOpen = true">
        <span /><span /><span />
      </button>
    </header>

    <!-- Mobile drawer -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="drawerOpen" class="drawer-overlay" @click="drawerOpen = false" />
      </Transition>
      <Transition name="slide-drawer">
        <nav v-if="drawerOpen" class="mobile-drawer">
          <div class="drawer-header">
            <span class="drawer-title">导航</span>
            <button class="drawer-close" @click="drawerOpen = false">✕</button>
          </div>
          <div class="drawer-nav">
            <router-link
              v-for="item in navItems"
              :key="item.path"
              :to="item.path"
              class="drawer-item"
              :class="{ active: route.path === item.path }"
              @click="drawerOpen = false"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </router-link>
          </div>
          <div class="drawer-actions">
            <el-button @click="goUpload(); drawerOpen = false">
              <el-icon><Upload /></el-icon>
              <span>上传数据</span>
            </el-button>
            <el-button @click="exportMap(); drawerOpen = false">
              <el-icon><Download /></el-icon>
              <span>导出报告</span>
            </el-button>
            <el-button type="primary" @click="publishMapService(); drawerOpen = false">
              <el-icon><Upload /></el-icon>
              <span>发布地图服务</span>
            </el-button>
          </div>
        </nav>
      </Transition>
    </Teleport>

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
const drawerOpen = ref(false)

const navItems = [
  { path: '/', title: '总览', icon: 'Location' },
  { path: '/compare', title: '双期对比', icon: 'Switch' },
  { path: '/report', title: '分析报告', icon: 'Document' },
  { path: '/upload', title: '上传', icon: 'Upload' },
]

function exportMap() {
  showExportDialog.value = true
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

/* Logo: show full by default, short on mobile */
.logo-short { display: none; }

/* Hamburger: hidden on desktop */
.hamburger {
  display: none;
  flex-direction: column;
  gap: 5px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  margin-left: auto;
}
.hamburger span {
  display: block;
  width: 22px;
  height: 2px;
  background: #ccc;
  border-radius: 1px;
  transition: transform 0.2s;
}

/* Mobile drawer overlay */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 100;
}

/* Mobile drawer */
.mobile-drawer {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: min(280px, 80vw);
  background: #1a1a1a;
  border-right: 1px solid #333;
  z-index: 101;
  display: flex;
  flex-direction: column;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #333;
}

.drawer-title {
  font-size: 16px;
  font-weight: 600;
  color: #ddd;
}

.drawer-close {
  background: none;
  border: none;
  color: #888;
  font-size: 18px;
  cursor: pointer;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}

.drawer-close:hover {
  background: #333;
  color: #fff;
}

.drawer-nav {
  flex: 1;
  padding: 8px 0;
}

.drawer-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  color: #aaa;
  text-decoration: none;
  font-size: 15px;
  transition: all 0.2s;
}

.drawer-item:hover {
  background: #252525;
  color: #fff;
}

.drawer-item.active {
  color: #fff;
  background: #252525;
  border-left: 3px solid #FFD43B;
}

.drawer-actions {
  padding: 16px 20px;
  border-top: 1px solid #333;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.drawer-actions .el-button {
  width: 100%;
  justify-content: flex-start;
}

/* Drawer transitions */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-drawer-enter-active { transition: transform 0.25s ease-out; }
.slide-drawer-leave-active { transition: transform 0.2s ease-in; }
.slide-drawer-enter-from, .slide-drawer-leave-to { transform: translateX(-100%); }

/* Mobile breakpoint */
@media (max-width: 767px) {
  .app-header {
    padding: 0 12px;
    height: 48px;
  }

  .logo-full { display: none; }
  .logo-short { display: inline; }
  .logo { font-size: 15px; }

  .nav-menu { display: none; }
  .header-actions { display: none; }
  .hamburger { display: flex; }
}
</style>
