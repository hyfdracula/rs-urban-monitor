<template>
  <div class="mode-selection">
    <h2 class="mode-title">选择数据接入方式</h2>
    <p class="mode-desc">根据你的需求选择合适的模式</p>

    <div class="mode-cards">
      <!-- Manual Mode -->
      <div class="mode-card" @click="$emit('select', 'manual')">
        <div class="card-icon manual-icon">
          <el-icon :size="32"><EditPen /></el-icon>
        </div>
        <h3>手动模式</h3>
        <p>填写参数 → 生成 GEE 代码 → 复制到 Earth Engine 运行</p>
        <el-tag size="small" type="success">推荐</el-tag>
      </div>

      <!-- Auto Mode -->
      <el-tooltip v-if="!geeReady" content="请先在顶部 GEE 按钮配置密钥" placement="top">
        <div class="mode-card disabled" @click="showAutoTip">
          <div class="card-icon auto-icon">
            <el-icon :size="32"><VideoPlay /></el-icon>
          </div>
          <h3>自动模式</h3>
          <p>一键自动化处理，从数据获取到地图展示全流程</p>
          <el-tag size="small" type="info">需配置密钥</el-tag>
        </div>
      </el-tooltip>
      <div v-else class="mode-card" @click="$emit('select', 'auto')">
        <div class="card-icon auto-icon">
          <el-icon :size="32"><VideoPlay /></el-icon>
        </div>
        <h3>自动模式</h3>
        <p>一键自动化处理，从数据获取到地图展示全流程</p>
        <el-tag size="small" type="success">已就绪</el-tag>
      </div>

      <!-- GeoServer Upload -->
      <div class="mode-card" @click="$emit('select', 'geoserver')">
        <div class="card-icon upload-icon">
          <el-icon :size="32"><UploadFilled /></el-icon>
        </div>
        <h3>文件上传</h3>
        <p>上传 GeoTIFF / Shapefile 至 GeoServer 发布 WMS</p>
        <el-tag size="small" type="warning">已有数据</el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { EditPen, VideoPlay, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getGeeKeyStatus } from '../../api'

defineEmits(['select'])

const geeReady = ref(false)

onMounted(async () => {
  try {
    const data = await getGeeKeyStatus()
    geeReady.value = data.has_key && data.status === 'valid'
  } catch {
    geeReady.value = false
  }
})

function showAutoTip() {
  ElMessage.warning('请先点击顶部「GEE」按钮配置密钥')
}
</script>

<style scoped>
.mode-selection {
  text-align: center;
  padding: 20px 0;
}

.mode-title {
  color: #ddd;
  margin: 0 0 8px;
  font-size: 20px;
}

.mode-desc {
  color: #888;
  font-size: 13px;
  margin: 0 0 28px;
}

.mode-cards {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.mode-card {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 28px 24px;
  width: 200px;
  cursor: pointer;
  transition: all 0.25s;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.mode-card:hover {
  border-color: #555;
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.mode-card h3 {
  color: #ddd;
  margin: 0;
  font-size: 16px;
}

.mode-card p {
  color: #888;
  font-size: 12px;
  margin: 0;
  line-height: 1.5;
}

.mode-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.mode-card.disabled:hover {
  border-color: #333;
  transform: none;
  box-shadow: none;
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.manual-icon {
  background: rgba(77, 171, 247, 0.15);
  color: #4DABF7;
}

.auto-icon {
  background: rgba(190, 75, 219, 0.15);
  color: #BE4BDB;
}

.upload-icon {
  background: rgba(255, 107, 107, 0.15);
  color: #FF6B6B;
}

@media (max-width: 700px) {
  .mode-cards {
    flex-direction: column;
    align-items: stretch;
  }

  .mode-card {
    width: 100%;
  }
}
</style>
