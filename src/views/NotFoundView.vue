<template>
  <div class="not-found">
    <div class="content">
      <div class="code">404</div>
      <div class="text">页面未找到</div>
      <p class="desc">请求的页面不存在或已被移除</p>
      <button class="back-btn" @click="$router.push('/')">返回首页</button>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.not-found {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a1a1a;
}

.content {
  text-align: center;
}

.code {
  font-size: 96px;
  font-weight: 800;
  color: #333;
  line-height: 1;
  letter-spacing: -4px;
}

.text {
  font-size: 20px;
  font-weight: 600;
  color: #888;
  margin-top: 8px;
}

.desc {
  font-size: 13px;
  color: #555;
  margin-top: 8px;
}

.back-btn {
  margin-top: 24px;
  padding: 8px 24px;
  background: #333;
  color: #ccc;
  border: 1px solid #444;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #444;
  color: #fff;
  border-color: #666;
}
</style>
