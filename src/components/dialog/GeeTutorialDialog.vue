<template>
  <el-dialog
    v-model="visible"
    title="GEE 密钥获取教程"
    width="620px"
    :close-on-click-modal="true"
    class="gee-tutorial-dialog"
    :append-to-body="true"
  >
    <div class="tutorial-content">
      <!-- Header -->
      <div class="tut-header">
        <span class="tut-emoji">🔑</span>
        <div>
          <h3 class="tut-title">GEE 密钥获取教程</h3>
          <p class="tut-subtitle">5 步完成，约 15 分钟</p>
        </div>
      </div>

      <!-- Timeline -->
      <div class="tut-timeline">

        <!-- Step 1 -->
        <div class="tut-step">
          <div class="tut-marker">
            <span class="tut-num">1</span>
            <div class="tut-line" />
          </div>
          <div class="tut-card">
            <h4>创建 Google Cloud 项目</h4>
            <div class="tut-detail">
              <p>打开 <a href="https://console.cloud.google.com" target="_blank" rel="noopener noreferrer">Google Cloud Console</a>，登录 Google 账号</p>
              <p>左上角 <strong>选择项目 → 新建项目</strong>，名称随意（如 <code>my-gee-project</code>）</p>
              <p class="tut-tip">💡 记下 <strong>项目 ID</strong>（如 <code>my-gee-project-123456</code>），后面会用到</p>
            </div>
          </div>
        </div>

        <!-- Step 2 -->
        <div class="tut-step">
          <div class="tut-marker">
            <span class="tut-num">2</span>
            <div class="tut-line" />
          </div>
          <div class="tut-card">
            <h4>启用 Earth Engine API</h4>
            <div class="tut-detail">
              <p>在控制台顶部搜索栏搜索 <code>Earth Engine</code></p>
              <p>进入 <strong>Google Earth Engine API</strong> 页面 → 点击 <strong>启用</strong></p>
              <a href="https://console.cloud.google.com/apis/library/earthengine.googleapis.com" target="_blank" rel="noopener noreferrer">
                <el-button size="small" type="primary" plain class="tut-btn">直接打开 API 页面</el-button>
              </a>
            </div>
          </div>
        </div>

        <!-- Step 3 -->
        <div class="tut-step">
          <div class="tut-marker">
            <span class="tut-num">3</span>
            <div class="tut-line" />
          </div>
          <div class="tut-card">
            <h4>创建服务账号 + 生成 JSON 密钥 <span class="tut-badge">核心步骤</span></h4>
            <div class="tut-detail">
              <p>左侧菜单 → <strong>IAM 和管理</strong> → <strong>服务账号</strong></p>
              <p>点击 <strong>创建服务账号</strong>，名称随意（如 <code>gee-service</code>），点 <strong>完成</strong></p>
              <p>创建完成后，点击该账号 → <strong>密钥</strong> 标签 → <strong>添加密钥 → 创建新密钥</strong></p>
              <p>选择 <strong>JSON</strong> → 点击 <strong>创建</strong></p>
              <p class="tut-tip">🔑 浏览器会自动下载一个 <code>.json</code> 文件 — <strong>这就是你的密钥</strong>，妥善保存</p>
            </div>
          </div>
        </div>

        <!-- Step 4 -->
        <div class="tut-step">
          <div class="tut-marker">
            <span class="tut-num">4</span>
            <div class="tut-line" />
          </div>
          <div class="tut-card">
            <h4>注册 GEE + 绑定服务账号</h4>
            <div class="tut-detail">
              <p>前往 <a href="https://code.earthengine.google.com/register" target="_blank" rel="noopener noreferrer">code.earthengine.google.com/register</a></p>
              <p>用同一个 Google 账号注册，学术用途选 <strong>Non-commercial</strong></p>
              <p>注册后进入 <a href="https://code.earthengine.google.com" target="_blank" rel="noopener noreferrer">GEE Code Editor</a>，点左上角 <strong>Settings → Cloud 项目</strong></p>
              <p>选择你创建的 GCP 项目，GEE 会自动关联服务账号</p>
              <a href="https://code.earthengine.google.com/register" target="_blank" rel="noopener noreferrer">
                <el-button size="small" type="primary" plain class="tut-btn">前往注册 GEE</el-button>
              </a>
            </div>
          </div>
        </div>

        <!-- Step 5 -->
        <div class="tut-step">
          <div class="tut-marker">
            <span class="tut-num">5</span>
          </div>
          <div class="tut-card">
            <h4>上传密钥到本系统</h4>
            <div class="tut-detail">
              <p>回到本页面上方的 <strong>第 3 步</strong>，将下载的 JSON 密钥文件拖拽上传</p>
              <p>系统会自动验证密钥是否有效</p>
              <p class="tut-tip">✅ 验证成功后即可使用自动模式</p>
            </div>
          </div>
        </div>
      </div>

      <!-- FAQ -->
      <div class="tut-faq">
        <h4 class="faq-title">常见问题</h4>
        <div class="faq-item">
          <div class="faq-q">❓ 注册 GEE 需要付费吗？</div>
          <div class="faq-a">学术研究可免费使用 Non-commercial 版本，配额充足。</div>
        </div>
        <div class="faq-item">
          <div class="faq-q">❓ 提示 "Please register" 怎么办？</div>
          <div class="faq-a">说明还没完成 Step 4 的 GEE 注册，请先去注册。</div>
        </div>
        <div class="faq-item">
          <div class="faq-q">❓ 验证失败 "Permission denied"？</div>
          <div class="faq-a">服务账号没有绑定到 GEE Cloud 项目，检查 Step 4。</div>
        </div>
        <div class="faq-item">
          <div class="faq-q">❓ 密钥文件泄露了怎么办？</div>
          <div class="faq-a">在 Google Cloud Console 的服务账号 → 密钥 页面删除旧密钥，重新生成新的。</div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
const props = defineProps({ modelValue: { type: Boolean, default: false } })
const emit = defineEmits(['update:modelValue'])

import { computed } from 'vue'
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})
</script>

<style scoped>
/* ─── Main layout ─── */
.tutorial-content { color: #ccc; }

.tut-header {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 24px; padding-bottom: 16px;
  border-bottom: 1px solid #2a2a2a;
}
.tut-emoji { font-size: 32px; }
.tut-title { color: #eee; font-size: 18px; margin: 0 0 2px; }
.tut-subtitle { color: #888; font-size: 13px; margin: 0; }

/* ─── Timeline ─── */
.tut-timeline { display: flex; flex-direction: column; gap: 0; }

.tut-step { display: flex; gap: 16px; }

.tut-marker {
  display: flex; flex-direction: column; align-items: center;
  flex-shrink: 0; width: 32px;
}
.tut-num {
  width: 32px; height: 32px; border-radius: 50%;
  background: linear-gradient(135deg, #4DABF7, #339AF0);
  color: #fff; font-size: 14px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.tut-line {
  width: 2px; flex: 1; min-height: 16px;
  background: linear-gradient(to bottom, #339AF0, #2a2a2a);
  margin: 4px 0;
}

.tut-card {
  flex: 1;
  background: #1e1e1e;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 12px;
  transition: border-color 0.2s;
}
.tut-card:hover { border-color: #444; }
.tut-card.highlight {
  border-color: rgba(77, 171, 247, 0.3);
  background: rgba(77, 171, 247, 0.04);
}

.tut-card h4 {
  color: #eee; font-size: 14px; margin: 0 0 8px;
  display: flex; align-items: center; gap: 8px;
}
.tut-badge {
  font-size: 10px; font-weight: 500;
  background: rgba(77, 171, 247, 0.15);
  color: #4DABF7;
  padding: 2px 8px; border-radius: 4px;
}

.tut-detail p {
  color: #aaa; font-size: 12px; margin: 0 0 6px; line-height: 1.6;
}
.tut-detail a {
  color: #4DABF7; text-decoration: none;
}
.tut-detail a:hover { text-decoration: underline; }
.tut-detail code {
  background: #2a2a2a; padding: 1px 6px; border-radius: 3px;
  font-size: 11px; color: #FFD43B; font-family: 'Consolas', 'Monaco', monospace;
}
.tut-detail strong { color: #ddd; }

.tut-tip {
  background: rgba(255, 212, 59, 0.06);
  border-left: 3px solid #FFD43B;
  padding: 6px 10px !important; border-radius: 0 4px 4px 0;
  margin-top: 8px !important;
}

.tut-btn { margin-top: 6px; }

/* ─── FAQ ─── */
.tut-faq {
  margin-top: 20px; padding-top: 16px;
  border-top: 1px solid #2a2a2a;
}
.faq-title {
  color: #ccc; font-size: 14px; margin: 0 0 12px;
}
.faq-item {
  padding: 8px 12px; margin-bottom: 6px;
  background: #1e1e1e; border-radius: 6px;
  border: 1px solid #2a2a2a;
}
.faq-q { color: #ddd; font-size: 12px; font-weight: 500; margin-bottom: 4px; }
.faq-a { color: #888; font-size: 12px; padding-left: 16px; line-height: 1.5; }
</style>
